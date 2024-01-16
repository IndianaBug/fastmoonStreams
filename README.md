# SatoshiVault
Introducing BTC DataVault, your go-to API for real-time and historical BTC data. Harness the power of API calls to access second-by-second insights on prices, liquidations, open interest volume, full order book levels, taker volume, maker volume, funding rates, open interest, and long/short ratios. Covering top exchanges including Binance, OKEx, Coinbase, Bybit, Bitget, Deribit, and KuCoin, BTC DataVault is your gateway to seamless data integration without the need for websocket streaming. Elevate your applications with precise information for informed decision-making in the world of Bitcoin trading 

## Tasks
### Market data:
- [x] binance websockets, api
- [x] okx websockets, api
- [x] bybit websockets 
- [x] deribit websockets, api 
- [x] coinbase websockets 
### Sentiment data:
- [x] news agregator, crypto panic
### Feature Generation:
- [ ] chatGPT sentiment score, topic modeling
- [ ] Footprints, orderflow

###
https://github.com/dyn4mik3/OrderBook/tree/master/orderbook

Features ranges:
-0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.4, 1.6, 1.8, 2, 2.33, 2.66, 3, 3,5, 4, 5, 7,5, 10
- Volume profile
- Range contraction/expantion indicator
###


Pice momentum indicators
• Average true range --- good to find consolidation
• Over different periods
• Sudden spike or on sudden --- qunantify
• Moving averages to gauge the trend
• Price percentages below moving averages 100-1000

Features from open interest
• The rate of change of OI relatively to OI n-steps ago
• OI and price divergence
• OI and colume divergence
• OI for different time frames
• Combine Open interest with volatility bands, like true range. Figure out what traders are doing in consiolidation
• Open interest entropy within different price levels
• Turnonver ration entropy
• Open interest kurtosis
• Open interest skewness
• Open interest persistance at different levels
• Open interset distribtuion ot at different price levels

Features from  liquidations
• Liquidation count
• Liquidation speed ratio: the speed at which liquidations are occuring compared to overall volume
• Open interest distribution at liquidation ranges: This feature would measure the concentration of open interest within specific price ranges where significant liquidations have occurred
• Open Interest Volatility with Liquidations over Time: This feature would measure the correlation between open interest volatility and liquidations over a period of time. A high correlation could suggest that liquidation events are contributing to increased volatility.
• A liquidation price cluster is a group of liquidations that occur at a similar price level within a given timeframe. These clusters can be identified by calculating the distribution of liquidation prices and identifying areas where the distribution is concentrated.
• Liquidation Volume Ratio: This feature would measure the ratio of liquidation volume to open interest. A high liquidation volume ratio would suggest that liquidations are occurring frequently relative to the overall open interest, which could increase the risk of sharp price swings.
• Open Interest Volatility with Liquidations by Hour: This feature would measure the correlation between open interest volatility and liquidations for each hour of the day. A high correlation could suggest that liquidation events are contributing to increased volatility during specific hours
• Liquidation heatmaps: Use funding, historical liquidation data and open interest at specific price levels in combination of clustering algorithm to identify liquidation heatmap

Funding rate faetures
• Funding Rate
• Funding rate persistance
• Open interest sensitivity to funding rate
• Funding rate distribution by time of the day
• FUnding rate volatility with open interest
• Funding rate index risk --- ocmbination of multiple data
• Open Interest Sensitivity to Funding Rate with Liquidation Price Clusters

Top Trader Long Short Position

The "top trader long short position" metric measures the total net position of the top 20 traders by trading volume. This metric provides an overview of the overall sentiment of major traders on the platform. A positive value indicates that the top traders are net long, meaning they have more long positions than short positions. A negative value indicates that the top traders are net short, meaning they have more short positions than long positions.

Top Trader Long Short Accounts

The "top trader long short accounts" metric measures the number of accounts with both long and short positions held by the top 20 traders by trading volume. This metric provides an indication of the diversity of trading strategies among large traders. A higher value suggests that the top traders are more active in both long and short positions, while a lower value suggests that they are more focused on one side of the market.

 "long short ratio" metric measures the ratio of long positions to short positions opened by all traders on the platform. This metric provides an overview of the overall sentiment of traders on the platform. A high long short ratio indicates that there are more long positions than short positions, which suggests that traders are generally optimistic about the market. A low long short ratio indicates that there are more short positions than long positions, which suggests that traders are generally pessimistic about the market.


Feature of TopTrader Long/Short
* Top Trader Long Short Position Distribution: This feature would measure the distribution of the top trader long short position across a range of prices.
* Top Trader Long Short Position Correlation with Price: This feature would measure the correlation between the top trader long short position and the price of the asset. 
* Top Trader Long Short Position Volatility: This feature would measure the volatility of the top trader long short position over time.
* Top Trader Long Short Position Persistence: This feature would measure the tendency of the top trader long short position to remain positive or negative over a given timeframe.
* Top Trader Long Short Position Acceleration: This feature would measure the rate at which the top trader long short position is changing over time.
* Top Trader Long Short Position Distribution vs. Open Interest Distribution:

CME --- the same shit

Open interest --- the same shit. But there you have direct access to open interest of put calls and stuff so try to capitaliza on that


https://github.com/matplotlib/mplfinance --- financial data visualization
https://github.com/TrellixVulnTeam/stock-pattern-recorginition_PMJP?tab=readme-ov-file  ---- for Deep Learnong for Feature Generation


# For the next project
https://www.coinfeeds.io/api-documentation   
https://defillama.com/docs/api
https://bitaps.com/
https://github.com/TransposeData/transpose-python-sdk
https://dexterlab.com/best-on-chain-analysis-tools/
https://github.com/aaarghhh/awesome_osint_criypto_web3_stuff?tab=readme-ov-file#btc-blockchain-databases-and-analyzers

https://gz.blockchair.com/bitcoin/transactions/
https://docs.coinapi.io/authentication
https://www.blockcypher.com/dev/bitcoin/?python#block-height-endpoint

# Bitcoin fundamental price model ___ From blockchair data : https://blockchair.com/dumps#database
## Indicators:
### Bitcoin fundamental data: https://charts.woobull.com/bitcoin-price-models/
- Realized price
- VWAP Price
- CVDD Floor
- Delta Cap
- Balanced Price
- NVT ratio, NVT signal  https://charts.woobull.com/bitcoin-nvt-ratio/
- VWAPs at different length: https://charts.woobull.com/bitcoin-vwap-ratio/
- MVRV
- Mayer Multiple
- Difficulty ribbon
- Sharpe Ration
- Volatility vesus other assets
- RVT
- Bitcoin marcatcap gained per dollar invested
- Bitcoin volatility
- Federal reserve money printing
- Bitcoin inflation rate
- Stock to flow
- Volume vs network value: https://charts.woobull.com/bitcoin-volume-vs-network-value/
- Bitcoin congestion and fees:  https://charts.woobull.com/bitcoin-congestion/
- Bitcoin hash price, revenue generated by miners https://charts.woobull.com/bitcoin-congestion/
---- Check models from here: https://studio.glassnode.com/dashboards/aec5d292-d140-42a9-4fd9-7c02cbc889bc?referrer=use_case

### Bitcoin sentimental data: https://charts.woobull.com/bitcoin-price-models/
- [ ] youtube hot keyword scrapping -- youtube api   ---- https://developers.google.com/youtube/v3/docs

### Resources
https://gz.blockchair.com/bitcoin/transactions/
https://docs.coinapi.io/authentication
https://www.blockcypher.com/dev/bitcoin/?python#block-height-endpoint
