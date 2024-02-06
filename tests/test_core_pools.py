from bal_addresses.api import is_core_pool


def test_is_core_pool():
    """
    confirm wstETH-WETH is a core pool
    """
    assert is_core_pool(
        "mainnet", "0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd0000000000000000000005c2"
    )
