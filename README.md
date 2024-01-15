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


#### Order flow features
Order Flow Momentum (OFM): Measures the change in order flow activity over time.
Order Flow Mean Reversion (OFMR): Measures the tendency of order flow activity to revert to its mean.
Order Flow Autocorrelation (OFAC): Measures the correlation of order flow activity with itself at a lag.
Order Flow Hurst Exponent (OFHE): Measures the fractal dimension of order flow activity.
Order Flow Entropy (OFE): Measures the degree of randomness in order flow activity.
Order Flow Asymmetry (OFA): Measures the imbalance between buy and sell order sizes.
Order Flow Skewness (OFS): Measures the degree to which order flow activity is skewed towards one side of the market.
Order Flow Kurtosis (OFK): Measures the degree to which order flow activity is peaked or flat-topped.
Order Flow Noise (OFN): Measures the amount of random noise in order flow activity.
Order Flow Profitability (OFP): Measures the profitability of trades based on order flow indicators.
Order Flow Risk (OFR): Measures the risk of trades based on order flow indicators.
Order Imbalance (OI): Measures the net difference between buy and sell orders at a specific price level.
Suitability for DL: High. OI data is readily available and can be used to train DL models to predict price movements and identify potential trading opportunities.
Delta: The net change in OI between two consecutive price levels.
Suitability for DL: High. Delta data can be used to track order flow dynamics and identify potential trend reversals.
Volume Imbalance (VI): Measures the net difference between buy and sell volume at a specific price level.
Suitability for DL: Moderate. VI data can be used to identify areas of strong support and resistance and potential trading opportunities.
Volume Profile (VP): A cumulative volume histogram that represents the distribution of trading activity throughout the trading day.
Suitability for DL: High. VP data can be used to identify support and resistance levels, identify areas of accumulation and distribution, and assess potential trading opportunities.
Order Flow Heatmap (OH): A visual representation of order flow activity, typically displayed as a color-coded grid where darker colors indicate higher order density.
Suitability for DL: Moderate. OH data can be used to identify areas of congestion and potential trading opportunities.
Footprint Chart: A dynamic visualization of order flow activity, showing the arrival of buy and sell orders at specific price levels.
Suitability for DL: High. Footprint charts can be analyzed using DL models to identify patterns and potential trading opportunities.
Cluster Analysis: A technique for grouping related orders based on their price and time of arrival.
Suitability for DL: Moderate. Cluster analysis can be used to identify potential imbalances and trading opportunities.
Order Size Distribution (OSD): A histogram of order size distribution, showing the frequency of different order sizes.
Suitability for DL: Moderate. OSD data can be used to identify institutional or retail-driven order flow and potential trading opportunities.
Order Flow Volatility: Measures the variation in order flow activity over time.
Suitability for DL: Moderate. Order flow volatility can be used to identify potential trading opportunities and assess market sentiment.
Order Flow Correlation: Measures the relationship between order flow activity at different price levels.
Suitability for DL: Moderate. Order flow correlation can be used to identify potential trading opportunities and assess market sentiment.
Order Flow Volume Ratio (OFVR): Measures the ratio of buy order volume to sell order volume.
Order Flow Depth (OFD): Measures the total number of limit orders at a specific price level.
Order Flow Time (OFT): Measures the time it takes for an order to be filled.
Order Flow Imbalance Duration (OID): Measures the duration of an order imbalance.
Order Flow Imbalance Width (OIW): Measures the width of an order imbalance.
Order Flow Imbalance Persistence (OIP): Measures the persistence of an order imbalance.
Order Flow VWAP (OFVWAP): Measures the volume-weighted average price of all orders executed at a specific price level.
Order Flow Spread (OFS): Measures the difference between the bid and ask prices.
Order Flow Bid-Ask Ratio (OBAR): Measures the ratio of the bid price to the ask price.
Order Flow Quote-to-Trade Ratio (QTR): Measures the ratio of the number of quotes to the number of trades.
Order Flow Liquidity (OFL): Measures the ease with which an asset can be bought or sold.
Order Flow Fragmentation (OFF): Measures the degree to which order flow is spread across different trading venues.
Order Flow Efficiency (OFE): Measures the degree to which order flow reflects the underlying demand and supply for an asset.
Order Flow Predictability (OFP): Measures the ability to predict future price movements based on order flow indicators.
Order Imbalance Distribution (OID): Measures the distribution of order imbalance across different price levels.
Order Flow Clustering (OFC): Groups related orders based on their order size, price, and time of arrival.
Order Flow Filtering (OFF): Filters out noise and irrelevant information from order flow data.
Order Flow Anomaly Detection (OFAD): Detects unusual patterns or deviations from normal order flow activity.
Order Flow Trend Analysis (OFTA): Analyzes the trends in order flow activity to identify potential price movements.
Order Flow Regime Switching (OFRS): Identifies changes in the trading regime based on order flow patterns.
Order Flow Signal Generation (OFSG): Generates trading signals based on order flow indicators.
Order Flow Portfolio Optimization (OFPO): Optimizes trading portfolios based on order flow analysis.
Order Flow Risk Management (OFRM): Manages trading risks based on order flow indicators.
Order Flow Dynamical Systems Modeling (OFDSM): Models the dynamics of order flow activity using complex systems theory.
Order Flow Reinforcement Learning (OFRL): Trains trading agents using reinforcement learning to learn from order flow data.
Order Flow Big Data Analytics (OFBDA): Analyzes large-scale order flow data using big data analytics techniques.
Order Flow Cloud Computing (OFCC): Deploys order flow analysis and trading algorithms on cloud computing platforms.
Order Flow Artificial Intelligence (OFAI): Integrates artificial intelligence techniques into order flow analysis and trading strategies.
Order Imbalance (OI): Measures the net difference between buy and sell orders at a specific price level.
Order Flow Volume Ratio (OFVR): Measures the ratio of buy order volume to sell order volume.
Order Flow Depth (OFD): Measures the total number of limit orders at a specific price level.
Order Flow Time (OFT): Measures the time it takes for an order to be filled.
Order Flow Imbalance Duration (OID): Measures the duration of an order imbalance.
Order Flow Imbalance Width (OIW): Measures the width of an order imbalance.
Order Flow Imbalance Persistence (OIP): Measures the persistence of an order imbalance.
Order Flow VWAP (OFVWAP): Measures the volume-weighted average price of all orders executed at a specific price level.
Order Flow Spread (OFS): Measures the difference between the bid and ask prices.
Order Flow Bid-Ask Ratio (OBAR): Measures the ratio of the bid price to the ask price.
Order Flow Quote-to-Trade Ratio (QTR): Measures the ratio of the number of quotes to the number of trades.
Order Flow Liquidity (OFL): Measures the ease with which an asset can be bought or sold.
Order Flow Fragmentation (OFF): Measures the degree to which order flow is spread across different trading venues.
Order Flow Efficiency (OFE): Measures the degree to which order flow reflects the underlying demand and supply for an asset.
Order Flow Predictability (OFP): Measures the ability to predict future price movements based on order flow indicators.
"Order Flow Features for Predicting Directional Movement in High-Frequency Data" by Michael Pritzker and Michael Uryasev (2023)
"Order Flow Features for Detecting High-Frequency Trading Strategies" by Tao Chen, Ruilin Ma, and Qingbo Zhang (2022)
"Order Flow Features for Predicting Liquidity in Electronic Markets" by Xinran Li and Xianming Hu (2021)
"Order Flow Features for Identifying Dark Pool Activity" by Haim Mendelson, Yuqiu Sun, and Jun Zhang (2020)
"Order Flow Features for Forecasting Volatility in Financial Markets" by Xi Chen, Xinyang Wang, and Mingxuan Li (2019)

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
