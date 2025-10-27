#!/usr/bin/env python3
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from bal_tools import Web3RpcByChain


EZKL_MULTISIG = "0x522Eb7a9b94fC016e98e35E8562C79DDDA8Aefc0"

FEE_HELPERS = {
    "mainnet": {
        "v2": "0x8A8B9f35765899B3a0291700141470D79EA2eA88",
        "v3": "0xc00fF743B73346c9a4C40509e0550FfC18e5426d",
    },
    "base": {
        "v2": "0xd22eecBB495380Ef52b1CCeF1cA594979885D484",
        "v3": "0xFc00536A0fd292c284deeF6af8F644d8373d9cad",
    }
}


def fetch_ezkl_pools():
    """Fetch all pools controlled by EZKL multisig across chains and versions."""
    w3_by_chain = Web3RpcByChain(os.getenv("DRPC_KEY"))
    abi_dir = Path(__file__).parent / "bal_addresses" / "abis"

    ezkl_pools_by_chain = {}

    for chain in FEE_HELPERS:
        chain_pools = []
        w3 = w3_by_chain[chain]

        for version, helper_addr in FEE_HELPERS[chain].items():
            abi_file = f"{version}_fee_helper.json"
            with open(abi_dir / abi_file) as f:
                abi = json.load(f)

            contract = w3.eth.contract(address=helper_addr, abi=abi)

            pool_set_id = contract.functions.getPoolSetIdForManager(EZKL_MULTISIG).call()

            if pool_set_id == 0:
                continue  # No pools registered

            pools = contract.functions.getAllPoolsInSet(pool_set_id).call()

            # v2 returns bytes32, v3 returns addresses
            if version == "v2":
                pools = ["0x" + p.hex() for p in pools]

            chain_pools.extend(pools)

        if chain_pools:
            ezkl_pools_by_chain[chain] = sorted(list(set(chain_pools)))

    return ezkl_pools_by_chain


def main():
    load_dotenv()
    ezkl_pools = fetch_ezkl_pools()

    with open("outputs/ezkl_pools.json", "w") as f:
        json.dump(ezkl_pools, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()