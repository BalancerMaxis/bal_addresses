import requests
import json
import pandas as pd
import os
from addresses import AddrBook
from web3 import Web3
import datetime

INFURA_KEY = os.getenv('WEB3_INFURA_PROJECT_ID')

w3_by_chain = {
    "mainnet": Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_KEY}")),
    "arbitrum": Web3(Web3.HTTPProvider(f"https://arbitrum-mainnet.infura.io/v3/{INFURA_KEY}")),
    "optimism": Web3(Web3.HTTPProvider(f"https://optimism-mainnet.infura.io/v3/{INFURA_KEY}")),
    "polygon": Web3(Web3.HTTPProvider(f"https://polygon-mainnet.infura.io/v3/{INFURA_KEY}")),
    "gnosis": Web3(Web3.HTTPProvider(f"https://rpc.gnosischain.com/")),
    "goerli": Web3(Web3.HTTPProvider(f"https://goerli.infura.io/v3/{INFURA_KEY}")),
    "sepolia": Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{INFURA_KEY}")),
    "zkevm": Web3(Web3.HTTPProvider(f"https://zkevm-rpc.com")),
    "avalanche": Web3(Web3.HTTPProvider(f"https://api.avax.network/ext/bc/C/rpc")),
}

def build_chain_permissions_list(chain_name):
    a = AddrBook(chain_name)
    r = a.flatbook
    results = {}
    address_names = a.reversebook
    action_ids_list = f"{a.GITHUB_DEPLOYMENTS_RAW}/action-ids/{chain_name}/action-ids.json"
    w3 = w3_by_chain[chain_name]
    authorizer = w3.eth.contract(address=r["20210418-authorizer/Authorizer"], abi=json.load(open("bal_addresses/abis/Authorizer.json")))
    try:
        result = requests.get(action_ids_list)
    except requests.exceptions.HTTPError as err:
        print(f"URL: {requests.request.url} returned error {err}")
    input = result.json()
    for deployment, contracts in input.items():
        print(f"Processing {deployment}")
        for contract, data in contracts.items():
            for fx, action_id in data["actionIds"].items():
                numMembers = authorizer.functions.getRoleMemberCount(action_id).call()
                if numMembers > 0:
                    memberAddressList = []
                    memberNameList = []
                    for i in range(0, numMembers, 1):
                        caller = (str(authorizer.functions.getRoleMember(action_id, i).call()))
                        memberAddressList.append(caller)
                        if isinstance(address_names[caller], str):
                            memberNameList.append(address_names[caller])
                        else:
                            memberNameList.append("undef")

                    d = {
                        "Fx": fx,
                        "Contract": contract,
                        "Deployment": deployment,
                        "Authorized_Caller_Addresses": memberAddressList,
                        "Authorized_Caller_Names": memberNameList,
                    }
                    assert action_id not in results.items(), \
                        f"actionId {action_id} already found {results[action_id][deployment]}/{results[action_id][contract]}/{results[action_id][fx]}"
                    results[action_id] = d
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
