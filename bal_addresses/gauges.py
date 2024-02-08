from bal_addresses import utils as BalUtils
from bal_addresses.graphql_queries import GraphQueries
from typing import Dict
from .errors import SumsDoNotMatchError
import json
from urllib.request import urlopen
import requests
from collections import defaultdict

AURA_BOOSTER_ADDRESS = "0xA57b8d98dAE62B26Ec3bcC4a365338157060B234" ## TODO check if this is different off mainnet
class BalGauges:
    def __init__(self, chain):
        self.chain = chain
        # TODO move build_core_pools into lib and figure out how to deal with the need for a global call.
        self.core_pools = BalUtils.build_core_pools(chain)
        self.queries = GraphQueries(self.chain)
    def get_aura_gauge_mappings(self) -> Dict[str, int]:
        """
        Returns a map like {"gauge_address": int(pid_number)} with all aura gauges on the operating chain
        """
        query = self.queries.AURA_GAUGE_MAPPINGS_QUERY
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"])
        aura_pid_by_gauge = {}
        for result_item in data["data"]["gauges"]:
            aura_pid_by_gauge[result_item["pool"]["gauge"]["id"]] = [result_item["pool"]["id"]]
        return aura_pid_by_gauge

    def get_aura_pid_from_gauge(self, deposit_gauge_address: str) -> int:
        return int(self.get_aura_gauge_mappings()[deposit_gauge_address][0])

    def get_bpt_balances(self, pool_id, block) -> Dict[str, int]:
        query = self.queries.BALANCER_POOL_SHARES_QUERY
        variables = {"poolId": pool_id, "block": block}
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"], variables)
        results = {}
        if data and 'data' in data and 'pool' in data['data'] and data['data']['pool']:
            for share in data['data']['pool']['shares']:
                results[share['userAddress']['id']] = share['balance']
        return results

    def get_gauge_deposit_shares(self, gauge_address, block) -> Dict[str, int]:
        query = self.queries.BALANCER_GAUGES_SHARES_QUERY
        variables = {
            "gaugeAddress": gauge_address,
            "block": block
        }
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"], variables)
        results = {}
        if 'data' in data and 'gaugeShares' in data['data']:
            for share in data['data']['gaugeShares']:
                results[share['user']['id']] = share['balance']
        return results

    def get_aura_pool_shares(self, gauge_address,  block) -> Dict[str, int]:
        # Prepare the GraphQL query and variables
        aura_pid = self.get_aura_pid_from_gauge(gauge_address)
        query = self.queries.AURA_SHARES_QUERY
        variables = {"poolId": aura_pid, "block": block}
        data = BalUtils.fetch_graphql_data(query["endpoint"], query["query"], variables)
        results = {}

        # Parse the data if the query was successful
        if data and 'data' in data and 'leaderboard' in data['data'] and data['data']['leaderboard']['accounts']:
            for account in data['data']['leaderboard']['accounts']:
                results[account['account']['id']] =  account['staked']
        return results

    def get_ecosystem_balances(self, pool_id, gauge_address, block) -> Dict[str, int]:
        bpts_in_bal_gauge = 0
        bpts_in_aura=0
        total_circulating_bpts=0
        total_bpts_counted=0
        ## Start with raw BPTS
        ecosystem_balances = defaultdict(int,  self.get_bpt_balances(pool_id, block))
        for address, amount in ecosystem_balances.items():
            total_circulating_bpts += float(amount)
        ## Factor in Gauge Deposits
        if gauge_address in ecosystem_balances.keys():
            # Verify that there are some gauge deposits and null them out so balances add up
            bpts_in_bal_gauge = ecosystem_balances[gauge_address]
            ecosystem_balances[gauge_address] = 0
            ## TODO think about what to do about pool tokens in the vault, how that works with subgraph magic
        else:
            print(f"WARNING: there are no BPTs from {pool_id} staked in the gauge at {gauge_address} did you cross wires, or is there no one staked?")

        for address, amount in  self.get_gauge_deposit_shares(gauge_address, block):
            ecosystem_balances[address] += float(amount)

        ## Factor in Aura Deposits
        if AURA_BOOSTER_ADDRESS in ecosystem_balances.keys():
            bpts_in_aura = ecosystem_balances[AURA_BOOSTER_ADDRESS]
            ecosystem_balances[AURA_BOOSTER_ADDRESS] = 0
        else:
            print(f"WARNING: there are no BPTs from {pool_id} staked in Aura did you cross wires, or is there no one staked?")
        for address,amount in self.get_aura_pool_shares(gauge_address, block):
            ecosystem_balances[address] += float(amount)

        ## CHeck everything
        print(ecosystem_balances)
        for address, amount in ecosystem_balances.items():
            total_bpts_counted += float(amount)
        print(f"Found {total_circulating_bpts} of which {bpts_in_bal_gauge} where staked by an address in a bal gauge and {bpts_in_aura} where deposited on aura at block {block}")
        if total_bpts_counted != total_circulating_bpts:
            raise SumsDoNotMatchError(f"initial bpts found{total_circulating_bpts}, final bpts counted:{total_bpts_counted}")
        return ecosystem_balances


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
