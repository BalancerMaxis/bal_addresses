import json

from bal_addresses.utils import build_core_pools


if __name__ == "__main__":
    # build core pools and dump result to json
    json.dump(build_core_pools(), open("outputs/core_pools.json", "w"), indent=2)
