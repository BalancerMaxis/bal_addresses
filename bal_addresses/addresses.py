
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

    def __init__(self, chain, jsonfile=False):
        self.jsonfile=jsonfile
        self.chain = chain
        self.dotmap = self.build_dotmap()
        deployments = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/deployments.json").json()
        self.deployments_only = DotMap(deployments["active"][chain] | deployments["old"][chain])

        try:
            self.flatbook = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/{chain}.json").json()
            self.reversebook = DotMap(requests.get(f"{self.GITHUB_RAW_OUTPUTS}/{chain}_reverse.json").json())
        except:
            self.flatbook = {"zero/zero": self.ZERO_ADDRESS }
            self.reversebook = {self.ZERO_ADDRESS: "zero/zero"}


    def search_unique(self, substr):
        results = [s for s in self.flatbook.keys() if substr in s]
        assert not len(results) > 1, f"search_contract: Multiple matches found: {results}"
        assert not len(results) < 1, f"{substr} NotFound"
        return results[0]

    def search_many(self, substr):
        search = [s for s in self.flatbook.keys() if substr in s]
        results = {key: self.flatbook[key] for key in search if key in self.flatbook}
        return results

    def latest_contract(self, contract_name):
        deployments = []
        for deployment, contractData in self.deployments_only.items():
            if list(contractData.keys())[0] == contract_name:
                deployments.append(deployment)
        assert len(deployments) > 0, "NotFound"
        deployments.sort(reverse=True)
        return self.deployments_only[deployments[0]][contract_name]


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

    def build_dotmap(self):
        if self.jsonfile:
            with open(self.jsonfile, "r") as f:
                fullbook = json.load(f)
        else:
            fullbook = self.fullbook
        return(DotMap(fullbook["active"].get(self.chain, {}) | fullbook["old"].get(self.chain, {})))
        ### Checksum one more time for good measure

    def flatten_dict(self, d, parent_key='', sep='/'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def generate_flatbook(self):
        print(f"Generating Addressbook for {self.chain}")
        monorepo_addresses = {}
        dupContracts = {}
        ab = dict(self.dotmap)
        return(self.flatten_dict(ab))



#  Version outside class to allow for recursion on the uninitialized class
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