
import json
from web3 import Web3
import requests
from dotmap import DotMap


class AddrBook:
    GITHUB_MONOREPO_RAW = "https://raw.githubusercontent.com/balancer-labs/balancer-v2-monorepo/master"
    GITHUB_MONOREPO_NICE = "https://github.com/balancer/balancer-v2-monorepo/blob/master"
    GITHUB_RAW_OUTPUTS = "https://raw.githubusercontent.com/BalancerMaxis/bal-maxi-addresses/main/outputs"
    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
    CHAIN_IDS_BY_NAME = {
        "mainnet": 1,
        "polygon": 137,
        "arbitrum": 42161,
        "optimism": 10,
        "gnosis": 100,
        "goerli": 42,
        "sepolia": 11155111
    }

    SCANNERS_BY_CHAIN = {
        "mainnet": "https://etherscan.io",
        "polygon": "https://polygonscan.com",
        "arbitrum": "https://arbiscan.io",
        "optimism": "https://optimistic.etherscan.io",
        "gnosis": "https://gnosisscan.io",
        "goerli": "https://goerli.etherscan.io/",
        "sepolia": "https://sepolia.etherscan.io/"
    }
    fullbook = requests.get(f"{GITHUB_RAW_OUTPUTS}/addressbook.json").json()
    fx_description_by_name = requests.get("https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/func_desc_by_name.json").json

    def __init__(self, chain):
        self.dotmap = DotMap(self.fullbook["active"].get(chain, {})  | self.fullbook["old"].get(chain, {}))
        try:
            self.flatbook = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/{chain}.json").json()
            self.reversebook = DotMap(requests.get(f"{self.GITHUB_RAW_OUTPUTS}/{chain}_reverse.json").json())
        except:
            self.flatbook = {"zero/zero": self.ZERO_ADDRESS }
            self.reversebook = {self.ZERO_ADDRESS: "zero/zero"}
        self.chain = chain

    def generate_flatbook(self):  ## TODO retire
        print(f"Generating Addressbook for {self.chain}")
        monorepo_addresses = {}
        dupContracts = {}
        ab = self.dotmap
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
            data = data[self.chain]
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
        try:
            with open(f"extras/{self.chain}.json") as f:
                data = json.load(f)
        except:
                data = {}
        data = checksum_address_dict(data)
        for group, t in data.items():
            for name, address in t.items():
                monorepo_addresses[f"{group}/{name}"] = address
        ### Checksum one more time for good measure
        monorepo_addresses = checksum_address_dict(monorepo_addresses)
        return DotMap(monorepo_addresses)


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


