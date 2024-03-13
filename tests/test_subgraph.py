import pytest


def test_get_first_block_after_utc_timestamp(chain, subgraph):
    """
    confirm we get the correct block number back
    """
    if chain == "mainnet":
        block = subgraph.get_first_block_after_utc_timestamp(1708607101)
        assert isinstance(block, int)
        assert block == 19283331
    else:
        pytest.skip(f"Skipping {chain}")
