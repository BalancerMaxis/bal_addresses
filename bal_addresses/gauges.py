from bal_addresses import utils as BalUtils
import json
from urllib.request import urlopen
import requests

class BalGauges:
    def __init__(self, chain):
        self.chain = chain
        self.core_pools = BalUtils.build_core_pools(chain)


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
            result += self.query_preferential_gauges(self.chain, skip + step_size, step_size)
        return result
