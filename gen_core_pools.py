import json
from bal_tools import BalPoolsGauges


def main():
    core_pools = {}

    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["BALANCER_PRODUCTION_CHAINS"]:
        gauge_info = BalPoolsGauges(chain)
        core_pools[chain] = gauge_info.build_core_pools()

    # dump the collected dict to json file
    with open("outputs/core_pools.json", "w") as f:
        core_pools_dict = {}
        for chain in core_pools:
            core_pools_dict[chain] = core_pools[chain].pools
        json.dump(core_pools_dict, f, indent=2)


if __name__ == "__main__":
    main()
