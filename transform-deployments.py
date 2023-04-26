#### Note this script has to run from the monorepo. It's just here until we figure out how to create a source of truth
#### that doesn't need this file and/or something like it is provided in the monorepo

### It generates addressbook.json

import os
import re
import json
from pathlib import Path
from pandas import DataFrame
import requests

monorepo = os.environ["MONOREPO_ROOT"]
basepath = f"{monorepo}/pkg/"


def main():
    # Get deployments
    active_deployments = []
    old_deployments = []

    ls = os.listdir(f"{basepath}/deployments/tasks")
    for path in ls:
        if bool(re.search(r'^\d{8}', path)):
            active_deployments.append(path)

    ls = os.listdir(f"{basepath}/deployments/tasks/deprecated")
    for path in ls:
        if bool(re.search(r'^\d{8}', path)):
            old_deployments.append(path)

    active = process_deployments(active_deployments, False)
    old = process_deployments(old_deployments, True)

    results = {
        "active": active,
        "old": old
    }
    print(results)
    with open("addressbook.json", "w") as f:
        json.dump(results, f, indent=3)


def process_deployments(deployments, old=False):
    result = {}
    for task in deployments:
        if old:
            path = Path(f"{basepath}/deployments/tasks/deprecated/{task}/output")
        else:
            path = Path(f"{basepath}/deployments/tasks/{task}/output")
        print(f"processing deployments/tasks/{task}/output/")

        print(list(path.glob("*.json")))
        for file in list(path.glob("*.json")):
            print(file)
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
