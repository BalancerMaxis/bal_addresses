import json

import requests

from gen_pools_and_gauges import get_subgraph_url


def get_pools_with_rate_provider(chain: str = None):
    """
    for every chain, query the official balancer subgraph and retrieve pools that:
    - have a rate provider different from address(0)
    - have a liquidity greater than $250k
    - have a yield fee > 0
    """
    core_pools = {}
    if chain:
        chains = {"CHAIN_IDS_BY_NAME": [chain]}
    else:
        with open("extras/chains.json", "r") as f:
            chains = json.load(f)
    for chain in chains["CHAIN_IDS_BY_NAME"]:
        if chain in ["sepolia", "goerli"]:
            continue
        core_pools[chain] = {}
        url = get_subgraph_url(chain)
        query = """{
            pools(
                first: 1000,
                where: {
                    and: [
                        {
                            priceRateProviders_: {
                                address_not: "0x0000000000000000000000000000000000000000"
                            }
                        },
                        {
                            totalLiquidity_gt: 250000
                        },
                        {
                            protocolYieldFeeCache_gt: 0
                        }
                    ]
                }
            ) {
                id,
                symbol
            }
        }"""
        r = requests.post(url, json={"query": query})
        r.raise_for_status()
        try:
            for pool in r.json()["data"]["pools"]:
                core_pools[chain][pool["id"]] = pool["symbol"]
        except KeyError:
            # no results for this chain
            pass
    return core_pools


def has_alive_preferential_gauge(chain: str, pool_id: str) -> bool:
    url = get_subgraph_url(chain, "gauges")
    query = f"""{{
        liquidityGauges(
            where: {{
                poolId: "{pool_id}",
                isKilled: false,
                isPreferentialGauge: true
            }}
        ) {{
            id
        }}
    }}"""
    r = requests.post(url, json={"query": query})
    r.raise_for_status()
    try:
        result = r.json()["data"]["liquidityGauges"]
    except KeyError:
        result = []
    if len(result) > 0:
        return True
    else:
        print(f"Pool {pool_id} on {chain} has no alive preferential gauge")


def build_core_pools(chain: str = None):
    """
    chain string format is the same as in extras/chains.json
    """
    core_pools = get_pools_with_rate_provider(chain)

    # filter out pools without an alive preferential gauge
    for chain in core_pools:
        for pool_id in list(core_pools[chain]):
            if not has_alive_preferential_gauge(chain, pool_id):
                del core_pools[chain][pool_id]

    # add pools from whitelist
    with open("config/core_pools_whitelist.json", "r") as f:
        whitelist = json.load(f)
    for chain in whitelist:
        try:
            for pool, symbol in whitelist[chain].items():
                if pool not in core_pools[chain]:
                    core_pools[chain][pool] = symbol
        except KeyError:
            # no results for this chain
            pass

    # remove pools from blacklist
    with open("config/core_pools_blacklist.json", "r") as f:
        blacklist = json.load(f)
    for chain in blacklist:
        try:
            for pool in blacklist[chain]:
                if pool in core_pools[chain]:
                    del core_pools[chain][pool]
        except KeyError:
            # no results for this chain
            pass

    return core_pools


def is_core_pool(chain: str, pool_id: str) -> bool:
    """
    check if a pool is a core pool using a fresh query to the subgraph

    params:
    chain: string format is the same as in extras/chains.json
    pool_id: this is the long version of a pool id, so contract address + addition
    """
    core_pools = build_core_pools(chain)
    return pool_id in core_pools[chain]


if __name__ == "__main__":
    # dump result to json
    json.dump(build_core_pools(), open("outputs/core_pools.json", "w"), indent=2)
