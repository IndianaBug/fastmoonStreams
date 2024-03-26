## Exchange Streams Overview

The following tables outline the streamlined WebSocket and aiohttp methods provided per exchange.
Notes: 
- If you want to change call parameters, you need to modify them in the folder clientpoints.
- Bulk websockets are supported only for Binance, OKX, Bybit, Deribit, and Bitget.
- Bulk websockets will be separated by margin types (Linear, Inverse) for Binance, Bybit, Bitget. For Deribit and OKX, this separation will not occur.

### Binance

- Bulk depth not recommended.

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades                | Stream of trades per instrument. If option trades are involved, you may call with a specific option symbol (e.g., BTC-21441-C-1231), specific expiry (e.g., BTC-1231-C), or just underlying instrument (e.g., BTC)|
| liquidations          | Stream of liquidations per instrument  |

#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |
| funding  | Stream of funding per instrument     |
| oi | Open interest of a specific symbol. |
| tta   | The proportion of net long and net short accounts to total accounts of the top 20% users with the highest margin balance. Each account is counted once only. Long Account % = Accounts of top traders with net long positions / Total accounts of top traders with open positions. Short Account % = Accounts of top traders with net short positions / Total accounts of top traders with open positions. Long/Short Ratio (Accounts) = Long Account % / Short Account %.  For inverse types of contracts, the call is the same for all symbols (e.g., BTCUSD, not BTCUSD_PERP)|
| ttp  | The proportion of net long and net short positions to total open positions of the top 20% users with the highest margin balance. Long Position % = Long positions of top traders / Total open positions of top traders. Short Position % = Short positions of top traders / Total open positions of top traders. Long/Short Ratio (Positions) = Long Position % / Short Position %. For inverse types of contracts, the call is the same for all symbols (e.g., BTCUSD, not BTCUSD_PERP)|
| gta | The proportion of net long and net short accounts to total accounts of the top 20% users with the highest margin balance. Each account is counted once only. Long Account % = Accounts of top traders with net long positions / Total accounts of top traders with open positions. Short Account % = Accounts of top traders with net short positions / Total accounts of top traders with open positions. Long/Short Ratio (Accounts) = Long Account % / Short Account %. For inverse types of contracts, the call is the same for all symbols (e.g., BTCUSD, not BTCUSD_PERP)|
| funding, special_method="fundfutureperp" | Queries fundings for all possible derivatives in a single call |
| oi, special_method="oifutureperp" | Queries oi for all possible derivatives in a single call |
| gta, special_method="posfutureperp" | Queries tta, ttp, gta for all possible derivatives in a single call |




### Bybit

- Bulk depth not recommended.

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades                | Stream of trades per instrument. If option trades are involved, you may call with a specific option symbol (e.g., BTC-21441-C-1231), specific expiry (e.g., BTC-1231-C), or just underlying instrument (e.g., BTC)|
| liquidations          | Stream of liquidations per instrument  |

#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |
| funding  | Stream of funding per instrument     |
| oi | Open interest of a specific symbol. |
| tta   | The proportion of net long and net short accounts to total accounts of the top 20% users with the highest margin balance. Each account is counted once only. Long Account % = Accounts of top traders with net long positions / Total accounts of top traders with open positions. Short Account % = Accounts of top traders with net short positions / Total accounts of top traders with open positions. Long/Short Ratio (Accounts) = Long Account % / Short Account %.  For inverse types of contracts, the call is the same for all symbols (e.g., BTCUSD, not BTCUSD_PERP)|
| ttp  | The proportion of net long and net short positions to total open positions of the top 20% users with the highest margin balance. Long Position % = Long positions of top traders / Total open positions of top traders. Short Position % = Short positions of top traders / Total open positions of top traders. Long/Short Ratio (Positions) = Long Position % / Short Position %. For inverse types of contracts, the call is the same for all symbols (e.g., BTCUSD, not BTCUSD_PERP)|
| gta | The proportion of net long and net short accounts to total accounts of the top 20% users with the highest margin balance. Each account is counted once only. Long Account % = Accounts of top traders with net long positions / Total accounts of top traders with open positions. Short Account % = Accounts of top traders with net short positions / Total accounts of top traders with open positions. Long/Short Ratio (Accounts) = Long Account % / Short Account %. For inverse types of contracts, the call is the same for all symbols (e.g., BTCUSD, not BTCUSD_PERP)|
| funding, special_method="fundfutureperp" | Queries fundings for all possible derivatives in a single call |
| oi, special_method="oifutureperp" | Queries oi for all possible derivatives in a single call |
| gta, special_method="posfutureperp" | Queries tta, ttp, gta for all possible derivatives in a single call |
