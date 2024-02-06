from bal_addresses.api import get_core_pools, has_alive_preferential_gauge, is_core_pool


def test_has_alive_preferential_gauge():
    """
    confirm wsteTH-WETH has an alive preferential gauge
    """
    assert has_alive_preferential_gauge(
        "mainnet",
        "0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd0000000000000000000005c2",
    )


def test_get_core_pools():
    """
    confirm we get a dict back with chains and pools
    """
    core_pools = get_core_pools()
    assert isinstance(core_pools, dict)
    assert "mainnet" in core_pools
    assert "polygon" in core_pools
    assert (
        "0xcd78a20c597e367a4e478a2411ceb790604d7c8f000000000000000000000c22"
        in core_pools["polygon"]
    )  # maticX-WMATIC-BPT
    assert (
        "0x0c8972437a38b389ec83d1e666b69b8a4fcf8bfd00000000000000000000049e"
        in core_pools["arbitrum"]
    )  # wstETH/rETH/sfrxETH


def test_is_core_pool():
    """
    confirm wstETH-WETH is a core pool
    """
    assert is_core_pool(
        "mainnet", "0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd0000000000000000000005c2"
    )
