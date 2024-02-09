from bal_addresses import utils as BalUtils, Aura
from bal_addresses import GraphQueries
from typing import Dict
from .errors import ChecksumError, UnexpectedListLength
import json
from urllib.request import urlopen
import requests
from collections import defaultdict
from web3 import Web3

class BalGauges:
    def __init__(self, chain):
        self.chain = chain
        # TODO move build_core_pools into lib and figure out how to deal with the need for a global call.
        self.core_pools = BalUtils.build_core_pools(chain)
        self.queries = GraphQueries(self.chain)
        self.aura = Aura(self.chain)
        try:
            self.aura_pids_by_address = Aura.get_aura_gauge_mappings()
        except Exception as e:
            print(f"Failed to populate aura pids from aura subgraph: {e}")
            self.aura_pids_by_address = None

    def get_bpt_balances(self, pool_id, block) -> Dict[str, int]:
        query = self.queries.BALANCER_POOL_SHARES_QUERY
        variables = {"poolId": pool_id, "block": block}
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"], variables)
        results = {}
        if data and 'data' in data and 'pool' in data['data'] and data['data']['pool']:
            for share in data['data']['pool']['shares']:
                user_address = Web3.toChecksumAddress(share['userAddress']['id'])
                results[user_address] = float(share['balance'])
        return results

    def get_gauge_deposit_shares(self, gauge_address, block) -> Dict[str, int]:
        query = self.queries.BALANCER_GAUGES_SHARES_QUERY
        variables = {"gaugeAddress": gauge_address, "block": block}
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"], variables)
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
