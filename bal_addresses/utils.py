import json
from urllib.request import urlopen
import requests

def get_subgraph_url(chain: str, subgraph="core") -> str:
    """
    perform some soup magic to determine the latest subgraph url used in the official frontend

    params:
    - chain: name of the chain
    - subgraph: "core" or "gauges"

    returns:
    - https url of the subgraph
    """
    chain = "gnosis-chain" if chain == "gnosis" else chain
    frontend_file = f"https://raw.githubusercontent.com/balancer/frontend-v2/develop/src/lib/config/{chain}/index.ts"
    if subgraph == "core":
        magic_word = "subgraph:"
    elif subgraph == "gauges":
        magic_word = "gauge:"
    found_magic_word = False
    with urlopen(frontend_file) as f:
        for line in f:
            if found_magic_word:
                return line.decode("utf-8").strip().strip(" ,'")
            if magic_word + " " in str(line):
                # url is on same line
                return line.decode("utf-8").split(magic_word)[1].strip().strip(",'")
            if magic_word in str(line):
                # url is on next line, return it on the next iteration
                found_magic_word = True


def get_pools_with_rate_provider(chain: str = None) -> dict:
    """
    for every chain, query the official balancer subgraph and retrieve pools that meets
    all three of the following conditions:
    - have a rate provider different from address(0)
    - have a liquidity greater than $250k
    - either:
      - have a yield fee > 0
      - be a meta stable pool with swap fee > 0
      - be a gyro pool

    params:
    - chain: name of the chain, if None, all chains will be queried

    returns:
    dictionary of the format {chain_name: {pool_id: symbol}}
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
                        { or: [
                            { protocolYieldFeeCache_gt: 0 },
                            { and: [
                                { swapFee_gt: 0 },
                                { poolType_contains: "MetaStable" },
                                { poolTypeVersion: 1 }
                            ] },
                            { poolType_contains_nocase: "Gyro" },
                        ] }
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
    """
    check if a pool has an alive preferential gauge using a fresh query to the subgraph

    params:
    - chain: name of the chain
    - pool_id: id of the pool

    returns:
    - True if the pool has a preferential gauge which is not killed
    """
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
    build the core pools dictionary by taking pools from `get_pools_with_rate_provider` and:
    - check if the pool has an alive preferential gauge
    - add pools from whitelist
    - remove pools from blacklist

    params:
    chain: name of the chain, if None, all chains will be queried

    returns:
    dictionary of the format {chain_name: {pool_id: symbol}}
    """
    core_pools = get_pools_with_rate_provider(chain)

    # make sure the pools have an alive preferential gauge
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