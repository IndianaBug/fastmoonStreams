## Exchange Streams Overview

The following tables outline the streamlined WebSocket and aiohttp methods provided per exchange.
Notes: 
- If you want to change call parameters, you need to modify them in the folder clientpoints.
- Bulk websockets are supported only for Binance, OKX, Bybit, Deribit, and Bitget.
- Bulk websockets will be separated by margin types (Linear, Inverse) for Binance, Bybit, Bitget. For Deribit and OKX, this separation will not occur.

### Binance

- Bulk depth not recommended.
- FAQs : https://www.binance.com/en/support/faq/crypto-derivatives?c=4&navId=4
- API FAQs : https://binance-docs.github.io/apidocs/spot/en/#spot-account-trade

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
| funding, special_method="fundfutureperp" | Queries fundings for Expiry Futures and Perpetual Futures in a single call |
| oi, special_method="oifutureperp" | Queries oi for Expiry Futures and Perpetual Futures in a single call |
| gta, special_method="posfutureperp" | Queries tta, ttp, gta for Expiry Futures and Perpetual Futures in a single call |




### Bybit

- Bulk depth not recommended.
- FAQs : https://bybit-exchange.github.io/docs/api-explorer/v5/market/market
- API FAQs : https://bybit-exchange.github.io/docs/v5/intro

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades                | Stream of trades per instrument. For options use underlying instrument. Ex. BTC for streaming all options trades|
| liquidations          | Stream of liquidations per instrument  |
| oifunding             | Streams the latest price snapshot, best bid/ask price, and trading volume in the last 24 hours.  https://bybit-exchange.github.io/docs/v5/market/tickers  |


#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |
| funding  | Stream of funding per instrument     |
| oi | Open interest of a specific symbol. |
| oifunding | Queries the latest price snapshot, best bid/ask price, and trading volume in the last 24 hours. https://bybit-exchange.github.io/docs/v5/market/tickers |
| gta | The ratio of users with net long and short positions (not the volume of positions)|
| funding, special_method="fundfutureperp" | Queries fundings for all possible derivatives in a single call |
| oi, special_method="oifutureperp" | Queries oi for Expiry Futures and Perpetual Futures in a single call |
| gta, special_method="posfutureperp" | Queries tta, ttp, gta for Expiry Futures and Perpetual Futures in a single call |



### OKX

- Bulk depth not recommended.
- FAQs : None
- API FAQs : https://www.okx.com/docs-v5/en/#overview

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades                | Stream of trades per instrument |
| liquidations          | Streams all liquidations per instrument type. Available types: SWAP, FUTURES, OPTION, MARGIN which must be inputed instead of the symbol  |
| funding             | Stream of funding for certain instrument  |
| oi             | Stream of open interest for certain instrument |
| optionTrades             |  Streams trades for all options with underlying instrument Ex. BTC-USD |


#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |
| funding  | Queries of funding per instrument     |
| oi | Open interest of a specific symbol. |
| oitotal | Retrieve the open interest and trading volume for Expiry Futures and Perpetual Futures. |
| gta | Retrieve the ratio of users with net long vs net short positions for Expiry Futures and Perpetual Futures. |
| oi, special_method="oifutureperp" | Queries oi for Expiry Futures and Perpetual Futures in a single call |
| funding, special_method="fundfutureperp" | Queries fundings for Expiry Futures and Perpetual Futures in a single call |



### Deribit

- Bulk depth not recommended.
- FAQs : None
- API FAQs : https://docs.deribit.com/#deribit-api-v2-1-1

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades (liquidations)               | Stream of trades per instrument. Every trade will be marked weather it's liquidation or not |
| tradesagg   (liquidations)             | Streams trades for all instruments by instType For Expiry Futures and Perpetual Futures just input "future" in instType parameter, "option" for options. Symbol parameter should be underlying asset Ex. BTC . Every trade will be marked weather it's a liquidation or not|
| heartbeats                | You need to call it for every instrument you stream in order to keep the connection alive |

#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |
| oifunding  | Retrieves the summary information such as open interest, funding, 24h volume, etc. for all instruments  . For Expiry Futures and Perpetual Futures just input "future" in instType parameter, "option" for options|



### Coinbase

- Bulk streams not allowed. You need to create separated ws connection for every stream.
- FAQs : None
- API FAQs : https://docs.cloud.coinbase.com/advanced-trade-api/docs/welcome

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades                | Stream of trades per instrument |

#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |



### Bitget

- Bulk streams of depth not recommended.
- FAQs : None
- API FAQs : https://www.bitget.com/api-doc/common/intro

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades                | Stream of trades per instrument |
| oifunding          | Streams the latest open inderest, funding,  traded price, bid price, ask price and 24-hour trading volume of the instruments. When there is a change deal, buy, sell, issue |


#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |
| funding  | Queries of funding per instrument     |
| oifunding | Retrives the latest open inderest, funding,  traded price, bid price, ask price and 24-hour trading volume of the instruments. When there is a change deal, buy, sell, issue |
| oi, special_method="oifutureperp" | Queries oi for Perpetual Futures in a single call |
| funding, special_method="fundfutureperp" | Queries fundings for Perpetual Futures in a single call |


