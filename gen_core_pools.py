import json
from bal_tools import BalPoolsGauges


def remove_orphaned_whitelist_entries():
    """
    Remove whitelist entries that are no longer on the vebal voting list.
    Updates the whitelist file in place.
    """
    # Load whitelist
    with open("config/core_pools_whitelist.json", "r") as f:
        whitelist = json.load(f)

    orphaned_entries = {}
    updated_whitelist = {}

    # Check each chain
    for chain, whitelisted_pools in whitelist.items():
        updated_whitelist[chain] = {}

        if not whitelisted_pools:
            continue

        # Get vebal voting list for this chain
        try:
            pool_gauge = BalPoolsGauges(chain=chain, use_cached_core_pools=False)
            vebal_pool_ids = {pool["id"].lower() for pool in pool_gauge.vebal_voting_list}

            # Separate orphaned entries from valid ones
            chain_orphans = {}
            for pool_id, symbol in whitelisted_pools.items():
                if pool_id.lower() not in vebal_pool_ids:
                    chain_orphans[pool_id] = symbol
                else:
                    updated_whitelist[chain][pool_id] = symbol

            if chain_orphans:
                orphaned_entries[chain] = chain_orphans
                print(
                    f"Removing {len(chain_orphans)} orphaned whitelist entries on {chain}"
                )
                for pool_id, symbol in chain_orphans.items():
                    print(f"  - {symbol}: {pool_id}")
        except Exception as e:
            print(f"Error checking {chain}: {e}")
            # Keep original entries if there's an error
            updated_whitelist[chain] = whitelisted_pools
            continue

    # Write updated whitelist back to file
    with open("config/core_pools_whitelist.json", "w") as f:
        json.dump(updated_whitelist, f, indent=2)
        f.write("\n")

    return orphaned_entries


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

    # remove orphaned whitelist entries
    orphaned_entries = remove_orphaned_whitelist_entries()

    if orphaned_entries:
        print("\n=== Removed Orphaned Whitelist Entries ===")
        print(
            "The following whitelist entries were removed (no longer on vebal voting list):"
        )
        for chain, pools in orphaned_entries.items():
            print(f"\n{chain}:")
            for pool_id, symbol in pools.items():
                print(f"  - {symbol}: {pool_id}")


if __name__ == "__main__":
    main()
