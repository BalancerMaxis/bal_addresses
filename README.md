# Monorepo Addresses

This repo is setup to make it easy to find up to date addresses at balancer.

## Outputs - structured data
The [outputs](./outputs) directory has a number of different address books that you can use in code or with your eyeballs.

### [chain].json Files 
Have keys of deployment/contract as well as some other extra stuff all with / notation.  It includes multisigs and signers known to the maxis as well as other addresses we have touched sorted by protocol.

### addressbook.json
Has all the addresses sorted into 2 dicts (active, and old).  Each dict is then mapped like `{chain:{deployment:{contract: address}}}`


## Python helpers
You can import this into python scripts by adding the following into your requirements.txt `git+https://github.com/BalancerMaxis/bal_addresses`.

once imported like `from bal_addresses import *`  you can use the following functions`["read_addressbook", "write_addressbooks", "addressbook_by_chain", "read_reversebook", "address_lookup_dict", "checksum_address_dict"]`

`read_addressbooks(chain)` will give you a dict of all the / notated names and their addresses.
`read_reversebook(chain)` will give you the same but with addresses as keys and the / name as value.

Most of the other functions are used by a github action which regenerates files read in by those 2 functions on a weekly basis.  You can explore them if you would like.

