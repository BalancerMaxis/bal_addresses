import requests
import json
import os
from bal_addresses import AddrBook, GITHUB_DEPLOYMENTS_RAW, NoResultError
from web3 import Web3

INFURA_KEY = os.getenv("INFURA_KEY")
ALCHEMY_KEY = os.getenv("ALCHEMY_KEY")
DRPC_KEY = os.getenv("DRPC_KEY")


DRPC_NAME_OVERRIDES = {
    "mainnet": "ethereum",
    "zkevm": "polygon-zkevm",
}


class W3_RPC:
    def __init__(self, chain, DRPC_KEY):
        drpc_chain = DRPC_NAME_OVERRIDES.get(chain, chain)
        self.w3 = Web3(
            Web3.HTTPProvider(
                f"https://lb.drpc.org/ogrpc?network={drpc_chain}&dkey={DRPC_KEY}"
            )
        )

    def __getattr__(self, name):
        return getattr(self.w3, name)


class W3_RPC_BY_CHAIN:
    def __init__(self, DRPC_KEY):
        self.DRPC_KEY = DRPC_KEY
        self.w3_by_chain = {}
        for chain in AddrBook.chain_ids_by_name.keys():
            self.w3_by_chain[chain] = W3_RPC(chain, DRPC_KEY)

    def __getitem__(self, chain):
        return self.w3_by_chain[chain]

    def __setitem__(self, chain, value):
        self.w3_by_chain[chain] = value

    def __delitem__(self, chain):
        del self.w3_by_chain[chain]


def build_chain_permissions_list(chain_name):
    a = AddrBook(chain_name)
    results = {}
    action_ids_list = (
        f"{GITHUB_DEPLOYMENTS_RAW}/action-ids/{chain_name}/action-ids.json"
    )
    w3 = W3_RPC(chain_name, os.getenv("DRPC_KEY"))

    try:
        authorizer_address = a.search_unique("20210418-authorizer/Authorizer").address
    except NoResultError as e:
        print(f"WARNING: Authorizer not found: {e}")
        return results
    authorizer = w3.eth.contract(
        address=authorizer_address,
        abi=json.load(open("bal_addresses/abis/Authorizer.json")),
    )
    try:
        result = requests.get(action_ids_list)
    except requests.exceptions.HTTPError as err:
        print(f"URL: {requests.request.url} returned error {err}")
    input = result.json()
    for deployment, contracts in input.items():
        print(f"Processing {deployment}")
        for data in contracts.values():
            for action_id in data["actionIds"].values():
                if action_id in results:
                    continue  # already have data
                numMembers = authorizer.functions.getRoleMemberCount(action_id).call()
                if numMembers > 0:
                    memberAddressList = []
                    for i in range(0, numMembers, 1):
                        caller = str(
                            authorizer.functions.getRoleMember(action_id, i).call()
                        )
                        memberAddressList.append(caller)

                    results[action_id] = memberAddressList
    return results


def generate_chain_files(chain):
    permissions = build_chain_permissions_list(chain)
    with open(f"outputs/permissions/active/{chain}.json", "w") as f:
        json.dump(permissions, f, indent=2)


def main():
    for chain in AddrBook.chain_ids_by_name.keys():
        print(f"\n\n\nGenerating Permissions Data for {chain.capitalize()}\n\n\n")
        generate_chain_files(chain)


if __name__ == "__main__":
    main()
