import json
from bal_tools import BalPoolsGauges


def main():
    core_pools_all_chains = BalPoolsGauges().build_core_pools(return_all_chains=True)

    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["BALANCER_PRODUCTION_CHAINS"]:
        assert chain in core_pools_all_chains, f"Missing core pools entry for {chain}"

    # dump the collected dict to json file
    with open("outputs/core_pools.json", "w") as f:
        json.dump(core_pools_all_chains, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
