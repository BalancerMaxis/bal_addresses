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
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/extras/mainnet.json",
        json={
            "zero": {
                "zero": "0x0000000000000000000000000000000000000000"
            },
            "balancer": {}

            }
    )
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/extras/multisigs.json",
        json={
            "mainnet": {
                "dao": "0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f",
            }
        }
    )
    a = AddrBook("mainnet")

    a.populate_deployments()
    assert a.deployments.vault.status == "ACTIVE"
    assert a.deployments.vault.contracts.Vault.name == "Vault"
    assert (
        a.deployments.vault.contracts.Vault.address == "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
    )
    assert a.deployments.vault.contracts.BalancerHelpers.name == "BalancerHelpers"
    # Make sure that when we try to access a non-existing attribute, we get an error
    with pytest.raises(AttributeError):
        assert a.deployments.vault.non_existing_attribute
    a.populate_extras()
    assert a.extras.zero.zero == "0x0000000000000000000000000000000000000000"
    # Make sure that when we try to access a non-existing attribute, we get an error
    with pytest.raises(AttributeError):
        assert a.extras.balancer.non_existing_attribute
    a.populate_multisigs()
    print(a.multisigs)
    assert a.multisigs.dao == "0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f"

@responses.activate
def test_deployments_invalid_format():
    """
    Make sure that library is data agnostic and can handle different formats
    """
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
                "contracts": {'name': 'Vault'},
                "status": "ACTIVE"
            }
        }
    )
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/extras/mainnet.json",
        json={
            "vault": {
                "contracts": {'name': 'Vault'},
                "status": "ACTIVE"
            }
        }
    )
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/extras/multisigs.json",
        json={
            "mainnet": {
                "contracts": {'name': 'Vault'},
                "status": "ACTIVE"
            }
        }
    )
    a = AddrBook("mainnet")

    a.populate_deployments()
    assert a.deployments.vault.contracts.name == "Vault"
    a.populate_extras()
    print(a.extras.vault.status)
    assert a.extras.vault.status == "ACTIVE"
    a.populate_multisigs()
    assert str(a.multisigs.status) == "ACTIVE"


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
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/extras/mainnet.json",
        json={},
        status=404
    )
    responses.add(
        responses.GET,
        "https://raw.githubusercontent.com/BalancerMaxis"
        "/bal_addresses/main/extras/multisigs.json",
        json={},
        status=404
    )
    a = AddrBook("mainnet")
    assert a.deployments is None
    with pytest.raises(AttributeError):
        assert a.deployments.vault.non_existing_attribute
    assert a.extras == {}
    with pytest.raises(AttributeError):
        assert a.extras.non_existing_attribute
    assert a.multisigs == {}
    with pytest.raises(AttributeError):
        assert a.multisigs.non_existing_attribute