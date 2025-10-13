import json

import pandas as pd

from bal_tools import BalPoolsGauges


def process_query_pools(result) -> dict:
    flattened_result = []
    for pool_data in result:
        if pool_data.symbol.startswith("circlesBackingLBP"):
            continue
        if pool_data.symbol.startswith("WETH-EIGEN"):
            continue
        flattened_result.append(
            {"address": pool_data.address, "symbol": pool_data.symbol}
        )
    df = pd.DataFrame(flattened_result)
    if len(df) == 0:
        return
    # assert no duplicate addresses exist
    assert len(df["address"].unique()) == len(df)

    # solve issue of duplicate pool symbols by appending address prefix
    df["original_symbol"] = df["symbol"]
    df["symbol"] = df["symbol"] + "-" + df["address"].str[2:6]

    # only extend address suffix for symbols that still have collisions
    colliding_symbols = df[df["symbol"].duplicated(keep=False)][
        "original_symbol"
    ].unique()
    for original_symbol_with_collision in colliding_symbols:
        collision_group_mask = df["original_symbol"] == original_symbol_with_collision
        collision_group = df[collision_group_mask]

        for address_suffix_length in range(4, 43):  # max 40 hex chars in address
            symbols_with_longer_suffix = (
                collision_group["original_symbol"]
                + "-"
                + collision_group["address"].str[2 : 2 + address_suffix_length]
            )
            if symbols_with_longer_suffix.nunique() == len(symbols_with_longer_suffix):
                df.loc[collision_group_mask, "symbol"] = symbols_with_longer_suffix
                break

    df = df.drop(columns=["original_symbol"])

    # confirm no duplicate symbols exist, raise if so
    if len(df["symbol"].unique()) != len(df):
        print("Found duplicate symbols!")
        print(df[df["symbol"].duplicated(keep=False)].sort_values("symbol"))
        raise
    return df.sort_values("address").set_index("symbol")["address"].to_dict()


def process_query_gauges(result) -> dict:
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
    return df.sort_values("address").set_index("symbol")["address"].to_dict()


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
        result = process_query_pools(pool_gauge_info.query_all_pools())
        if result:
            pools[chain] = result
        # gauges
        result = process_query_gauges(pool_gauge_info.query_all_gauges())
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
        f.write("\n")
    with open("outputs/gauges.json", "w") as f:
        json.dump(gauges, f, indent=2)
        f.write("\n")
    with open("outputs/root_gauges.json", "w") as f:
        json.dump(root_gauges, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
