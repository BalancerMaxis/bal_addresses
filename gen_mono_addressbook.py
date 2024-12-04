#### Note this script has to run from the monorepo. It's just here until we figure out how to create a source of truth
#### that doesn't need this file and/or something like it is provided in the monorepo

### It generates addressbook.json

import os
import re
import json
from pathlib import Path

from bal_addresses import AddrBook


deployments = os.environ["DEPLOYMENTS_REPO_ROOT_URL"]
basepath = deployments


def main():
    # Get deployments
    active_deployments = []
    old_deployments = []
    ls = sorted(os.listdir(f"{basepath}/v2/tasks") + os.listdir(f"{basepath}/v3/tasks"))
    for path in ls:
        if bool(re.search(r"^\d{8}", path)):
            active_deployments.append(path)
    print(active_deployments)
    ls = sorted(
        os.listdir(f"{basepath}/v2/deprecated")
        + os.listdir(f"{basepath}/v3/deprecated")
    )
    for path in ls:
        if bool(re.search(r"^\d{8}", path)):
            old_deployments.append(path)

    active = process_deployments(active_deployments, False)
    old = process_deployments(old_deployments, True)

    results = {"active": active, "old": old}
    with open("outputs/deployments.json", "w") as f:
        json.dump(results, f, indent=2)
    ### Add extras
    for chain in active.keys():
        with open("extras/multisigs.json", "r") as f:
            data = json.load(f)
            data = data.get(chain, {})
            data = AddrBook.checksum_address_dict(data)
        if "multisigs" not in active[chain].keys():
            active[chain]["multisigs"] = {}
        for multisig, address in data.items():
            active[chain]["multisigs"][multisig] = address
        ### add signers
        if "EOA" not in active[chain].keys():
            active[chain]["EOA"] = {}
        with open("extras/signers.json", "r") as f:
            data = json.load(f)
            data = AddrBook.checksum_address_dict(data)
            active[chain]["EOA"] = data
        ### add pools
        if "pools" not in active[chain]:
            active[chain]["pools"] = {}
        with open("outputs/pools.json", "r") as f:
            data = json.load(f)
            data = data.get(chain, {})
            data = AddrBook.checksum_address_dict(data)
            active[chain]["pools"] = data
        ### add gauges
        if "gauges" not in active[chain]:
            active[chain]["gauges"] = {}
        with open("outputs/gauges.json", "r") as f:
            data = json.load(f)
            data = data.get(chain, {})
            data = AddrBook.checksum_address_dict(data)
            active[chain]["gauges"] = data
        ### add extras
        try:
            with open(f"extras/{chain}.json") as f:
                data = json.load(f)
                data = AddrBook.checksum_address_dict(data)
        except:
            data = {}

        active[chain] = data | active[chain]
    results = {"active": active, "old": old}
    with open("outputs/addressbook.json", "w") as f:
        json.dump(results, f, indent=2)


def process_deployments(deployments, old=False):
    result = {}
    for version in ["v2", "v3"]:
        for task in deployments:
            if old:
                path = Path(f"{basepath}/{version}/deprecated/{task}/output")
            else:
                path = Path(f"{basepath}/{version}/tasks/{task}/output")
            for file in list(sorted(path.glob("*.json"))):
                chain = file.stem
                if chain not in result.keys():
                    result[chain] = {}
                if task not in result[chain].keys():
                    result[chain][task] = {}
                with open(str(file), "r") as f:
                    data = json.load(f)
                for contract, address in data.items():
                    result[chain][task][contract] = address
    return result


if __name__ == "__main__":
    main()
