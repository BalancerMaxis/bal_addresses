import pytest

from bal_addresses import AddrBook


@pytest.fixture(scope="module", params=list(AddrBook.chains["CHAIN_IDS_BY_NAME"]))
def chain(request):
    chain = request.param
    return chain
