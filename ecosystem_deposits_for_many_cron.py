from bal_addresses import Ecosystem, BalGauges, Aura, GraphQueries
import csv
import os
from collections import defaultdict
from web3 import Web3
from typing import Dict
from bal_addresses.errors import  ChecksumError, NoResultError
from datetime import datetime, timezone
### Example Run for ezETH/rETH
#  export POOL_ID=0x05ff47afada98a98982113758878f9a8b9fdda0a000000000000000000000645
#  export GAUGE_ADDRESS=0xc859bf9d7b8c557bbd229565124c2c09269f3aef
#  export BLOCK=19192051
#  pip3 install -r requirements.txt
#  python3 tools/ecosystem_deposits_for_pool.py

POOLS_TO_RUN_ON = [
    {
        "name": "weETH/rETH",
        "pool_id": "0x05ff47afada98a98982113758878f9a8b9fdda0a000000000000000000000645",
        "gauge": "0xc859bf9d7b8c557bbd229565124c2c09269f3aef"
    },
    {
        "name": "ezETH/ETH",
        "pool_id": "0x596192bb6e41802428ac943d2f1476c1af25cc0e000000000000000000000659",
        "gauge": "0xa8b309a75f0d64ed632d45a003c68a30e59a1d8b"
    },
    {
        "name": "weETH/ezETH/rswETH",
        "pool_id": "0x848a5564158d84b8a8fb68ab5d004fae11619a5400000000000000000000066a",
        "gauge": "0x253ED65fff980AEE7E94a0dC57BE304426048b35",
    },
    {
        "name": "rsETH/ETHx",
        "pool_id": "0x7761b6e0daa04e70637d81f1da7d186c205c2ade00000000000000000000065d",
        "gauge": "0x0bcdb6d9b27bd62d3de605393902c7d1a2c71aab",
    }
]
def get_ecosystem_balances_w_csv(pool_id: str, gauge_address: str, block: int, name: str, chain="mainnet") -> Dict[str, int]:
    gauges = BalGauges(chain)
    aura = Aura(chain)
    gauge_address = Web3.toChecksumAddress(gauge_address)
    bpt_balances = defaultdict(float)
    gauge_balances = defaultdict(float)
    aura_balances = defaultdict(float)
    bpts_in_bal_gauge = 0
    bpts_in_aura = 0
    total_circulating_bpts = 0
    total_bpts_counted = 0

    ## Start with raw BPTS
    ecosystem_balances = defaultdict(int, gauges.get_bpt_balances(pool_id, block))
    for address, amount in ecosystem_balances.items():

        ecosystem_balances[address] = float(amount)
        bpt_balances[address] = float(amount)
        total_circulating_bpts += float(amount)

    ## Factor in Gauge Deposits
    # Subtract the gauge itself
    if gauge_address in ecosystem_balances.keys():
        bpts_in_bal_gauge = ecosystem_balances[gauge_address]
        ecosystem_balances[gauge_address] = 0
    else:
        print(
            f"WARNING: there are no BPTs from {pool_id} staked in the gauge at {gauge_address} did you cross wires, or is there no one staked?")

    # Add in Gauge Balances
    checksum = 0
    for address, amount in gauges.get_gauge_deposit_shares(gauge_address, block).items():
        gauge_balances[address] = float(amount)
        ecosystem_balances[address] += float(amount)
        checksum += amount
    if checksum != bpts_in_aura:
        print(
            f"Warning: {bpts_in_bal_gauge} BPTs were found in the deposited in a bal gauge and zeroed out, but {checksum} of 'em where counted as gauge deposits.")

    ## Factor in Aura Deposits
    # Subtract the gauge itself
    aura_staker = aura.AURA_GAUGE_STAKER_BY_CHAIN[chain]
    if aura_staker in ecosystem_balances.keys():
        bpts_in_aura = ecosystem_balances[aura_staker]
        ecosystem_balances[aura_staker] = 0
    else:
        print(
            f"WARNING: there are no BPTs from {pool_id} staked in Aura did you cross wires, or is there no one staked?")

    # Add in Aura Balances
    checksum = 0
    try:
        aura_shares_by_address = aura.get_aura_pool_shares(gauge_address, block).items()
    except NoResultError as e:
        print(e)
        aura_shares_by_address = defaultdict(int)

    for address, amount in aura_shares_by_address:
        aura_balances[address]
        ecosystem_balances[address] += amount
        checksum += amount
    if checksum != bpts_in_aura:
        print(
            f"Warning: {bpts_in_aura} BPTs were found in the aura proxy and zeroed out, but {checksum} of 'em where counted as Aura deposits.")

    ## CHeck everything
    for address, amount in ecosystem_balances.items():
        total_bpts_counted += float(amount)
    print(
        f"Found {total_circulating_bpts} of which {bpts_in_bal_gauge} where staked by an address in a bal gauge and {bpts_in_aura} where deposited on aura at block {block}")
    ## Slight tolerance for rounding
    delta = abs(total_circulating_bpts - total_bpts_counted)
    if delta > 1e-10:
        raise ChecksumError(
            f"initial bpts found {total_circulating_bpts}, final bpts counted:{total_bpts_counted} the delta is {total_circulating_bpts - total_bpts_counted}")

    ## Build CSV
    name = name.replace("/", "-") # /'s are path structure
    output_file = f"out/{name}/{block}_{pool_id}.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        writer = csv.writer(f)

        writer.writerow(["depositor_address", "bpt_in_wallet", "bpt_in_bal_gauge", "bpt_in_aura", "total_pool_tokens"])
        for depositor, amount in ecosystem_balances.items():
            writer.writerow([depositor, bpt_balances[depositor], gauge_balances[depositor], aura_balances[depositor], amount])
    print("CSV file generated successfully: ", output_file)
    return ecosystem_balances

def main():
    ## Load config from environment
    # Set BLOCK to run on a specific block
    block = os.environ.get("BLOCK")
    # Set TIMESTAMP to find the next block after a UTC timestamp if BLOCK is missing
    timestamp = os.environ.get("TIMESTAMP")
    # Set pool_id to run on only 1 of the pool's listed on the top of this file instead of all of them
    pool_id = os.environ.get("POOL_ID")
    chain = "mainnet"
    q = GraphQueries(chain)
    timestamp = None
    if not block:
        if not timestamp:
            timestamp = int(datetime.now(timezone.utc).timestamp() - 300) # Use 5 minutes ago to make sure subgraphs are up to date
        block = q.get_first_block_after_utc_timestamp(timestamp)
        print(f"Using {block} at unixtime(UTC): {timestamp}")
    for poolinfo in POOLS_TO_RUN_ON:
        if pool_id and poolinfo["pool_id"] != pool_id:
            continue
        print(f"\n\nRunning on {poolinfo['name']}, pool_id: {poolinfo['pool_id']}, gauge: {poolinfo['gauge']}, block: {block}\n\n")
        try:
            get_ecosystem_balances_w_csv(
                pool_id=poolinfo["pool_id"],
                gauge_address=poolinfo["gauge"],
                name=poolinfo["name"],
                chain = chain,
                block = block
            )
        except Exception as e:
            print(f"WARNING: run for {poolinfo['pool_id']} did not finish:\n{e}")


if __name__ == "__main__":
    main()
