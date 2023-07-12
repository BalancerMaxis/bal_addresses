import pytest
import responses

from bal_addresses import AddrBook


@responses.activate
def test_deployments_populated():
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/outputs/deployments.json",
        json={
            "BFactory": "0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd",
        }
    )
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/balancer"
        "/balancer-deployments/master/addresses/mainnet.json",
        json={
            "20210418-vault": {
                "contracts": [
                    {
                        "name": "Vault",
                        "address": "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
                    },
                    {
                        "name": "BalancerHelpers",
                        "address": "0x5aDDCCa35b7A0D07C74063c48700C8590E87864E"
                    },
                    {
                        "name": "ProtocolFeesCollector",
                        "address": "0xce88686553686DA562CE7Cea497CE749DA109f9F"
                    }
                ],
                "status": "ACTIVE"
            }
        }
    )
    a = AddrBook("mainnet")

    a.populate_deployments()
    assert a.deployments.vault.status == "ACTIVE"
    assert a.deployments.vault.contracts[0].name == "Vault"
    assert a.deployments.vault.contracts[1].name == "BalancerHelpers"
    # Make sure that when we try to access a non-existing attribute, we get an error
    with pytest.raises(AttributeError):
        assert a.deployments.vault.non_existing_attribute


@responses.activate
def test_deployments_not_populated():
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/outputs/deployments.json",
        json={
            "BFactory": "0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd",
        }
    )
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/balancer"
        "/balancer-deployments/master/addresses/mainnet.json",
        json={},
        status=404
    )
    a = AddrBook("mainnet")
    assert a.deployments is None
    with pytest.raises(AttributeError):
        assert a.deployments.vault.non_existing_attribute
