
import json
from web3 import Web3
import requests
from dotmap import DotMap

## Expose some config for bootstrapping, maybe there is a better way to do this without so many github hits but allowing this to be used before invoking the class.
chains = requests.get(f"https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json").json()
CHAIN_IDS_BY_NAME = chains["CHAIN_IDS_BY_NAME"]
SCANNERS_BY_CHAIN = chains["SCANNERS_BY_CHAIN"]


### Main class
class BalPermissions:
    chains = DotMap(requests.get(
        f"https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json").json())
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

    def __init__(self, chain):
        self.chain = chain
        self.ACTIVE_PERMISSIONS_BY_ACTION_ID = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/permissions/active/{chain}.json").json()
        self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT = DotMap(requests.get(f"{self.GITHUB_DEPLOYMENTS_RAW}/action-ids/{chain}/action-ids.json").json())
        self.fx_path_by_role = {}
        self.role_by_fx_path = {}
        for deployment, contract_data in self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT.items():
            for fx, role in contract_data["actionIds"]:
                fx_path = f"{deployment}/{str(contract_data)}/{fx}"
                self.fx_path_by_role[role] = fx_path
                assert fx_path not in self.role_by_fx_path.values(), f"{fx_path} shows up twice?"
                self.role_by_fx_path[fx_path] = role

    def search_fx(self, substr):
        search = [s for s in self.role_by_fx_path.keys() if substr in s]
        results = {key: self.flatbook[key] for key in search if key in self.flatbook}
        return results

    def needs_authorizer(self, contract, deployment):
        return self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT[deployment][contract]["useAdaptor"]

    def allowed_addesses(self, action_id):
        return self.ACTIVE_PERMISSIONS_BY_ACTION_ID["Authorized_Caller_Addresses"]

    def allowed_caller_names(self, action_id):
        return self.ACTIVE_PERMISSIONS_BY_ACTION_ID["Authorized_Caller_Names"]

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