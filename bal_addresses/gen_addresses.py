import os
from addresses import write_addressbooks, CHAIN_IDS_BY_NAME


def main():
    chains = CHAIN_IDS_BY_NAME.keys()
    print(f"Generating new addressbook jsons for {chains}")
    write_addressbooks(chains)

if __name__ == "__main__":
    main()
