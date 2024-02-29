from typing import Dict
import json
import requests
from web3 import Web3

from bal_addresses.subgraph import Subgraph


class BalPoolsGauges:
    def __init__(self, chain):
        self.chain = chain
        self.subgraph = Subgraph(self.chain)
        self.core_pools = self.build_core_pools()

    def is_pool_exempt_from_yield_fee(self, pool_id: str) -> bool:
        data = self.subgraph.fetch_graphql_data(
            "core", "yield_fee_exempt", {"poolId": pool_id}
        )
        for pool in data["poolTokens"]:
            address = pool["poolId"]["address"]
            if pool["id"].split("-")[-1] == address:
                continue
            if pool["isExemptFromYieldProtocolFee"] == True:
                return True

    def get_bpt_balances(self, pool_id: str, block: int) -> Dict[str, int]:
        variables = {"poolId": pool_id, "block": int(block)}
        data = self.subgraph.fetch_graphql_data(
            "core", "get_user_pool_balances", variables
        )
        results = {}
        if "pool" in data and data["pool"]:
            for share in data["pool"]["shares"]:
                user_address = Web3.toChecksumAddress(share["userAddress"]["id"])
                results[user_address] = float(share["balance"])
        return results

    def get_gauge_deposit_shares(
        self, gauge_address: str, block: int
    ) -> Dict[str, int]:
        gauge_address = Web3.toChecksumAddress(gauge_address)
        variables = {"gaugeAddress": gauge_address, "block": int(block)}
        data = self.subgraph.fetch_graphql_data(
            self.subgraph.BALANCER_GAUGES_SHARES_QUERY, variables
        )
        results = {}
        if "data" in data and "gaugeShares" in data["data"]:
            for share in data["data"]["gaugeShares"]:
                user_address = Web3.toChecksumAddress(share["user"]["id"])
                results[user_address] = float(share["balance"])
        return results

    def is_core_pool(self, pool_id: str) -> bool:
        """
        check if a pool is a core pool using a fresh query to the subgraph

        params:
        pool_id: this is the long version of a pool id, so contract address + suffix

        returns:
        True if the pool is a core pool
        """
        return pool_id in self.core_pools

    def query_preferential_gauges(self, skip=0, step_size=100) -> list:
        """
        TODO: add docstring
        """
        variables = {"skip": skip, "step_size": step_size}
        data = self.subgraph.fetch_graphql_data("gauges", "pref_gauges", variables)
        try:
            result = data["liquidityGauges"]
        except KeyError:
            result = []
        if len(result) > 0:
            # didnt reach end of results yet, collect next page
            result += self.query_preferential_gauges(skip + step_size, step_size)
        return result

    def get_pools_with_rate_provider(self) -> dict:
        """
        for every chain, query the official balancer subgraph and retrieve pools that meets
        all three of the following conditions:
        - have a rate provider different from address(0)
        - have a liquidity greater than $250k
        - either:
          - have a yield fee > 0
          - be a meta stable pool with swap fee > 0
          - be a gyro pool

        returns:
        dictionary of the format {chain_name: {pool_id: symbol}}
        """
        filtered_pools = {}
        data = self.subgraph.fetch_graphql_data("core", "pools_rate_provider")
        try:
            for pool in data["pools"]:
                filtered_pools[pool["id"]] = pool["symbol"]
        except KeyError:
            # no results for this chain
            pass
        return filtered_pools

    def has_alive_preferential_gauge(self, pool_id: str) -> bool:
        """
        check if a pool has an alive preferential gauge using a fresh query to the subgraph

        params:
        - pool_id: id of the pool

        returns:
        - True if the pool has a preferential gauge which is not killed
        """
        variables = {"pool_id": pool_id}
        data = self.subgraph.fetch_graphql_data(
            "gauges", "alive_preferential_gauge", variables
        )
        try:
            result = data["pools"]
        except KeyError:
            result = []
        if len(result) == 0:
            print(f"Pool {pool_id} on {self.chain} has no preferential gauge")
            return False
        for gauge in result:
            if gauge["preferentialGauge"]["isKilled"] == False:
                return True
        print(f"Pool {pool_id} on {self.chain} has no alive preferential gauge")

    def build_core_pools(self):
        """
        build the core pools dictionary by taking pools from `get_pools_with_rate_provider` and:
        - check if the pool has an alive preferential gauge
        - add pools from whitelist
        - remove pools from blacklist

        returns:
        dictionary of the format {pool_id: symbol}
        """
        core_pools = self.get_pools_with_rate_provider()

        # make sure the pools have an alive preferential gauge
        for pool_id in core_pools.copy():
            if not self.has_alive_preferential_gauge(pool_id):
                del core_pools[pool_id]

        # add pools from whitelist
        with open("config/core_pools_whitelist.json", "r") as f:
            whitelist = json.load(f)
        try:
            for pool, symbol in whitelist[self.chain].items():
                if pool not in core_pools:
                    core_pools[pool] = symbol
        except KeyError:
            # no results for this chain
            pass

        # remove pools from blacklist
        with open("config/core_pools_blacklist.json", "r") as f:
            blacklist = json.load(f)
        try:
            for pool in blacklist[self.chain]:
                if pool in core_pools:
                    del core_pools[pool]
        except KeyError:
            # no results for this chain
            pass

        return core_pools
