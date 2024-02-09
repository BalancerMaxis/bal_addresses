from bal_addresses import Ecosystem
import csv
import os

### Example Run for ezETH/rETH
#  export POOL_ID=0x05ff47afada98a98982113758878f9a8b9fdda0a000000000000000000000645
#  export GAUGE_ADDRESS=0xc859bf9d7b8c557bbd229565124c2c09269f3aef
#  export BLOCK=19192051
#  pip3 install -r requirements.txt
#  python3 tools/ecosystem_deposits_for_pool.py

def main(
        chain="mainnet",
        output_filename="output.json"
         ):
    pool_id = os.environ["POOL_ID"]
    gauge_address = os.environ["GAUGE_ADDRESS"]
    block = os.environ["BLOCK"]
    eco = Ecosystem(chain)
    csv_file = output_filename
    user_balances =eco.get_ecosystem_balances(pool_id, gauge_address, block)
    with open(csv_file, 'w') as f:
        writer = csv.writer(f)

        writer.writerow(["depositor_address", "total_pool_tokens"])
        for depositor, amount in user_balances.items():
            writer.writerow([depositor, amount])
     print("CSV file generated successfully: ", csv_file)



if __name__ == "__main__":
    main()
