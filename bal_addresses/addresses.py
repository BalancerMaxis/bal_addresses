import json
from typing import Dict
from typing import Optional

import requests
from dotmap import DotMap
from munch import Munch
from web3 import Web3

GITHUB_MONOREPO_RAW = (
    "https://raw.githubusercontent.com/balancer-labs/balancer-v2-monorepo/master"
)
GITHUB_MONOREPO_NICE = (
    "https://github.com/balancer/balancer-v2-monorepo/blob/master"
)
GITHUB_DEPLOYMENTS_RAW = (
    "https://raw.githubusercontent.com/balancer/balancer-deployments/master"
)
GITHUB_DEPLOYMENTS_NICE = "https://github.com/balancer/balancer-deployments/blob/master"
GITHUB_RAW_OUTPUTS = (
    "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/outputs"
)
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class MultipleMatchesError(Exception):
    pass


class NoResultError(Exception):
    pass


class AddrBook:

    fullbook = requests.get(f"{GITHUB_RAW_OUTPUTS}/addressbook.json").json()
    chains = requests.get(
        "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json"
    ).json()
    CHAIN_IDS_BY_NAME = chains["CHAIN_IDS_BY_NAME"]

    def __init__(self, chain, jsonfile=False):
        self.jsonfile = jsonfile
        self.chain = chain
        self.dotmap = self.build_dotmap()
        deployments = requests.get(f"{GITHUB_RAW_OUTPUTS}/deployments.json").json()
        try:
            dold = deployments["old"][chain]
        except Exception:
            dold = {}
        try:
            dactive = deployments["active"][chain]
        except Exception:
            dactive = {}
        self.deployments_only = DotMap(dactive | dold)
        try:
            self.flatbook = requests.get(f"{GITHUB_RAW_OUTPUTS}/{chain}.json").json()
            self.reversebook = DotMap(
                requests.get(f"{GITHUB_RAW_OUTPUTS}/{chain}_reverse.json").json())
        except Exception:
            self.flatbook = {"zero/zero": ZERO_ADDRESS}
            self.reversebook = {ZERO_ADDRESS: "zero/zero"}

        self._deployments = None

    @property
    def deployments(self) -> Optional[Munch]:
        """
        Get the deployments for all chains in a form of a Munch object
        """
        if self._deployments is not None:
            return self._deployments
        else:
            self.populate_deployments()

        return self._deployments

    def populate_deployments(self) -> None:
        chain_deployments = requests.get(
            f"{GITHUB_DEPLOYMENTS_RAW}/addresses/{self.chain}.json"
        )
        if chain_deployments.ok:
            self._deployments = Munch()
            # Remove date from key
            processed_deployment = self._process_deployment(chain_deployments.json())
            self._deployments = Munch.fromDict(processed_deployment)

    def _process_deployment(self, deployment: Dict) -> Dict:
        """
        Process deployment to remove date from key and replace - with _
        """
        processed_deployment = {}
        for k, v in deployment.items():
            # lstrip date in format YYYYMMDD-:
            # Change all - to underscores
            deployment_identifier = k.lstrip("0123456789-").replace("-", "_")
            # Flatten contracts list to dict with name as key
            if isinstance(v.get('contracts'), list):
                v['contracts'] = {contract['name']: contract for contract in v['contracts']}
            processed_deployment[deployment_identifier] = v
        return processed_deployment

    def search_unique(self, substr):
        results = [s for s in self.flatbook.keys() if substr in s]
        if len(results) > 1:
            raise MultipleMatchesError(f"{substr} Multiple matches found: {results}")
        if len(results) < 1:
            raise NoResultError(f"{substr}")
        return results[0]

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
            raise NoResultError(contract_name)
        deployments.sort(reverse=True)
        return self.deployments_only[deployments[0]][contract_name]

    @staticmethod
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
        return (
            DotMap(fullbook["active"].get(self.chain, {}) | fullbook["old"].get(self.chain, {})))
        # Checksum one more time for good measure

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
        ab = dict(self.dotmap)
        return self.flatten_dict(ab)


# Version outside class to allow for recursion on the uninitialized class
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
