import os
import json

INFURA_KEY = os.environ["WEB3_INFURA_PROJECT_ID"]


CHAIN_IDS_BY_NAME = {
    "mainnet": 1,
    "polygon": 137,
    "arbitrum": 42161,
    "optimism": 10,
    "gnosis": 100,
    "goerli": 42
}

SCANNERS_BY_CHAIN = {
    "mainnet": "https://etherscan.io",
    "polygon": "https://polygonscan.com",
    "arbitrum": "https://arbiscan.io",
    "optimism": "https://optimistic.etherscan.io",
    "gnosis": "https://gnosisscan.io",
    "goerli": "https://goerli.etherscan.io/"
}


def gen_allchain_addresses(chain):
    with open("addressbook.json", "r") as f:
        data = json.load(f)
    chainbook = data["active"][chain] | data["old"][chain]
    return chainbook


def addressbook_by_chain(chain):  ## TODO retire
    monorepo_addresses = {}
    dupContracts = {}
    ab = gen_allchain_addresses(chain)
    for deployment, contracts in ab.items():
        for contract, address in contracts.items():
            monorepo_addresses[f"{deployment}/{contract}"] = address
        ## TODO think about using the dedup list to build a directory of most recent contracts
        if contract not in dupContracts.keys():
            dupContracts[contract] = 1
        else:
            dupContracts[contract] += 1
    ### add multisigs
    with open("extras/multisigs.json", "r") as f:
        data = json.load(f)
        data = data[chain]
        data = checksum_address_dict(data)
    for multisig, address in data.items():
        monorepo_addresses[f"multisigs/{multisig}"] = address
    ### add signers
    with open("extras/signers.json", "r") as f:
        data = json.load(f)
        data = checksum_address_dict(data)
    for group, t in data.items():
        for name, address in t.items():
            monorepo_addresses[f"EOA/{group}/{name}"] = address
    ### add extras
    with open(f"extras/{chain}.json") as f:
        data = json.load(f)
    data = checksum_address_dict(data)
    for group, t in data.items():
        for name, address in t.items():
            monorepo_addresses[f"{group}/{name}"] = address
    ### Checksum one more time for good measure
    monorepo_addresses = checksum_address_dict(monorepo_addresses)
    return monorepo_addresses



def checksum_address_dict(addresses):
    """
    convert addresses to their checksum variant taken from a (nested) dict
    """
    checksummed = {}
    for k, v in addresses.items():
        if isinstance(v, str):
            checksummed[k] = Web3.toChecksumAddress(v)
        elif isinstance(v, dict):
            checksummed[k] = checksum_address_dict(v)
        else:
            print(k, v, "formatted incorrectly")
    return checksummed


def address_lookup_dict(chain):
    ab = addressbook_by_chain(chain)
    inv_map = {v: k for k, v in ab.items()}
    return inv_map

def read_addressbook(chain):
    with open(f"outputs/{chain}.json", "r") as f:
        return json.load(f)

def read_reversebook(chain):
    with open(f"outputs/{chain}_reverse.json", "r") as f:
        return json.load(f)

def get_registry(chain):
    addressbook_by_chain(chain)



def write_addressbooks(chainlist=CHAIN_IDS_BY_NAME.keys()):
    for chain in chainlist:
        with open(f"outputs/{chain}.json", "w") as f:
            json.dump(addressbook_by_chain(chain), f, indent=3)
        with open(f"outputs/{chain}_reverse.json", "w") as f:
            json.dump(address_lookup_dict(chain), f, indent=3)

