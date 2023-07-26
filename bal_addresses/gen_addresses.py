import os
from addresses import AddrBook
import requests
import json

def reverse_dict(d):
    d = dict(d)
    inv_map = {v: k for k, v in d.items()}
    return inv_map

def write_addressbooks(chainlist=AddrBook.chain_ids_by_name.keys()):
    for chain in chainlist:
        print(f"Writing addressbooks for {chain}")
        flatbook = AddrBook(chain, jsonfile="outputs/addressbook.json").generate_flatbook()
        with open(f"outputs/{chain}.json", "w") as f:
            json.dump(flatbook, f, indent=3)
        with open(f"outputs/{chain}_reverse.json", "w") as f:
            json.dump(reverse_dict(flatbook), f, indent=3)

def main():
    chains = AddrBook.chain_ids_by_name.keys()
    print(f"Generating new addressbook jsons for {chains}")
    write_addressbooks(chains)

if __name__ == "__main__":
    main()
