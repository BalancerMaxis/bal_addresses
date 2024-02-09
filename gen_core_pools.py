import json

from bal_addresses.utils import build_core_pools


if __name__ == "__main__":
    with open("extras/chains.json", "r") as f:
        chains = json.load(f)

    # build core pools for every chain and dump result to json
    all_core_pools = {}
    for chain in chains["CHAIN_IDS_BY_NAME"]:
        if chain in ["sepolia", "goerli"]:
            continue
        all_core_pools[chain] = build_core_pools(chain)

    json.dump(all_core_pools, open("outputs/core_pools.json", "w"), indent=2)
