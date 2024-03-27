from collections import defaultdict
from typing import Dict
import json
from .errors import UnexpectedListLengthError, MultipleMatchesError, NoResultError
from .subgraph import Subgraph
from .utils import to_checksum_address

AURA_L2_DEFAULT_GAUGE_STAKER = to_checksum_address("0xC181Edc719480bd089b94647c2Dc504e2700a2B0")


class KeyAsDefaultDict(defaultdict):
    def __missing__(self, key):
        return key


class Aura:
    ## Aura seems to stake from the same address on all chains except mainnet
    AURA_GAUGE_STAKER_BY_CHAIN = defaultdict(lambda: AURA_L2_DEFAULT_GAUGE_STAKER)
    AURA_GAUGE_STAKER_BY_CHAIN["mainnet"] = to_checksum_address("0xaF52695E1bB01A16D33D7194C28C42b10e0Dbec2")

    def __init__(self, chain):
        self.chain = chain
        self.subgraph = Subgraph(chain)
        try:
            self.aura_pids_by_address = Aura.get_aura_gauge_mappings(self)
        except Exception as e:
            print(f"Failed to populate aura pids from aura subgraph: {e}")
            self.aura_pids_by_address = None

    def get_aura_gauge_mappings(self) -> Dict[str, int]:
        """
        Get a dict with gauge_address as key and aura PID as value for the running chain.
        """
        data = self.subgraph.fetch_graphql_data("aura", "get_aura_gauge_mappings")
        #print(json.dumps(data, indent=1))
        aura_pid_by_gauge = {}
        for result_item in data["gauges"]:
            gauge_address = to_checksum_address(result_item["pool"]["gauge"]["id"])
            pid = result_item["pool"]["id"]
            # Seems like pid can be a string or a list
            if isinstance(pid, list):
                if len(pid > 1):
                    raise MultipleMatchesError(f"Gauge: {gauge_address} is returning multiple aura PIDs: {pid}")
                else:
                    pid = [pid][0]

            if gauge_address in aura_pid_by_gauge:
                raise MultipleMatchesError(
                    f"Gauge with address{gauge_address} already found with PID {aura_pid_by_gauge[gauge_address]} when trying to insert new PID {pid}")
            aura_pid_by_gauge[gauge_address] = pid
        return aura_pid_by_gauge

    def get_aura_pool_shares(self, gauge_address, block) -> Dict[str, int]:
        """
        Get a dict with user address as key and wei balance staked in aura as value for the specified gauge and block

        params:
        - gauge: The gauge to query that has BPTs deposited in it
        - block: The block to query on

        returns:
        - result of the query
        """
        # Prepare the GraphQL query and variables
        gauge_address = to_checksum_address(gauge_address)
        aura_pid = self.aura_pids_by_address.get(gauge_address)
        variables = {"poolId": aura_pid, "block": int(block)}
        data = self.subgraph.fetch_graphql_data("aura", "get_aura_user_pool_balances", variables)
        results = {}
        # Parse the data if the query was successful
        if data and  'leaderboard' in data and data['leaderboard']['accounts']:
            for account in data['leaderboard']['accounts']:
                ## Aura amounts are WEI denominated and others are float.  Transform
                amount = float(int(account['staked']) / 1e18)
                user_address = to_checksum_address(account['account']['id'])
                results[user_address] = amount
        # TODO better handle pagination with the query and this function/pull multiple pages if required
        assert len(results) < 1000, "Pagination limit hit on Aura query"
        return results

    def get_aura_pid_from_gauge(self, deposit_gauge_address: str) -> int:
        """
        Get the Aura PID for a given Balancer Gauge

        params:
        - deposit_gauge_address: The gauge to query that has BPTs deposited in it

        returns:
        - The Aura PID of the specified gauge
        """
        deposit_gauge_address = to_checksum_address(deposit_gauge_address)
        result = self.aura_pids_by_address.get(deposit_gauge_address, None)
        if not result:
            raise NoResultError(f"Gauge {deposit_gauge_address} has no Aura PID")
        if isinstance(result, str):
            return result
        else:
            if len(result) != 1:
                raise UnexpectedListLengthError(
                    f"Got a list result with something other than 1 member when compiling aura PID mapping: {result}")
            return result[0]
