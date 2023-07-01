
import json
from web3 import Web3
import requests
from dotmap import DotMap
from bal_addresses import AddrBook

## Expose some config for bootstrapping, maybe there is a better way to do this without so many github hits but allowing this to be used before invoking the class.
chains = requests.get(f"https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json").json()
CHAIN_IDS_BY_NAME = chains["CHAIN_IDS_BY_NAME"]
SCANNERS_BY_CHAIN = chains["SCANNERS_BY_CHAIN"]


### Errors
class MultipleMatchesError(Exception):
    pass


class NoResultError(Exception):
    pass


### Main class
class BalPermissions:
    chains = DotMap(requests.get(
        f"https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json").json())
    GITHUB_DEPLOYMENTS_RAW = "https://raw.githubusercontent.com/balancer/balancer-deployments/master"
    GITHUB_DEPLOYMENTS_NICE = "https://github.com/balancer/balancer-deployments/blob/master"
    ## TODO switch back to main branch
    #GITHUB_RAW_OUTPUTS = "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/outputs"
    GITHUB_RAW_OUTPUTS = "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/generate_permissions_jsons/outputs"
    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
    CHAIN_IDS_BY_NAME = chains["CHAIN_IDS_BY_NAME"]
    SCANNERS_BY_CHAIN = chains["SCANNERS_BY_CHAIN"]

    fx_description_by_name = requests.get("https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/func_desc_by_name.json").json

    ### Errors
    class MultipleMatchesError(Exception):
        pass

    class NoResultError(Exception):
        pass

    def __init__(self, chain):
        self.chain = chain
        self.ACTIVE_PERMISSIONS_BY_ACTION_ID = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/permissions/active/{chain}.json").json()
        self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT = requests.get(f"{self.GITHUB_DEPLOYMENTS_RAW}/action-ids/{chain}/action-ids.json").json()
        self.fx_path_by_role = {}
        self.role_by_fx_path = {}
        for deployment, contracts in self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT.items():
            for contract, contract_data in contracts.items():
                for fx, role in contract_data["actionIds"].items():
                    fx_path = f"{deployment}/{contract}/{fx}"
                    self.fx_path_by_role[role] = fx_path
                    assert fx_path not in self.role_by_fx_path.values(), f"{fx_path} shows up twice?"
                    self.role_by_fx_path[fx_path] = role

    def search_fx(self, substr):
        search = [s for s in self.role_by_fx_path.keys() if substr in s]
        results = {key: self.role_by_fx_path[key] for key in search if key in self.role_by_fx_path}
        return results

    def search_many_fxs_by_unique_deployment(self, deployment_substr, fx_substr):
        a = AddrBook(self.chain)
        results = []
        deployment = a.search_unique_deployment(deployment_substr)
        deployment_fxs = self.search_fx(deployment).keys()
        search = [s for s in deployment_fxs if fx_substr in s]
        for r in search:
            result = DotMap({
                "fx_path": r,
                "action_id": self.role_by_fx_path[r]
            })
            results.append(result)
        return results

    def search_unique_fx_by_unique_deployment(self, deployment_substr, fx_substr):
        results = self.search_many_fxs_by_unique_deployment(deployment_substr, fx_substr)
        if len(results) > 1:
            raise self.MultipleMatchesError(f"{fx_substr} Multiple matches found: {results}")
        if len(results) < 1:
            raise self.NoResultError(f"{fx_substr}")
        return results[0]

    def needs_authorizer(self, contract, deployment):
        return self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT[deployment][contract]["useAdaptor"]

    def allowed_addesses(self, action_id):
        try:
            return self.ACTIVE_PERMISSIONS_BY_ACTION_ID[action_id]["Authorized_Caller_Addresses"]
        except KeyError:
            raise self.NoResultError(f"{action_id} has no authorized callers")

    def allowed_caller_names(self, action_id):
        try:
            return self.ACTIVE_PERMISSIONS_BY_ACTION_ID[action_id]["Authorized_Caller_Names"]
        except KeyError:
            raise self.NoResultError(f"{action_id} has no authorized callers")


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