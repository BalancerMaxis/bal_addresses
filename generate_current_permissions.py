import requests
import json
import os
from bal_addresses import AddrBook, GITHUB_DEPLOYMENTS_RAW
from web3 import Web3

INFURA_KEY = os.getenv("INFURA_KEY")
ALCHEMY_KEY = os.getenv("ALCHEMY_KEY")

w3_by_chain = {
    "base": Web3(
        Web3.HTTPProvider(f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}")
    ),
    "gnosis": Web3(Web3.HTTPProvider(f"https://rpc.gnosischain.com")),
    "zkevm": Web3(Web3.HTTPProvider(f"https://zkevm-rpc.com")),
    "avalanche": Web3(Web3.HTTPProvider(f"https://api.avax.network/ext/bc/C/rpc")),
    "fantom": Web3(Web3.HTTPProvider("https://rpc.fantom.network")),
    ### Less reliable RPCs first to fail fast :)
    "mainnet": Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_KEY}")),
    "arbitrum": Web3(
        Web3.HTTPProvider(f"https://arbitrum-mainnet.infura.io/v3/{INFURA_KEY}")
    ),
    "optimism": Web3(
        Web3.HTTPProvider(f"https://optimism-mainnet.infura.io/v3/{INFURA_KEY}")
    ),
    "polygon": Web3(
        Web3.HTTPProvider(f"https://polygon-mainnet.infura.io/v3/{INFURA_KEY}")
    ),
    "sepolia": Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{INFURA_KEY}")),
}


def build_chain_permissions_list(chain_name):
    a = AddrBook(chain_name)
    results = {}
    action_ids_list = (
        f"{GITHUB_DEPLOYMENTS_RAW}/action-ids/{chain_name}/action-ids.json"
    )
    w3 = w3_by_chain[chain_name]
    authorizer = w3.eth.contract(
        address=a.search_unique("20210418-authorizer/Authorizer").address,
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
    for chain in w3_by_chain:
        print(f"\n\n\nGenerating Permissions Data for {chain.capitalize()}\n\n\n")
        generate_chain_files(chain)


if __name__ == "__main__":
    main()
