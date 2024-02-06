from bal_addresses.utils import build_core_pools, has_alive_preferential_gauge


def has_alive_preferential_gauge(chain: str, pool_id: str) -> bool:
    """
    check if a pool has an alive preferential gauge

    params:
    chain: string format is the same as in extras/chains.json
    pool_id: this is the long version of a pool id, so contract address + suffix

    returns:
    True if the pool has an alive preferential gauge
    """
    return has_alive_preferential_gauge(chain, pool_id)


def get_core_pools(chain: str) -> dict:
    """
    get the core pools for a chain

    params:
    chain: string format is the same as in extras/chains.json

    returns:
    dictionary of the format {pool_id: symbol}
    """
    core_pools = build_core_pools(chain)
    return core_pools[chain]


def is_core_pool(chain: str, pool_id: str) -> bool:
    """
    check if a pool is a core pool using a fresh query to the subgraph

    params:
    chain: string format is the same as in extras/chains.json
    pool_id: this is the long version of a pool id, so contract address + suffix

    returns:
    True if the pool is a core pool
    """
    core_pools = build_core_pools(chain)
    return pool_id in core_pools[chain]
