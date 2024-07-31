import requests
import json
import os
from bal_addresses import AddrBook, GITHUB_DEPLOYMENTS_RAW, NoResultError
from web3 import Web3
from bal_tools import Web3Rpc

DRPC_KEY = os.getenv("DRPC_KEY")


def build_chain_permissions_list(chain_name):
    a = AddrBook(chain_name)
    results = {}
    action_ids_list = (
        f"{GITHUB_DEPLOYMENTS_RAW}/action-ids/{chain_name}/action-ids.json"
    )
    w3 = Web3Rpc(chain_name, DRPC_KEY)

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
    for chain in AddrBook.chains.BALANCER_PRODUCTION_CHAINS:
        print(f"\n\n\nGenerating Permissions Data for {chain.capitalize()}\n\n\n")
        generate_chain_files(chain)


if __name__ == "__main__":
    main()
