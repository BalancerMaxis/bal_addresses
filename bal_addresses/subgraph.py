from urllib.request import urlopen
import os
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from bal_addresses import AddrBook


graphql_base_path = f"{os.path.dirname(os.path.abspath(__file__))}/graphql"

AURA_SUBGRAPHS_BY_CHAIN = {
    "mainnet": "https://graph.data.aura.finance/subgraphs/name/aura/aura-mainnet-v2-1",
    "arbitrum": "https://api.thegraph.com/subgraphs/name/aurafinance/aura-finance-arbitrum",
    "optimism": "https://api.thegraph.com/subgraphs/name/aurafinance/aura-finance-optimism",
    "gnosis": "https://api.thegraph.com/subgraphs/name/aurafinance/aura-finance-gnosis-chain",
    "base": "https://api.thegraph.com/subgraphs/name/aurafinance/aura-finance-base",
    "polygon": "https://api.thegraph.com/subgraphs/name/aurafinance/aura-finance-polygon",
    "zkevm": "https://api.studio.thegraph.com/query/69982/aura-finance-zkevm/version/latest",
    "avalanche": "https://subgraph.satsuma-prod.com/cae76ab408ca/1xhub-ltd/aura-finance-avalanche/version/v0.0.1/api",
}


class Subgraph:
    def __init__(self, chain: str):
        if chain not in AddrBook.chain_ids_by_name.keys():
            raise ValueError(f"Invalid chain: {chain}")
        self.chain = chain

    def get_subgraph_url(self, subgraph="core") -> str:
        """
        perform some soup magic to determine the latest subgraph url used in the official frontend

        params:
        - subgraph: "core", "gauges" , "blocks" or "aura"

        returns:
        - https url of the subgraph
        """
        chain = "gnosis-chain" if self.chain == "gnosis" else self.chain

        if subgraph == "core":
            magic_word = "subgraph:"
        elif subgraph == "gauges":
            magic_word = "gauge:"
        elif subgraph == "blocks":
            magic_word = "blocks:"
            ## UI has no blocks subgraph for op
            if chain == "optimism":
                return "https://api.thegraph.com/subgraphs/name/iliaazhel/optimism-blocklytics"
        elif subgraph == "aura":
            return AURA_SUBGRAPHS_BY_CHAIN.get(chain, None)

        # get subgraph url from production frontend
        frontend_file = f"https://raw.githubusercontent.com/balancer/frontend-v2/develop/src/lib/config/{chain}/index.ts"
        found_magic_word = False
        with urlopen(frontend_file) as f:
            for line in f:
                if found_magic_word:

                    url = line.decode("utf-8").strip().strip(" ,'")
                    return url
                if magic_word + " " in str(line):
                    # url is on same line
                    return line.decode("utf-8").split(magic_word)[1].strip().strip(",'")
                if magic_word in str(line):
                    # url is on next line, return it on the next iteration
                    found_magic_word = True

    def fetch_graphql_data(self, subgraph: str, query: str, params: dict = None):
        """
        query a subgraph using a locally saved query

        params:
        - query: the name of the query (file) to be executed
        - params: optional parameters to be passed to the query

        returns:
        - result of the query
        """
        # build the client
        url = self.get_subgraph_url(subgraph)
        transport = RequestsHTTPTransport(
            url=url,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)

        # retrieve the query from its file and execute it
        with open(f"{graphql_base_path}/{subgraph}/{query}.gql") as f:
            gql_query = gql(f.read())
        result = client.execute(gql_query, variable_values=params)

        return result

    def get_first_block_after_utc_timestamp(self, timestamp: int) -> int:
        data = self.fetch_graphql_data(
            "blocks", "first_block_after_ts", {"timestamp": int(timestamp)}
        )
        return int(data["blocks"][0]["number"])