### Bingx

- Bulk streams not allowed. You need to create separated ws connection for every stream.
- FAQs : None
- API FAQs : https://bingx-api.github.io/docs/#/en-us/swapV2/changelog

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams snapshot of books and bids with the length of 100                                                                |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades, needSnap=True  | Stream of trades of an instrument                                   |



#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Bingx are not clear with weight of rate limits. Websockets only stream absolute amounts of books with the length of 100, these are with the length of 1000. Use it, but be mindful with rate limits. Maybe, call with intervall of 30+seconds|
| funding  | Queries of funding per instrument     |
| oi | Retrives the latest open inderest, funding,  traded price, bid price, ask price and 24-hour trading volume of the instruments. When there is a change deal, buy, sell, issue |



### Kucoin

- Bulk streams not allowed. You need to create separated ws connection for every stream.
- FAQs : None
- API FAQs : https://www.kucoin.com/docs/beginners/introduction

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to orderbook in absolute amounts                                                            |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades  | Stream of trades of an instrument                                   |



#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | not recommended to use due to weigted rate limits|
| oifunding | The real-time ticker includes this https://www.kucoin.com/docs/rest/futures-trading/market-data/get-symbol-detail |



### Gate.io

- Bulk streams not allowed. You need to create separated ws connection for every stream.
- Only runs on the cloud, use Japan as the location for optimal performance
- Only USDT marginated futures available
- FAQs : None
- API FAQs : https://www.gate.io/docs/developers/apiv4/en/

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades (liquidations)               | Streams trades for an instrument. Every trade will be marked weather it was a liquidaiton or not. |
| oifunding             | Streams oi, funding by an underlying_instrument or an instrument https://www.gate.io/docs/developers/apiv4/en/#list-futures-tickers  |
| oi             | Only for options. Streams open interest for every option instrument by an underlying instrument (BTC) |


#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | Not recommended to use due to limit rates |
| trades (liquidations)  | Queries trades for an instrument. Every trade will be marked weather it was a liquidaiton or not|
| oifunding | Queries this oi, funding for an instrument or an underlying instrument (ex. BTC) https://www.gate.io/docs/developers/apiv4/en/#list-futures-tickers    |
| liquidations | Retrives liquidation history of an instrument |
| tta (oi)| Queries, oi, tta by an instrument or an underlying_instrument (ex. BTC) https://www.gate.io/docs/developers/apiv4/en/#futures-stats 



### HTX

- Bulk streams not allowed. You need to create separated ws connection for every stream.
- FAQs : None
- API FAQs : https://www.htx.com/en-us/opend/newApiPages/

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to order books in absolute amount                                                                      |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades                | Streams trades for an instrument |
| liquidations             |Streams liquidations for an underlying instrument  |
| funding            | Streams funding for an underlying instrument |


#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Queries updates to order books in absolute amount                                                                      |
| oi                | Queries trades for an instrument. Every trade will be marked weather it was a liquidaiton or not. |
| tta             | 	Query Top Trader Sentiment Index Function-Account by an underlying Instrument (use future as the instType)|
| ttp            | 	Query Top Trader Sentiment Index Function-Position, only for Linear Margin Types by an underlying Instrument (use future as the instType)|
| depth     special_method="depthfutureperp"           | Queries the depth snapshot of all Expiry Futures and Perpetual Futures for an underlying instrument  (use future and the instType) |
| trades   special_method="tradesfutureperp"          | Queries last trades of all Expiry Futures and Perpetual Futures for an underlying instrument  (use future and the instType) |
| oi        special_method="oifutureperp"     | Queries current open interest for all Expiry Futures and Perpetual Futures for an underlying instrument  (use future and the instType) |





### MEXC

- Bulk streams not allowed. You need to create separated ws connection for every stream.
- Overall, api support is poor and unfriendly.
- I wouldn't use perpetual depth streams.
- API FAQs : https://mexcdevelop.github.io/apidocs/contract_v1_en

#### Websockets

| Method Name           | Description                                                                                                            |
|-----------------------|------------------------------------------------------------------------------------------------------------------------|
| depth                 | Streams updates to orderbook in absolute amounts                                                            |
| depth, needSnap=True  | The same as depth but will snap the order books with the length of 1000 levels                                         |
| trades  | Stream of trades of an instrument                                   |
| oifunding | The real-time ticker includes this https://www.kucoin.com/docs/rest/futures-trading/market-data/get-symbol-detail |



#### Aiohttp

- pullTimeout need to be passed to every method, which is the intreval between every pull

| Method Name          | Description                                                                                                            |
|---------------------------|------------------------------------------------------------------------------------------------------------------------|
| depth   | not recommended to use due to weigted rate limits|
| oifunding | The real-time ticker includes this https://mexcdevelop.github.io/apidocs/contract_v1_en/#public-channels |
