import os
from addresses import write_addressbooks, CHAIN_IDS_BY_NAME


def main():
    chains = CHAIN_IDS_BY_NAME.keys()
    write_addressbooks(chains)

if __name__ == "__main__":
    main()
