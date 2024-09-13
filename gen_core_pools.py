import json
from bal_tools import BalPoolsGauges


def main():
    core_pools = {}

    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["BALANCER_PRODUCTION_CHAINS"]:
        gauge_info = BalPoolsGauges(chain)
        core_pools[chain] = gauge_info.build_core_pools().pools

    # dump the collected dict to json file
    with open("outputs/core_pools.json", "w") as f:
        json.dump(core_pools, f, indent=2)


if __name__ == "__main__":
    main()
