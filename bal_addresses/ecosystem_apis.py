from  .addresses import AddrBook
from .queries import GraphQueries
from .gauges import BalGauges
from .errors import ChecksumError, UnexpectedListLength, MultipleMatchesError
import requests
import re
import json
from collections import defaultdict
from typing import Dict
from web3 import Web3
from bal_addresses import utils as BalUtils


class KeyAsDefaultDict(defaultdict):
    def __missing__(self, key):
        return key

class Ecosystem:
    def __init__(self, chain):
        self.chain = chain
        self.queries = GraphQueries(chain)
        self.gauges = BalGauges(chain)
        self.aura = Aura(chain)
        self.beefy = Beefy(chain)

    def get_ecosystem_balances(self, pool_id: str, gauge_address: str, block: int) -> Dict[str, int]:
        gauge_address = Web3.toChecksumAddress(gauge_address)
        bpts_in_bal_gauge = 0
        bpts_in_aura = 0
        total_circulating_bpts = 0
        total_bpts_counted = 0
        ## Start with raw BPTS
        ecosystem_balances = defaultdict(int, self.gauges.get_bpt_balances(pool_id, block))
        for address, amount in ecosystem_balances.items():
            total_circulating_bpts += float(amount)
        ## Factor in Gauge Deposits
        if gauge_address in ecosystem_balances.keys():
            # Verify that there are some gauge deposits and null them out so balances add up
            bpts_in_bal_gauge = ecosystem_balances[gauge_address]
            ecosystem_balances[gauge_address] = 0
            ## TODO think about what to do about pool tokens in the vault, how that works with subgraph magic
        else:
            print(
                f"WARNING: there are no BPTs from {pool_id} staked in the gauge at {gauge_address} did you cross wires, or is there no one staked?")

        checksum = 0
        for address, amount in self.gauges.get_gauge_deposit_shares(gauge_address, block).items():
            ecosystem_balances[address] += float(amount)
            checksum += amount
        if checksum != bpts_in_aura:
            print(
                f"Warning: {bpts_in_bal_gauge} BPTs were found in the deposited in a bal gauge and zeroed out, but {checksum} of 'em where counted as gauge deposits.")

        ## Factor in Aura Deposits
        aura_staker = self.aura.AURA_GAUGE_STAKER_BY_CHAIN[self.chain]
        if aura_staker in ecosystem_balances.keys():
            bpts_in_aura = ecosystem_balances[aura_staker]
            ecosystem_balances[aura_staker] = 0
        else:
            print(
                f"WARNING: there are no BPTs from {pool_id} staked in Aura did you cross wires, or is there no one staked?")
        checksum = 0
        for address, amount in self.aura.get_aura_pool_shares(gauge_address, block).items():
            ecosystem_balances[address] += amount
            checksum += amount
        if checksum != bpts_in_aura:
            print(f"Warning: {bpts_in_aura} BPTs were found in the aura proxy and zeroed out, but {checksum} of 'em where counted as Aura deposits.")

        ## CHeck everything
        for address, amount in ecosystem_balances.items():
            total_bpts_counted += float(amount)
        print(
            f"Found {total_circulating_bpts} of which {bpts_in_bal_gauge} where staked by an address in a bal gauge and {bpts_in_aura} where deposited on aura at block {block}")
        ## Slight tolerance for rounding
        delta = abs(total_circulating_bpts - total_bpts_counted)
        if delta > 1e-10:
            raise ChecksumError(
                f"initial bpts found {total_circulating_bpts}, final bpts counted:{total_bpts_counted} the delta is {total_circulating_bpts - total_bpts_counted}" )
        return ecosystem_balances


class Beefy:
    API_URL = "https://api.beefy.finance/vaults/"
    CHAIN_MAP = ""
    ## Pre-populate API data
    __results = requests.get(API_URL)
    __results.raise_for_status()
    API_FULL_RESULT = __results.json()

    ## Build chain name translation map
    #### See https://raw.githubusercontent.com/beefyfinance/beefy-api/master/packages/address-book/util/chainIdMap.ts
    BEEFY_NAME_BY_BAL_NAME = KeyAsDefaultDict()
    BEEFY_NAME_BY_BAL_NAME["mainnet"] = "ethereum"
    BEEFY_NAME_BY_BAL_NAME["avalanche"] = "avax"

    def __init__(self, chain):
        self.chain = chain
        self.BEEFY_CHAIN_NAME = self.BEEFY_NAME_BY_BAL_NAME[self.chain]
        results = requests.get(self.API_URL + self.BEEFY_CHAIN_NAME)
        results.raise_for_status()
        self.API_CHAIN_RESULTS = results.json()


class Aura:
    AURA_GAUGE_STAKER_BY_CHAIN ={
        "mainnet": "0xaF52695E1bB01A16D33D7194C28C42b10e0Dbec2"
    }
    def __init__(self, chain):
        self.chain = chain
        self.queries = GraphQueries(chain)
        try:
            self.aura_pids_by_address = Aura.get_aura_gauge_mappings(self)
        except Exception as e:
            print(f"Failed to populate aura pids from aura subgraph: {e}")
            self.aura_pids_by_address = None
    def get_aura_gauge_mappings(self) -> Dict[str, int]:
        """
        Returns a map like {"gauge_address": int(pid_number)} with all aura gauges on the operating chain
        """
        query = self.queries.AURA_GAUGE_MAPPINGS_QUERY
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"])
        aura_pid_by_gauge = {}
        for result_item in data["data"]["gauges"]:
            gauge_address = Web3.toChecksumAddress(result_item["pool"]["gauge"]["id"])
            pid = result_item["pool"]["id"]
            # Seems like pid can be a string or a list
            if isinstance(pid, list):
                if len(pid > 1):
                    raise MultipleMatchesError(f"Gauge: {gauge_address} is returning multiple aura PIDs: {pid}")
                else:
                    pid=[pid][0]


            if gauge_address in aura_pid_by_gauge:
                raise MultipleMatchesError(f"Gauge with address{gauge_address} already found with PID {aura_pid_by_gauge[gauge_address]} when trying to insert new PID {pid}")
            aura_pid_by_gauge[gauge_address] = pid
        return aura_pid_by_gauge
    def get_aura_pool_shares(self, gauge_address, block) -> Dict[str, int]:
        # Prepare the GraphQL query and variables
        aura_pid = self.get_aura_pid_from_gauge(gauge_address)
        query = self.queries.AURA_SHARES_QUERY
        variables = {"poolId": aura_pid, "block": int(block)}
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"], variables)
        results = {}
        # Parse the data if the query was successful
        if data and 'data' in data and 'leaderboard' in data['data'] and data['data']['leaderboard']['accounts']:
            for account in data['data']['leaderboard']['accounts']:
                ## Aura amounts are WEI denominated and others are float.  Transform
                amount = float(int(account['staked']) / 1e18)
                user_address = Web3.toChecksumAddress(account['account']['id'])
                results[user_address] = amount
        return results


    def get_aura_pid_from_gauge(self, deposit_gauge_address: str) -> str:
        deposit_gauge_address = Web3.toChecksumAddress(deposit_gauge_address)
        try:
            result = self.aura_pids_by_address[deposit_gauge_address]
        except KeyError as e:
            print(f"WARNING: Gauge {deposit_gauge_address} does is not returning any deposits on Aura, is Aura Empty for this pool?")

        if isinstance(result, str):
            return result
        else:
            if len(result) != 1:
                raise UnexpectedListLength(f"Got a list result with something other than 1 memeber when compling aura PID mapping: {result}")
            return result[0]