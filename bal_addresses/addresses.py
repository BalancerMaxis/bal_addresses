import json
from .errors import MultipleMatchesError, NoResultError
from typing import Dict
from typing import Optional

import requests
from munch import Munch
from web3 import Web3

GITHUB_MONOREPO_RAW = (
    "https://raw.githubusercontent.com/balancer-labs/balancer-v2-monorepo/master"
)
GITHUB_MONOREPO_NICE = "https://github.com/balancer/balancer-v2-monorepo/blob/master"
GITHUB_DEPLOYMENTS_RAW = (
    "https://raw.githubusercontent.com/balancer/balancer-deployments/master"
)
GITHUB_DEPLOYMENTS_NICE = "https://github.com/balancer/balancer-deployments/blob/master"
GITHUB_RAW_OUTPUTS = (
    "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/outputs"
)
GITHUB_RAW_EXTRAS = (
    "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras"
)
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class AddrBook:
    chains = Munch.fromDict(
        requests.get(
            "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json"
        ).json()
    )
    fx_description_by_name = Munch.fromDict(
        requests.get(
            "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/func_desc_by_name.json"
        ).json()
    )
    chain_ids_by_name = chains.CHAIN_IDS_BY_NAME

    def __init__(self, chain, jsonfile=False):
        self.jsonfile = jsonfile
        self.chain = chain
        deployments = requests.get(f"{GITHUB_RAW_OUTPUTS}/deployments.json").json()
        try:
            dold = deployments["old"][chain]
        except Exception:
            dold = {}
        try:
            dactive = deployments["active"][chain]
        except Exception:
            dactive = {}
        self.deployments_only = Munch.fromDict(dactive | dold)
        try:
            self.flatbook = self.generate_flatbook()
            self.reversebook = {value: key for key, value in self.flatbook.items()}
        except:
            self.flatbook = {}
            self.reversebook = {}
        self._deployments = None
        self._extras = None
        self._multisigs = None
        self._eoas = None
        self._pools = None
        self._gauges = None
        self._root_gauges = None

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

    @property
    def extras(self) -> Optional[Munch]:
        """
        Get the extras for all chains in a form of a Munch object
        """
        if self._extras is not None:
            return self._extras
        else:
            self.populate_extras()
        return self._extras

    @property
    def EOAs(self) -> Optional[Munch]:
        """
        Get the extras for all chains in a form of a Munch object
        """
        if self._eoas is not None:
            return self._eoas
        else:
            self.populate_eoas()
        return self._eoas

    @property
    def multisigs(self) -> Optional[Munch]:
        """
        Get the multisigs for all chains in a form of a Munch object
        """
        if self._multisigs is not None:
            return self._multisigs
        else:
            self.populate_multisigs()
        return self._multisigs

    @property
    def pools(self) -> Optional[Munch]:
        """
        Get the pools for all chains in a form of a Munch object
        """
        if self._pools is not None:
            return self._pools
        else:
            self.populate_pools()
        return self._pools

    @property
    def gauges(self) -> Optional[Munch]:
        """
        Get the gauges for all chains in a form of a Munch object
        """
        if self._gauges is not None:
            return self._gauges
        else:
            self.populate_gauges()
        return self._gauges

    @property
    def root_gauges(self) -> Optional[Munch]:
        """
        Get the root gauges for all chains in a form of a Munch object
        """
        if self._root_gauges is not None:
            return self._root_gauges
        else:
            self.populate_root_gauges()
        return self._root_gauges

    def populate_deployments(self) -> None:
        chain_deployments = requests.get(
            f"{GITHUB_DEPLOYMENTS_RAW}/addresses/{self.chain}.json"
        )
        if chain_deployments.ok:
            # Remove date from key
            processed_deployment = self._process_deployment(chain_deployments.json())
            self._deployments = Munch.fromDict(processed_deployment)
        else:
            print(f"Warning: No deploys for chain {self.chain}")
            return Munch.fromDict({})

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
            if isinstance(v.get("contracts"), list):
                contracts = {
                    contract["name"]: {
                        **contract,
                        "deployment": k,
                        "path": f"{k}/{contract['name']}",
                    }
                    for contract in v["contracts"]
                }
                contracts_by_contract = {
                    contract: data for contract, data in contracts.items()
                }
                v["contracts"] = contracts_by_contract
            processed_deployment[deployment_identifier] = v
        return processed_deployment

    def populate_extras(self) -> None:
        chain_extras = requests.get(f"{GITHUB_RAW_EXTRAS}/{self.chain}.json")
        if chain_extras.ok:
            self._extras = Munch.fromDict(
                self.checksum_address_dict(chain_extras.json())
            )
        else:
            print(
                f"Warning: No extras for chain {self.chain}, extras must be added in extras/chain.json"
            )
            self._extras = Munch.fromDict({})

    def populate_eoas(self) -> None:
        eoas = requests.get(f"{GITHUB_RAW_EXTRAS}/signers.json")
        if eoas.ok:
            self._eoas = Munch.fromDict(self.checksum_address_dict(eoas.json()))

    def populate_multisigs(self) -> None:
        msigs = requests.get(f"{GITHUB_RAW_EXTRAS}/multisigs.json").json()
        if msigs.get(self.chain):
            self._multisigs = Munch.fromDict(
                self.checksum_address_dict(msigs[self.chain])
            )
        else:
            print(
                f"Warning: No multisigs for chain {self.chain}, multisigs must be added in extras/multisig.json"
            )
            self._multisigs = Munch.fromDict({})

    def populate_pools(self) -> None:
        with open("extras/pools.json", "r") as f:
            pools = json.load(f)
        if pools.get(self.chain):
            self._pools = Munch.fromDict(self.checksum_address_dict(pools[self.chain]))
        else:
            print(f"Warning: No pools for chain {self.chain}")
            self._pools = Munch.fromDict({})

    def populate_gauges(self) -> None:
        with open("extras/gauges.json", "r") as f:
            gauges = json.load(f)
        if gauges.get(self.chain):
            self._gauges = Munch.fromDict(
                self.checksum_address_dict(gauges[self.chain])
            )
        else:
            print(f"Warning: No gauges for chain {self.chain}")
            self._gauges = Munch.fromDict({})

    def populate_root_gauges(self) -> None:
        with open("extras/root_gauges.json", "r") as f:
            root_gauges = json.load(f)
        if root_gauges.get(self.chain):
            self._root_gauges = Munch.fromDict(
                self.checksum_address_dict(root_gauges[self.chain])
            )
        else:
            print(f"Warning: No root gauges for chain {self.chain}")
            self._root_gauges = Munch.fromDict({})

    def search_unique(self, substr):
        results = [s for s in self.flatbook.keys() if substr in s]
        if len(results) > 1:
            raise MultipleMatchesError(f"{substr} Multiple matches found: {results}")
        if len(results) < 1:
            raise NoResultError(f"{substr}")
        return Munch.fromDict(
            {"path": results[0], "address": self.flatbook[results[0]]}
        )

    def search_unique_deployment(self, substr):
        results = [s for s in self.deployments_only.keys() if substr in s]
        if len(results) > 1:
            raise MultipleMatchesError(f"{substr} Multiple matches found: {results}")
        if len(results) < 1:
            raise NoResultError(f"{substr}")
        return Munch.fromDict(
            {
                "deployment": results[0],
                "addresses_by_contract": self.deployments_only[results[0]],
            }
        )

    def search_many_deployments(self, substr):
        search = [s for s in self.deployments_only.keys() if substr in s]
        return search

    def search_many(self, substr):
        output = []
        results = {
            path: address for path, address in self.flatbook.items() if substr in path
        }
        outputs = [
            Munch.fromDict({"path": path, "address": address})
            for path, address in results.items()
        ]
        return outputs

    def latest_contract(self, contract_name):
        deployments = []
        for deployment, contractData in self.deployments_only.items():
            if contract_name in contractData.keys():
                deployments.append(deployment)
        if len(deployments) == 0:
            raise NoResultError(contract_name)
        deployments.sort(reverse=True)
        address = self.deployments_only[deployments[0]][contract_name]
        return Munch.fromDict({"path": self.reversebook[address], "address": address})

    @staticmethod
    def checksum_address_dict(addresses):
        """
        convert addresses to their checksum variant taken from a (nested) dict
        """
        checksummed = {}
        for k, v in addresses.items():
            if isinstance(v, dict):
                checksummed[k] = checksum_address_dict(v)
            elif isinstance(v, str):
                try:
                    checksummed[k] = Web3.toChecksumAddress(v)
                except:
                    checksummed[k] = v
            else:
                print(k, v, "formatted incorrectly")
                checksummed[k] = v
        return checksummed

    def flatten_dict(self, d, parent_key="", sep="/"):
        items = []
        d = dict(d)
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def generate_flatbook(self):
        flatbook = {}
        self.populate_eoas()
        self.populate_deployments()
        self.populate_multisigs()
        self.populate_pools()
        self.populate_gauges()
        self.populate_root_gauges()
        self.populate_extras()
        # write pools and gauges first, so they get overwritten by deployments later
        # deployment label should take precedence over pool/gauge label
        flatbook["pools"] = self.flatten_dict(self.pools)
        flatbook["gauges"] = self.flatten_dict(self.gauges)
        flatbook["root_gauges"] = self.flatten_dict(self.root_gauges)
        for deployment, ddata in self.deployments.items():
            for contract, infodict in ddata["contracts"].items():
                flatbook[infodict.path] = infodict.address
        flatbook = {**flatbook, **self.flatten_dict(self.extras)}
        flatbook["multisigs"] = self.flatten_dict(self.multisigs)
        flatbook["EOA"] = self.flatten_dict(self.EOAs)
        return self.flatten_dict(flatbook)


# Version outside class to allow for recursion on the uninitialized class
def checksum_address_dict(addresses):
    """
    convert addresses to their checksum variant taken from a (nested) dict
    """
    checksummed = {}
    for k, v in addresses.items():
        if isinstance(v, dict):
            checksummed[k] = checksum_address_dict(v)
        elif isinstance(v, str):
            try:
                checksummed[k] = Web3.toChecksumAddress(v)
            except:
                checksummed[k] = v
        else:
            print(k, v, "formatted incorrectly")
            checksummed[k] = v
    return checksummed
