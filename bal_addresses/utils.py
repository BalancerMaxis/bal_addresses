from urllib.request import urlopen

def get_subgraph_url(chain: str, subgraph="core") -> str:
    """
    perform some soup magic to determine the latest subgraph url used in the official frontend

    params:
    - chain: name of the chain
    - subgraph: "core" or "gauges"

    returns:
    - https url of the subgraph
    """
    chain = "gnosis-chain" if chain == "gnosis" else chain
    frontend_file = f"https://raw.githubusercontent.com/balancer/frontend-v2/develop/src/lib/config/{chain}/index.ts"
    if subgraph == "core":
        magic_word = "subgraph:"
    elif subgraph == "gauges":
        magic_word = "gauge:"
    found_magic_word = False
    with urlopen(frontend_file) as f:
        for line in f:
            if found_magic_word:
                return line.decode("utf-8").strip().strip(" ,'")
            if magic_word + " " in str(line):
                # url is on same line
                return line.decode("utf-8").split(magic_word)[1].strip().strip(",'")
            if magic_word in str(line):
                # url is on next line, return it on the next iteration
                found_magic_word = True
