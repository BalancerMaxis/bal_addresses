from collections import defaultdict
from urllib.request import urlopen

import requests

from bal_addresses.errors import GraphQLRequestError


class SubgraphQueries:
    def get_subgraph_url(self, chain: str, subgraph="core") -> str:
        """
        perform some soup magic to determine the latest subgraph url used in the official frontend

        params:
        - chain: name of the chain
        - subgraph: "core", "gauges" or "aura"

        returns:
        - https url of the subgraph
        """
        chain = "gnosis-chain" if chain == "gnosis" else chain

        if subgraph == "core":
            magic_word = "subgraph:"
        elif subgraph == "gauges":
            magic_word = "gauge:"
        elif subgraph == "aura":
            if chain == "zkevm":
                return "https://subgraph.satsuma-prod.com/ab0804deff79/1xhub-ltd/aura-finance-zkevm/api"
            elif chain in ["avalanche"]:
                return None
            else:
                return (
                    f"https://graph.aura.finance/subgraphs/name/aura/aura-{chain}-v2-1"
                )
        elif subgraph == "blocks":
            return defaultdict(
                lambda: None,
                blocks={
                    "mainnet": "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks",
                    "arbitrum": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-one-blocks",
                    "polygon": "https://api.thegraph.com/subgraphs/name/ianlapham/polygon-blocks",
                    "base": "https://api.studio.thegraph.com/query/48427/bleu-base-blocks/version/latest",
                    "gnosis": "https://api.thegraph.com/subgraphs/name/rebase-agency/gnosis-chain-blocks",
                    "avalanche": "https://api.thegraph.com/subgraphs/name/iliaazhel/avalanche-blocks",
                    "zkevm": "https://api.studio.thegraph.com/query/48427/bleu-polygon-zkevm-blocks/version/latest",
                },
            )

        # get subgraph url from production frontend
        frontend_file = f"https://raw.githubusercontent.com/balancer/frontend-v2/develop/src/lib/config/{chain}/index.ts"
        found_magic_word = False
        with urlopen(frontend_file) as f:
            for line in f:
                if found_magic_word:
                    return line.decode("utf-8").strip().strip(" ,'")
                if magic_word + " " in str(line):
                    # url is on same line
                    return line.decode("utf-8").split(magic_word)[1].strip().strip(",'")
                if magic_word in str(line):
                    # url is on next line, return it on the next iteration
                    found_magic_word = True

    def get_first_block_after_utc_timestamp(self, timestamp: int):
        result = self.fetch_graphql_data(
            self.GET_FIRST_BLOCK_AFTER_TIMESTAMP, {"timestamp": int(timestamp)}
        )
        return int(result["data"]["blocks"][0]["number"])

    def fetch_graphql_data(self, query_object, variables=None):
        if variables:
            response = requests.post(
                query_object["endpoint"],
                json={"query": query_object["query"], "variables": variables},
            )
        else:
            response = requests.post(
                query_object["endpoint"], json={"query": query_object["query"]}
            )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise GraphQLRequestError(f"HTTP Error: {e}")
        data = response.json()
        if "errors" in data:
            raise GraphQLRequestError(f"Error: {data['errors']}")
        return data

    def __init__(self, chain):
        self.chain = chain
        self.subgraph_url = {
            "balancer": self.get_subgraph_url(chain, "core"),
            "gauges": self.get_subgraph_url(chain, "gauges"),
            "aura": self.get_subgraph_url(chain, "aura"),
            "blocks": self.get_subgraph_url(chain, "blocks"),
        }

        ## TODO add asert that result list is < 1000 due to first: 1000 in the query
        self.BALANCER_POOL_SHARES_QUERY = {
            "endpoint": self.subgraph_url["balancer"],
            "query": """
    query GetUserPoolBalances($poolId: ID!, $block: Int) {
        pool(id: $poolId, block: {number: $block}) {
            shares(where: {balance_gt: "0"}, orderBy: balance, orderDirection: desc) {
                userAddress {
                    id
                }
                balance
            }
        }
    }
""",
        }
        ## TODO think about pagination above

        self.BALANCER_GAUGES_SHARES_QUERY = {
            "endpoint": self.subgraph_url["balancer"],
            "query": """
        query FetchGaugeShares($gaugeAddress: String!, $block: Int) {
          gaugeShares(
            block: {number: $block}
            where: {gauge_contains_nocase: $gaugeAddress, balance_gt: "0"}
            orderBy: balance
            orderDirection: desc
            first: 1000
          ) {
            balance
            id
            user {
              id
            }
          }
        }
        """,
        }

        # --- AURA QUERIES ---
        self.AURA_SHARES_QUERY = {
            "endpoint": self.subgraph_url["balancer"],
            "query": """
        query PoolLeaderboard($poolId: ID!, $block: Int) {
          leaderboard: pool(id: $poolId, block: {number: $block}) {
            accounts(
              first: 1000
              where: {staked_gt: 0}
              orderBy: staked
              orderDirection: desc
            ) {
              staked
              pool {
                id
              }
              account {
                id
              }
            }
            totalStaked
          }
        }
        """,
        }

        self.AURA_GAUGE_MAPPINGS_QUERY = {
            "endpoint": self.subgraph_url["balancer"],
            "query": """
query getAuraGaugeMappings {
  gauges(first: 1000) {
    pool {
      id
      gauge {
        id
      }
    }
  }
}

""",
            # --- GENERAL QUERIES ---
        }
        self.GET_FIRST_BLOCK_AFTER_TIMESTAMP = {
            "endpoint": self.subgraph_url["balancer"],
            "query": """
query FirstBlockAfterTimestamp($timestamp: Int) {
  blocks(first: 1, orderBy: number, orderDirection: asc, where: {timestamp_gt: $timestamp}) {
    number,
    timestamp
  }
}
""",
        }
