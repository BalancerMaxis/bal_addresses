import json

import pandas as pd
import requests

from bal_addresses.utils import get_subgraph_url


NO_GAUGE_SUBGRAPH = ["bsc", "kovan", "fantom", "rinkeby"]


def query_swap_enabled_pools(chain_name, skip=0, step_size=100) -> list:
    url = get_subgraph_url(chain_name, "core")
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
        result += query_swap_enabled_pools(chain_name, skip + step_size, step_size)
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


def query_preferential_gauges(chain_name, skip=0, step_size=100) -> list:
    url = get_subgraph_url(chain_name, "gauges")
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
        result += query_preferential_gauges(chain_name, skip + step_size, step_size)
    return result


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
        # pools
        result = process_query_swap_enabled_pools(query_swap_enabled_pools(chain))
        if result:
            pools[chain] = result
        with open(f"extras/pools.json", "w") as f:
            json.dump(pools, f, indent=2)

        # gauges
        if chain in NO_GAUGE_SUBGRAPH:
            # no (gauge) subgraph exists for this chain
            continue
        result = process_query_preferential_gauges(query_preferential_gauges(chain))
        if result:
            gauges[chain] = result
        with open("extras/gauges.json", "w") as f:
            json.dump(gauges, f, indent=2)


if __name__ == "__main__":
    main()
