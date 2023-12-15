import json
import urllib.request

import pandas as pd
import requests


NO_GAUGE_SUBGRAPH = ["bsc", "kovan", "fantom", "rinkeby"]


def get_subgraph_url(chain_name: str, subgraph="core"):
    chain_name = "gnosis-chain" if chain_name == "gnosis" else chain_name
    frontend_file = f"https://raw.githubusercontent.com/balancer/frontend-v2/develop/src/lib/config/{chain_name}/index.ts"
    if subgraph == "core":
        magic_word = "subgraph:"
    elif subgraph == "gauges":
        magic_word = "gauge:"
    found_magic_word = False
    with urllib.request.urlopen(frontend_file) as f:
        for line in f:
            if found_magic_word:
                return line.decode("utf-8").strip().strip(" ,'")
            if magic_word + " " in str(line):
                # url is on same line
                return line.decode("utf-8").split(magic_word)[1].strip().strip(",'")
            if magic_word in str(line):
                # url is on next line, return it on the next iteration
                found_magic_word = True


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
        print("found duplicate symbols!")
        print(df[df["symbol"].duplicated(keep=False)].sort_values("symbol"))
        raise
    print(df.info())
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
