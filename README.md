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

once imported like `from bal_addresses import AddrBook`.

Then you can invoke the Address Book on a chain like so

`a = AddrBook(chain_name)` where chain_name is one of the chains listed in `AddrBook.CHAIN_IDS_BY_NAME.keys()`

Then you can do this with the flatbook:
```
>>> a.flatbook["20230320-composable-stable-pool-v4/ComposableStablePoolFactory"]
'0xfADa0f4547AB2de89D1304A668C39B3E09Aa7c76'
>>> a.flatbook["multisigs/lm"]
'0xc38c5f97B34E175FFd35407fc91a937300E33860'
>>> 
```

This with the reversebook:
```text
>>> a.reversebook["0xfADa0f4547AB2de89D1304A668C39B3E09Aa7c76"]
'20230320-composable-stable-pool-v4/ComposableStablePoolFactory'
```

You can also use the structured data as follows
```
>>> r = a.dotmap
>>> r.multisigs
DotMap(lm='0xc38c5f97B34E175FFd35407fc91a937300E33860', dao='0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f', fees='0x7c68c42De679ffB0f16216154C996C354cF1161B', feeManager='0xf4A80929163C5179Ca042E1B292F5EFBBE3D89e6', karpatkey='0x0EFcCBb9E2C09Ea29551879bd9Da32362b32fc89', emergency='0xA29F61256e948F3FB707b4b3B138C5cCb9EF9888', maxi_ops='0x166f54F44F271407f24AA1BE415a730035637325', blabs_ops='0x02f35dA6A02017154367Bc4d47bb6c7D06C7533B', linearPoolController='0x75a52c0e32397A3FC0c052E2CeB3479802713Cf4')
>>> r.multisigs.dao
'0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f'
```

Note that for the deployments the dotmap has a problem with digit starting members.  For this reason you have to use it like this
```text
>>> r["20230320-composable-stable-pool-v4"]["ComposableStablePoolFactory"]
'0xfADa0f4547AB2de89D1304A668C39B3E09Aa7c76'
```


As you can see from the examples above, the dotmap works like a dict, so you can easily loop over any part of the structure.

```python
from bal_addresses import AddrBook
a = AddrBook("mainnet")
r = a.dotmap
for contract, address in r["20230320-composable-stable-pool-v4"].items():
    print(f"{contract} has {address}")
```
Returns
```text
ComposableStablePoolFactory has 0xfADa0f4547AB2de89D1304A668C39B3E09Aa7c76
MockComposableStablePool has 0x5537f945D8c3FCFDc1b8DECEEBD220FAD26aFdA8
```

There is also search and lookup commands
```text
>>> a.search_many("Composable")
{'20230320-composable-stable-pool-v4/ComposableStablePoolFactory': '0xfADa0f4547AB2de89D1304A668C39B3E09Aa7c76', '20230320-composable-stable-pool-v4/MockComposableStablePool': '0x5537f945D8c3FCFDc1b8DECEEBD220FAD26aFdA8', '20230206-composable-stable-pool-v3/ComposableStablePoolFactory': '0xdba127fBc23fb20F5929C546af220A991b5C6e01', '20230206-composable-stable-pool-v3/MockComposableStablePool': '0x222bc81C6F3C17e9e9Aba47a12f55a1Dea42f163', '20220906-composable-stable-pool/ComposableStablePoolFactory': '0xf9ac7B9dF2b3454E841110CcE5550bD5AC6f875F', '20221122-composable-stable-pool-v2/ComposableStablePoolFactory': '0x85a80afee867aDf27B50BdB7b76DA70f1E853062', '20221122-composable-stable-pool-v2/MockComposableStablePool': '0x373b347bc87998b151A5E9B6bB6ca692b766648a'}
>>> a.search_many("GaugeAdder")
{'20230109-gauge-adder-v3/GaugeAdder': '0x5efBb12F01f27F0E020565866effC1dA491E91A4', '20220325-gauge-adder/GaugeAdder': '0xEd5ba579bB5D516263ff6E1C10fcAc1040075Fe2', '20220628-gauge-adder-v2/GaugeAdder': '0x2fFB7B215Ae7F088eC2530C7aa8E1B24E398f26a'}
>>> a.search_unique("GaugeControl")
'20220325-gauge-controller/GaugeController'
>>> a.latest_contract("Vault")
'0xBA12222222228d8Ba445958a75a0704d566BF2C8'
>>> a.reversebook[a.latest_contract("ComposableStablePoolFactory")]
'20230320-composable-stable-pool-v4/ComposableStablePoolFactory'
>>> 

```
Most of the other functions are used by a github action which regenerates files read in by those 2 functions on a weekly basis.  You can explore them if you would like.  

