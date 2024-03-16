import json

from bal_addresses.pools_gauges import BalPoolsGauges


def main():
    core_pools = {}

    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["CHAIN_IDS_BY_NAME"]:
        gauge_info = BalPoolsGauges(chain)

        # core pools
        if chain in ["sepolia", "goerli"]:
            continue
        core_pools[chain] = gauge_info.core_pools

    # dump the collected dict to json file
    with open("outputs/core_pools.json", "w") as f:
        json.dump(core_pools, f, indent=2)


if __name__ == "__main__":
    main()
