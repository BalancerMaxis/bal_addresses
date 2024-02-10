from bal_addresses import utils as BalUtils
from .queries import GraphQueries
from typing import Dict
from .errors import ChecksumError, UnexpectedListLengthError
import json
from urllib.request import urlopen
import requests
from collections import defaultdict
from web3 import Web3


class BalPoolsGauges:
    def __init__(self, chain):
        self.chain = chain
        # TODO move build_core_pools into lib and figure out how to deal with the need for a global call.
        self.core_pools = self.build_core_pools()
        self.queries = GraphQueries(self.chain)


    def get_bpt_balances(self, pool_id: str, block: int) -> Dict[str, int]:
        variables = {"poolId": pool_id, "block": int(block)}
        data = self.queries.fetch_graphql_data(self.queries.BALANCER_POOL_SHARES_QUERY, variables)
        results = {}
        if data and 'data' in data and 'pool' in data['data'] and data['data']['pool']:
            for share in data['data']['pool']['shares']:
                user_address = Web3.toChecksumAddress(share['userAddress']['id'])
                results[user_address] = float(share['balance'])
        return results

    def get_gauge_deposit_shares(self, gauge_address: str, block: int) -> Dict[str, int]:
        gauge_address = Web3.toChecksumAddress(gauge_address)
        variables = {"gaugeAddress": gauge_address, "block": int(block)}
        data = self.queries.fetch_graphql_data(self.queries.BALANCER_GAUGES_SHARES_QUERY, variables)
        results = {}
        if 'data' in data and 'gaugeShares' in data['data']:
            for share in data['data']['gaugeShares']:
                user_address = Web3.toChecksumAddress(share['user']['id'])
                results[user_address] = float(share['balance'])
        return results

    def has_alive_preferential_gauge(self, pool_id: str) -> bool:
        """
        check if a pool has an alive preferential gauge

        params:
        chain: string format is the same as in extras/chains.json
        pool_id: this is the long version of a pool id, so contract address + suffix

        returns:
        True if the pool has an alive preferential gauge
        """
        return BalUtils.has_alive_preferential_gauge(self.chain, pool_id)

    # TODO remove and/or move description to var somehow?
    def get_core_pools(self) -> dict:
        """
        get the core pools for a chain

        params:
        chain: string format is the same as in extras/chains.json

        returns:
        dictionary of the format {pool_id: symbol}
        """
        return self.core_pools

    def is_core_pool(self, pool_id: str) -> bool:
        """
        check if a pool is a core pool using a fresh query to the subgraph

        params:
        chain: string format is the same as in extras/chains.json
        pool_id: this is the long version of a pool id, so contract address + suffix

        returns:
        True if the pool is a core pool
        """
        return pool_id in self.core_pools

    def query_preferential_gauges(self, skip=0, step_size=100) -> list:
        ## Todo
        url = BalUtils.get_subgraph_url(self.chain, "gauges")
        query = f"""{{
            liquidityGauges(
                skip: {skip}
                first: {step_size}
                where: {{isPreferentialGauge: true}}
            ) {{
                id
                symbol
            }}
        }}"""
        r = requests.post(url, json={"query": query})
        r.raise_for_status()
        try:
            result = r.json()["data"]["liquidityGauges"]
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

        params:
        - chain: name of the chain

        returns:
        dictionary of the format {chain_name: {pool_id: symbol}}
        """
        filtered_pools = {}
        url = BalUtils.get_subgraph_url(self.chain)
        query = """{
            pools(
                first: 1000,
                where: {
                    and: [
                        {
                            priceRateProviders_: {
                                address_not: "0x0000000000000000000000000000000000000000"
                            }
                        },
                        {
                            totalLiquidity_gt: 250000
                        },
                        { or: [
                            { protocolYieldFeeCache_gt: 0 },
                            { and: [
                                { swapFee_gt: 0 },
                                { poolType_contains: "MetaStable" },
                                { poolTypeVersion: 1 }
                            ] },
                            { poolType_contains_nocase: "Gyro" },
                        ] }
                    ]
                }
            ) {
                id,
                symbol
            }
        }"""
        r = requests.post(url, json={"query": query})
        r.raise_for_status()
        try:
            for pool in r.json()["data"]["pools"]:
                filtered_pools[pool["id"]] = pool["symbol"]
        except KeyError:
            # no results for this chain
            pass
        return filtered_pools

    def has_alive_preferential_gauge(self, pool_id: str) -> bool:
        """
        check if a pool has an alive preferential gauge using a fresh query to the subgraph

        params:
        - chain: name of the chain
        - pool_id: id of the pool

        returns:
        - True if the pool has a preferential gauge which is not killed
        """
        url = BalUtils.get_subgraph_url(self.chain, "gauges")
        query = f"""{{
            liquidityGauges(
                where: {{
                    poolId: "{pool_id}",
                    isKilled: false,
                    isPreferentialGauge: true
                }}
            ) {{
                id
            }}
        }}"""
        r = requests.post(url, json={"query": query})
        r.raise_for_status()
        try:
            result = r.json()["data"]["liquidityGauges"]
        except KeyError:
            result = []
        if len(result) > 0:
            return True
        else:
            print(f"Pool {pool_id} on {self.chain} has no alive preferential gauge")

    def build_core_pools(self):
        """
        build the core pools dictionary by taking pools from `get_pools_with_rate_provider` and:
        - check if the pool has an alive preferential gauge
        - add pools from whitelist
        - remove pools from blacklist

        params:
        chain: name of the chain

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