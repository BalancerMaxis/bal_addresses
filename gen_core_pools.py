import json

from bal_addresses import AddrBook
from bal_addresses.pools_gauges import BalPoolsGauges


if __name__ == "__main__":
    chains = AddrBook.chains

    # build core pools for every chain and dump result to json
    all_core_pools = {}
    for chain in chains["CHAIN_IDS_BY_NAME"]:
        if chain in ["sepolia", "goerli"]:
            continue
        all_core_pools[chain] = BalPoolsGauges(chain).build_core_pools()

    json.dump(all_core_pools, open("outputs/core_pools.json", "w"), indent=2)
