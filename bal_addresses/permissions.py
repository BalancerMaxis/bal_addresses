
import json
from web3 import Web3
import requests
from dotmap import DotMap
from bal_addresses import AddrBook
from collections import defaultdict

### Errors
class MultipleMatchesError(Exception):
    pass


class NoResultError(Exception):
    pass


### Main class
class BalPermissions:
    GITHUB_DEPLOYMENTS_RAW = "https://raw.githubusercontent.com/balancer/balancer-deployments/master"
    ## TODO switch back to main branch
    #GITHUB_RAW_OUTPUTS = "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/outputs"
    GITHUB_RAW_OUTPUTS = "https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/generate_permissions_jsons/outputs"


    ### Errors
    class MultipleMatchesError(Exception):
        pass

    class NoResultError(Exception):
        pass

    def __init__(self, chain):
        self.chain = chain
        self.ACTIVE_PERMISSIONS_BY_ACTION_ID = requests.get(f"{self.GITHUB_RAW_OUTPUTS}/permissions/active/{chain}.json").json()
        self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT = requests.get(f"{self.GITHUB_DEPLOYMENTS_RAW}/action-ids/{chain}/action-ids.json").json()

        # Define
        self.paths_by_action_id = defaultdict(set)
        self.deployments_by_fx = defaultdict(set)
        self.contracts_by_fx = defaultdict(set)
        self.contracts_by_deployment = defaultdict(set)
        self.action_id_by_fx = {}
        self.action_id_by_path = {}
        # Populate
        for deployment, contracts in self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT.items():
            for contract, contract_data in contracts.items():
                for fx, action_id in contract_data["actionIds"].items():
                    path = f"{deployment}/{contract}/{fx}"
                    assert path not in self.action_id_by_path.values(), f"{path} shows up twice?"
                    self.action_id_by_path[path] = action_id
                    self.action_id_by_fx[fx] = action_id
                    self.deployments_by_fx[fx].add(deployment)
                    self.contracts_by_fx[fx].add(contract)
                    self.contracts_by_deployment[deployment].add(contract)
                    self.paths_by_action_id[action_id].add(path)


    def search_fx(self, substr):
        search = [s for s in self.action_id_by_fx.keys() if substr in s]
        results = [fx for fx in search if fx in self.action_id_by_fx]
        return results

    def search_path(self, substr):
        search = [s for s in self.action_id_by_path.keys() if substr in s]
        results = [path for path in search if path in self.action_id_by_path]
        return results

    def search_many_paths_by_unique_deployment(self, deployment_substr, fx_substr):
        a = AddrBook(self.chain)
        results = []
        deployment = a.search_unique_deployment(deployment_substr)
        deployment_fxs = self.search_path(deployment)
        search = [s for s in deployment_fxs if fx_substr in s]
        for r in search:
            result = DotMap({
                "path": r,
                "action_id": self.action_id_by_path[r]
            })
            results.append(result)
        return results

    def search_unique_path_by_unique_deployment(self, deployment_substr, fx_substr):
        results = self.search_many_paths_by_unique_deployment(deployment_substr, fx_substr)
        if len(results) > 1:
            raise self.MultipleMatchesError(f"{fx_substr} Multiple matches found: {results}")
        if len(results) < 1:
            raise self.NoResultError(f"{fx_substr}")
        return results[0]

    def needs_authorizer(self, contract, deployment):
        return self.ACTION_IDS_BY_CONTRACT_BY_DEPLOYMENT[deployment][contract]["useAdaptor"]

    def allowed_addesses(self, action_id):
        try:
            return self.ACTIVE_PERMISSIONS_BY_ACTION_ID[action_id]
        except KeyError:
            raise self.NoResultError(f"{action_id} has no authorized callers")

    def allowed_caller_names(self, action_id):
        a = AddrBook(self.chain)
        try:
            addresslist = self.ACTIVE_PERMISSIONS_BY_ACTION_ID[action_id]
        except KeyError:
            raise self.NoResultError(f"{action_id} has no authorized callers")
        names = [a.flatbook.get(item, 'undef') for item in addresslist]
        return names



