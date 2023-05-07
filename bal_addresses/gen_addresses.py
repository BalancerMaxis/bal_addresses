import os
from addresses import AddrBook
from dotmap import DotMap
import requests
import json



def reverse_dict(dict):
    inv_map = {v: k for k, v in dict.items()}
    return DotMap(inv_map)

def write_addressbooks(chainlist=AddrBook.CHAIN_IDS_BY_NAME.keys()):
    for chain in chainlist:
        print(f"Writing addressbooks for {chain}")
        flatbook = AddrBook(chain).generate_flatbook()
        with open(f"outputs/{chain}.json", "w") as f:
            json.dump(flatbook, f, indent=3)
        with open(f"outputs/{chain}_reverse.json", "w") as f:
            json.dump(reverse_dict(flatbook), f, indent=3)

def main():
    chains = AddrBook.CHAIN_IDS_BY_NAME.keys()
    print(f"Generating new addressbook jsons for {chains}")
    write_addressbooks(chains)

if __name__ == "__main__":
    main()
