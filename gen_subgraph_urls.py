import json

import requests

from bal_addresses.subgraph import Subgraph


def main():
    urls = {}

    with open("extras/chains.json", "r") as f:
        chains = json.load(f)
    for chain in chains["CHAIN_IDS_BY_NAME"]:
        if chain not in urls:
            urls[chain] = {}
        for subgraph_type in ["core", "gauges", "blocks", "aura"]:
            subgraph = Subgraph(chain)
            url = subgraph.get_subgraph_url(subgraph_type)
            if url:
                code = requests.get(url).status_code
                if code == 200:
                    urls[chain].update({subgraph_type: url})
                else:
                    # if code not in urls[chain]:
                    #     urls[chain][code] = {}
                    urls[chain].update({subgraph_type: {code: url}})
            else:
                continue

    # dump the collected dict to json file
    with open("outputs/subgraph_urls.json", "w") as f:
        json.dump(urls, f, indent=2)


if __name__ == "__main__":
    main()
