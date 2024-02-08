from bal_addresses import AddrBook

NO_BALANCER_SUBGRAPH = []
NO_GAUGE_SUBGRAPH = ["bsc", "kovan", "fantom", "rinkeby"]
NO_AURA_SUBGRAPH = ["avalanche"]


class GraphEndpoints:
    balancer = {}
    gauges = {}
    aura = {}
    for chain in AddrBook.chain_ids_by_name.keys():
        ## Mainnet often has a different URL string format
        if chain == "mainnet":
            balancer[chain] = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2"
            gauges[chain] = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-gauges"
            aura[chain] = "https://graph.aura.finance/subgraphs/name/aura/aura-mainnet-v2-1"
        ## This handles other chains which tend to follow a pattern, with some chains sometimes missing depending on the subgraph
        else:
            ## balancer
            if chain not in NO_BALANCER_SUBGRAPH:
                balancer[chain] = f"https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-{chain}-v2"
            else:
                balancer[chain] = None
            ## gauges
            if chain not in NO_GAUGE_SUBGRAPH:
                gauges[chain] = f"https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-gauges-{chain}"
            else:
                gauges[chain] = None
            ## aura
            if chain not in NO_AURA_SUBGRAPH:
                aura[chain] = f"https://graph.aura.finance/subgraphs/name/aura/aura-{chain}-v2-1"
            else:
                aura[chain] = None


class GraphQueries:
    def __init__(self, chain):
        self.chain = chain
        self.AURA_GAUGE_MAPPINGS_QUERY = {"endpoint": GraphEndpoints.aura[chain], "query": """
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
"""}
        ## TODO add asert that result list is < 1000 due to first: 1000 in the query
        self.BALANCER_POOL_SHARES_QUERY = {"endpoint": GraphEndpoints.balancer[chain], "query": """
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
"""
        }
        ## TODO think about pagination above



        self.BALANCER_GAUGES_SHARES_QUERY = {"endpoint": GraphEndpoints.gauges[chain], "query":"""
        query FetchGaugeShares($gaugeAddress: String!, $block: Int) {
          gaugeShares(
            block: {number: $block}
            where: {gauge_contains_nocase: $gaugeAddress, balance_gt: "1"}
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
        """
            }

    # --- AURA QUERIES ---
        self.AURA_SHARES_QUERY = {"endpoint": GraphEndpoints.aura[chain], "query": """
        query PoolLeaderboard($poolId: ID!, $block: Int) {
          leaderboard: pool(id: $poolId, block: {number: $block}) {
            accounts(
              first: 1000
              where: {staked_gt: 1}
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
        """
            }

        self.AURA_GAUGE_MAPPINGS_QUERY={"endpoint": GraphEndpoints.aura["chain"], "query": """
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
"""
            }

                                  
