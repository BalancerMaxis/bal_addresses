import json
import os

import requests
from bal_tools.subgraph import Subgraph


def main():
    # make sure that if thegraph api key somehow finds its way into the env that it is wiped
    os.environ["GRAPH_API_KEY"] = ""

    urls = {}

    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["CHAIN_IDS_BY_NAME"]:
        if chain not in urls:
            urls[chain] = {}
        for subgraph_type in [
            "vault-v3",
            "pools-v3",
            "core",
            "gauges",
            "blocks",
            "aura",
        ]:
            subgraph = Subgraph(chain)
            try:
                url = subgraph.get_subgraph_url(subgraph_type)
            except:
                continue
            if url:
                print(url)
                code = requests.get(url).status_code
                if code == 200:
                    urls[chain].update({subgraph_type: url})
                else:
                    urls[chain].update({subgraph_type: {code: url}})
            else:
                continue

    # dump the collected dict to json file
    with open("outputs/subgraph_urls.json", "w") as f:
        json.dump(urls, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
