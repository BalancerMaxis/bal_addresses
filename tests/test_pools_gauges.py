import pytest

EXAMPLE_PREFERENTIAL_GAUGES = {
    "mainnet": "0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd0000000000000000000005c2",  # wsteTH-WETH
}
EXAMPLE_CORE_POOLS = {
    "mainnet": "0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd0000000000000000000005c2",  # wsteTH-WETH
    "polygon": "0xcd78a20c597e367a4e478a2411ceb790604d7c8f000000000000000000000c22",  # maticX-WMATIC-BPT
    "arbitrum": "0x0c8972437a38b389ec83d1e666b69b8a4fcf8bfd00000000000000000000049e",  # wstETH/rETH/sfrxETH
    "base": "0xc771c1a5905420daec317b154eb13e4198ba97d0000000000000000000000023",  # "rETH-WETH-BPT"
}
EXAMPLE_YIELD_FEE_EXEMPT_TRUE = {
    "gnosis": "0xdd439304a77f54b1f7854751ac1169b279591ef7000000000000000000000064"
}


def test_has_alive_preferential_gauge(bal_pools_gauges):
    """
    confirm example alive preferential gauge can be found
    """
    try:
        example = EXAMPLE_PREFERENTIAL_GAUGES[bal_pools_gauges.chain]
    except KeyError:
        pytest.skip(f"Skipping {bal_pools_gauges.chain}, no example preferential gauge")

    assert bal_pools_gauges.has_alive_preferential_gauge(example)


def test_core_pools_dict(bal_pools_gauges):
    """
    confirm we get a dict back with entries
    """
    core_pools = bal_pools_gauges.core_pools
    assert isinstance(core_pools, dict)


def test_core_pools_attr(bal_pools_gauges):
    """
    confirm example core pool is in the dict
    """
    core_pools = bal_pools_gauges.core_pools

    try:
        example = EXAMPLE_CORE_POOLS[bal_pools_gauges.chain]
    except KeyError:
        pytest.skip(f"Skipping {bal_pools_gauges.chain}, no example core pools")

    assert example in core_pools


def test_is_core_pool(bal_pools_gauges):
    """
    confirm example core pool is present
    """
    try:
        example = EXAMPLE_CORE_POOLS[bal_pools_gauges.chain]
    except KeyError:
        pytest.skip(f"Skipping {bal_pools_gauges.chain}, no example core pools")

    assert bal_pools_gauges.is_core_pool(example)


def test_is_core_pool_false(bal_pools_gauges):
    """
    confirm spoofed core pool is not present
    """
    with pytest.raises(AssertionError):
        assert bal_pools_gauges.is_core_pool(
            "0x0000000000000000000000000000000000000000000000000000000000000000"
        )


def test_is_pool_exempt_from_yield_fee(bal_pools_gauges):
    """
    confirm example pool is exempt from yield fee
    """
    try:
        example = EXAMPLE_YIELD_FEE_EXEMPT_TRUE[bal_pools_gauges.chain]
    except KeyError:
        pytest.skip(
            f"Skipping {bal_pools_gauges.chain}, no example yield fee exempt pool"
        )

    assert bal_pools_gauges.is_pool_exempt_from_yield_fee(example)


def test_build_core_pools(bal_pools_gauges):
    """
    confirm core_pools can be built and is a dict
    """
    assert isinstance(bal_pools_gauges.build_core_pools(), dict)
