import json

import pandas as pd
import requests

from bal_tools import BalPoolsGauges
from bal_tools import Subgraph


def query_swap_enabled_pools(chain, skip=0, step_size=100) -> list:
    url = Subgraph(chain).get_subgraph_url("core")
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


def process_query_pools(result) -> dict:
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


def process_query_gauges(result) -> dict:
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


def process_query_root_gauges(result, gauges) -> dict:
    # map to child gauges
    df = []
    for root_gauge in result:
        for chain in gauges:
            for symbol, gauge in gauges[chain].items():
                if "chain" not in root_gauge:
                    # mainnet root gauge == child gauge
                    continue
                if root_gauge["recipient"] == gauge:
                    root_gauge["symbol"] = symbol[:-4].replace(
                        "-gauge-", f"-{root_gauge['chain'].lower()}-root-"
                    )
                    root_gauge["symbol"] += f"{root_gauge['id'][2:6]}"
                    df.append(root_gauge)

    if len(df) == 0:
        return
    df = pd.DataFrame(df)

    # drop duplicates
    df = df[~df.duplicated()]

    # assert no duplicate addresses exist
    assert len(df["id"].unique()) == len(df)

    # confirm no duplicate symbols exist, raise if so
    if len(df["symbol"].unique()) != len(df):
        print("Found duplicate symbols!")
        print(df[df["symbol"].duplicated(keep=False)].sort_values("symbol"))
        raise
    return df.set_index("symbol")["id"].to_dict()


def main():
    pools = {}
    gauges = {}
    root_gauges = {}

    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["BALANCER_PRODUCTION_CHAINS"]:
        print(f"Generating pools and gauges for {chain}...")
        pool_gauge_info = BalPoolsGauges(chain)
        # pools
        result = process_query_pools(query_swap_enabled_pools(chain))
        if result:
            pools[chain] = result
        # gauges
        result = process_query_gauges(pool_gauge_info.query_preferential_gauges())
        if result:
            gauges[chain] = result
        # cache mainnet BalPoolsGauges
        if chain == "mainnet":
            gauge_info_mainnet = pool_gauge_info

    # root gauges; only on mainnet
    result = process_query_root_gauges(gauge_info_mainnet.query_root_gauges(), gauges)
    if result:
        root_gauges["mainnet"] = result

    # dump all collected dicts to json files
    with open(f"outputs/pools.json", "w") as f:
        json.dump(pools, f, indent=2)
    with open("outputs/gauges.json", "w") as f:
        json.dump(gauges, f, indent=2)
    with open("outputs/root_gauges.json", "w") as f:
        json.dump(root_gauges, f, indent=2)


if __name__ == "__main__":
    main()
