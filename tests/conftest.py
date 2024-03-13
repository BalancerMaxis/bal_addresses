import pytest

from bal_addresses import AddrBook
from bal_addresses.pools_gauges import BalPoolsGauges
from bal_addresses.subgraph import Subgraph


@pytest.fixture(scope="module", params=list(AddrBook.chains["CHAIN_IDS_BY_NAME"]))
def chain(request):
    chain = request.param
    if chain in ["sepolia", "goerli"]:
        pytest.skip(f"Skipping {chain} testnet")
    return chain


@pytest.fixture(scope="module")
def bal_pools_gauges(chain):
    return BalPoolsGauges(chain)


@pytest.fixture(scope="module")
def subgraph(chain):
    return Subgraph(chain)
