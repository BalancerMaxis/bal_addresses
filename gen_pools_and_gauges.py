import json

import pandas as pd
import requests

from bal_addresses.pools_gauges import BalPoolsGauges
from bal_addresses.queries import SubgraphQueries


NO_GAUGE_SUBGRAPH = ["bsc", "kovan", "fantom", "rinkeby"]


def query_swap_enabled_pools(chain, skip=0, step_size=100) -> list:
    url = SubgraphQueries(chain).subgraph_url["balancer"]
    query = f"""{{
        pools(
            skip: {skip}
            first: {step_size}
            where: {{swapEnabled: true}}
        ) {{
            address
            symbol
        }}
    }}"""
    r = requests.post(url, json={"query": query})
    r.raise_for_status()
    try:
        result = r.json()["data"]["pools"]
    except KeyError:
        result = []
    if len(result) > 0:
        # didnt reach end of results yet, collect next page
        result += query_swap_enabled_pools(chain, skip + step_size, step_size)
    return result


def process_query_swap_enabled_pools(result) -> dict:
    df = pd.DataFrame(result)
    if len(df) == 0:
        return
    # assert no duplicate addresses exist
    assert len(df["address"].unique()) == len(df)

    # solve issue of duplicate gauge symbols
    df["symbol"] = df["symbol"] + "-" + df["address"].str[2:6]

    # confirm no duplicate symbols exist, raise if so
    if len(df["symbol"].unique()) != len(df):
        print("Found duplicate symbols!")
        print(df[df["symbol"].duplicated(keep=False)].sort_values("symbol"))
        raise
    return df.set_index("symbol")["address"].to_dict()


def process_query_preferential_gauges(result) -> dict:
    df = pd.DataFrame(result)
    if len(df) == 0:
        return
    # assert no duplicate addresses exist
    assert len(df["id"].unique()) == len(df)

    # solve issue of duplicate gauge symbols
    df["symbol"] = df["symbol"] + "-" + df["id"].str[2:6]

    # confirm no duplicate symbols exist, raise if so
    if len(df["symbol"].unique()) != len(df):
        print("Found duplicate symbols!")
        print(df[df["symbol"].duplicated(keep=False)].sort_values("symbol"))
        raise
    return df.set_index("symbol")["id"].to_dict()


def main():
    pools = {}
    gauges = {}
    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["CHAIN_IDS_BY_NAME"]:
        gauge_info = BalPoolsGauges(chain)
        # pools
        # TODO: consider moving to query object??
        result = process_query_swap_enabled_pools(query_swap_enabled_pools(chain))
        if result:
            pools[chain] = result
        with open(f"extras/pools.json", "w") as f:
            json.dump(pools, f, indent=2)

        # gauges
        if chain in NO_GAUGE_SUBGRAPH:
            # no (gauge) subgraph exists for this chain
            continue
        result = process_query_preferential_gauges(
            gauge_info.query_preferential_gauges()
        )
        if result:
            gauges[chain] = result
        with open("extras/gauges.json", "w") as f:
            json.dump(gauges, f, indent=2)


if __name__ == "__main__":
    main()
