import pytest

from bal_addresses import AddrBook
from bal_addresses.pools_gauges import BalPoolsGauges
from bal_addresses.subgraph import Subgraph
from bal_addresses.ecosystem import Aura


@pytest.fixture(scope="module", params=list(AddrBook.chains["CHAIN_IDS_BY_NAME"]))
def chain(request):
    chain = request.param
    return chain


@pytest.fixture(scope="module")
def bal_pools_gauges(chain):
    return BalPoolsGauges(chain)


@pytest.fixture(scope="module")
def subgraph(chain):
    return Subgraph(chain)


@pytest.fixture(scope="module")
def aura(chain):
    return Aura(chain)
