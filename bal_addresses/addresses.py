
import json
from web3 import Web3
import requests
from dotmap import DotMap

## Expose some config for bootstrapping, maybe there is a better way to do this without so many github hits but allowing this to be used before invoking the class.
chains = requests.get(f"https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json").json()
CHAIN_IDS_BY_NAME = chains["CHAIN_IDS_BY_NAME"]
SCANNERS_BY_CHAIN = chains["SCANNERS_BY_CHAIN"]




### Main class
class AddrBook:
    chains = DotMap(requests.get(
        f"https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json").json())
    GITHUB_MONOREPO_RAW = "https://raw.githubusercontent.com/balancer-labs/balancer-v2-monorepo/master"
    GITHUB_MONOREPO_NICE = "https://github.com/balancer/balancer-v2-monorepo/blob/master"
    GITHUB_DEPLOYMENTS_RAW = "https://raw.githubusercontent.com/balancer/balancer-deployments/master"
    GITHUB_DEPLOYMENTS_NICE = "https://github.com/balancer/balancer-deployments/blob/master"
    GITHUB_RAW_OUTPUTS = "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/outputs"
    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
    CHAIN_IDS_BY_NAME = chains["CHAIN_IDS_BY_NAME"]
    SCANNERS_BY_CHAIN = chains["SCANNERS_BY_CHAIN"]

    fullbook = requests.get(f"{GITHUB_RAW_OUTPUTS}/addressbook.json").json()

    fx_description_by_name = requests.get("https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/func_desc_by_name.json").json

    ### Errors
    class MultipleMatchesError(Exception):
        pass

    class NoResultError(Exception):
        pass

    def __init__(self, chain, jsonfile=False):
        self.jsonfile=jsonfile
        self.chain = chain
        self.dotmap = self.build_dotmap()
        deployments = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/deployments.json").json()
        try:
            dold =  deployments["old"][chain]
        except:
            dold = {}
        try:
            dactive = deployments["active"][chain]
        except:
            dactive = {}
        self.deployments_only = DotMap(dactive | dold)
        try:
            self.flatbook = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/{chain}.json").json()
            self.reversebook = DotMap(requests.get(f"{self.GITHUB_RAW_OUTPUTS}/{chain}_reverse.json").json())
        except:
            self.flatbook = {"zero/zero": self.ZERO_ADDRESS }
            self.reversebook = {self.ZERO_ADDRESS: "zero/zero"}


    def search_unique(self, substr):
        results = [s for s in self.flatbook.keys() if substr in s]
        if len(results) > 1:
            raise self.MultipleMatchesError(f"{substr} Multiple matches found: {results}")
        if len(results) < 1:
            raise self.NoResultError(f"{substr}")
        return results[0]

    def search_unique_deployment(self, substr):
        results = [s for s in self.deployments_only.keys() if substr in s]
        if len(results) > 1:
            raise self.MultipleMatchesError(f"{substr} Multiple matches found: {results}")
        if len(results) < 1:
            raise self.NoResultError(f"{substr}")
        return results[0]

    def search_many_deployments(self, substr):
        search = [s for s in self.deployments_only.keys() if substr in s]
        results = {key: self.deployments_only[key] for key in search if key in self.flatbook}
        return results

    def search_many(self, substr):
        search = [s for s in self.flatbook.keys() if substr in s]
        results = {key: self.flatbook[key] for key in search if key in self.flatbook}
        return results

    def latest_contract(self, contract_name):
        deployments = []
        for deployment, contractData in self.deployments_only.items():
            if contract_name in contractData.keys():
                deployments.append(deployment)
        if len(deployments) == 0:
            raise self.NoResultError(contract_name)
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