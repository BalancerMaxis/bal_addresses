#### Note this script has to run from the monorepo. It's just here until we figure out how to create a source of truth
#### that doesn't need this file and/or something like it is provided in the monorepo

### It generates addressbook.json

import os
import re
import json
import urllib.request
from pathlib import Path

import pandas as pd
import requests

from bal_addresses import AddrBook


deployments = os.environ["DEPLOYMENTS_REPO_ROOT_URL"]
basepath = deployments


def main():
    # Get deployments
    active_deployments = []
    old_deployments = []
    ls = os.listdir(f"{basepath}/tasks")
    for path in ls:
        if bool(re.search(r"^\d{8}", path)):
            active_deployments.append(path)

    ls = os.listdir(f"{basepath}/tasks/deprecated")
    for path in ls:
        if bool(re.search(r"^\d{8}", path)):
            old_deployments.append(path)

    active = process_deployments(active_deployments, False)
    old = process_deployments(old_deployments, True)

    results = {"active": active, "old": old}
    with open("outputs/deployments.json", "w") as f:
        json.dump(results, f, indent=3)
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
        ### add extras
        try:
            with open(f"extras/{chain}.json") as f:
                data = json.load(f)
                data = AddrBook.checksum_address_dict(data)
        except:
            data = {}
        ### add gauges
        print(chain)
        if chain in ["bsc", "kovan", "fantom", "rinkeby"]:
            # no (gauge) subgraph exists for this chain
            continue
        active[chain]["gauges"] = process_query_preferential_gauges(
            query_preferential_gauges(chain)
        )

        active[chain] = data | active[chain]
    results = {"active": active, "old": old}
    with open("outputs/addressbook.json", "w") as f:
        json.dump(results, f, indent=3)


def process_deployments(deployments, old=False):
    result = {}
    for task in deployments:
        if old:
            path = Path(f"{basepath}/tasks/deprecated/{task}/output")
        else:
            path = Path(f"{basepath}/tasks/{task}/output")
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


def get_gauges_subgraph_url(chain_name):
    chain_name = "gnosis-chain" if chain_name == "gnosis" else chain_name
    frontend_file = f"https://raw.githubusercontent.com/balancer/frontend-v2/develop/src/lib/config/{chain_name}/index.ts"
    with urllib.request.urlopen(frontend_file) as f:
        found_gauge_line = False
        for line in f:
            if found_gauge_line:
                return line.decode("utf-8").strip().strip(",").strip("'")
            if "gauge:" in str(line):
                found_gauge_line = True


def query_preferential_gauges(chain_name, skip=0, step_size=100) -> list:
    url = get_gauges_subgraph_url(chain_name)
    query = f"""{{
        liquidityGauges(
            skip: {skip}
            first: {step_size}
            where: {{isPreferentialGauge: true}}
        ) {{
            id
            symbol
        }}
    }}"""
    r = requests.post(url, json={"query": query})
    r.raise_for_status()
    try:
        result = r.json()["data"]["liquidityGauges"]
    except KeyError:
        result = []
    if len(result) > 0:
        # didnt reach end of results yet, collect next page
        result += query_preferential_gauges(chain_name, skip + step_size, step_size)
    return result


def process_query_preferential_gauges(result) -> dict:
    df = pd.DataFrame(result)
    if len(df) == 0:
        return
    assert len(df["id"].unique()) == len(df)
    if len(df["symbol"].unique()) != len(df):
        # TODO
        print("found duplicate symbols!")
        print(df[df["symbol"].duplicated(keep=False)].sort_values("symbol"))
    return df.set_index("symbol")["id"].to_dict()


if __name__ == "__main__":
    main()
