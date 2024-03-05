from  .addresses import AddrBook
from .subgraph import Subgraph
from .pools_gauges import BalPoolsGauges
from .errors import ChecksumError, UnexpectedListLengthError, MultipleMatchesError, NoResultError
import requests
import re
import json
from collections import defaultdict
from typing import Dict
from web3 import Web3


class KeyAsDefaultDict(defaultdict):
    def __missing__(self, key):
        return key

class Aura:
    AURA_GAUGE_STAKER_BY_CHAIN ={
        "mainnet": "0xaF52695E1bB01A16D33D7194C28C42b10e0Dbec2"
    }
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
        Returns a map like {"gauge_address": int(pid_number)} with all aura gauges on the operating chain
        """
        data = self.subgraph.fetch_graphql_data("aura", "get_aura_gauge_mappings")
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
        variables = {"poolId": aura_pid, "block": int(block)}
        data = self.queries.fetch_graphql_data("aura", "get_aura_user_pool_balances", variables)
        results = {}
        # Parse the data if the query was successful
        if data and 'data' in data and 'leaderboard' in data['data'] and data['data']['leaderboard']['accounts']:
            for account in data['data']['leaderboard']['accounts']:
                ## Aura amounts are WEI denominated and others are float.  Transform
                amount = float(int(account['staked']) / 1e18)
                user_address = Web3.toChecksumAddress(account['account']['id'])
                results[user_address] = amount
        #TODO better handle pagination with the query and this function/pull multiple pages if required
        assert len(results) < 1000, "Pagination limit hit on Aura query"
        return results


    def get_aura_pid_from_gauge(self, deposit_gauge_address: str) -> str:
        deposit_gauge_address = Web3.toChecksumAddress(deposit_gauge_address)
        result = self.aura_pids_by_address.get(deposit_gauge_address, None)
        if not result:
            raise NoResultError(f"Gauge {deposit_gauge_address} has no Aura PID")
        if isinstance(result, str):
            return result
        else:
            if len(result) != 1:
                raise UnexpectedListLengthError(f"Got a list result with something other than 1 memeber when compling aura PID mapping: {result}")
            return result[0]