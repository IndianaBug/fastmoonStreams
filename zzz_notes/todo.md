# To-Do List

## 🌟 Priority
- [ ] Remove DOM from APimixers

## 🗓️ Must do
- [ ] Duckerize # helper https://github.com/kostyafarber/crypto-lob-data-pipeline?tab=readme-ov-file
- [ ] Telegram allerts


## Producer
- [ ] make prometeus server, monitor metrics
- [ ] visualize those with kibana

## Consumer
- [ ] Faust stats monitoring 🔍
- [ ] After having full metrics of streams, redesgn you system accordingly
- [ ] backpressure managment with max.poll.records and fetch.min.bytes
        run the app for a few minutes nad estimate the amount of data in bytes that it consumes over 1 secod at its noraml times, lower times and higher times. 
        Faust stats monitoring for your help
- [ ] implement CI/CD pipelines to automate the testing and deployment of your faust application.



<!-- Git helper
remove too large files from:
git stash
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch kafka.zip" --prune-empty --tag-name-filter cat -- --all
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force --all
git push --force --tags
git stash pop -->



<!-- ## Data Features

# Express levels in percentages from the current price.
# HOw many levels to create? Consider volatility, fine granuality. But to lower frequencies, choose coarser granuality. Liquidity, 
# BUT this must be a hyperparameter to tune, mate
# Systematically test if features make sense by using machine learning models. Perhabs, it would be wiser to test them in bulk
# Do some correlation analysis. Do something like random forests, that automatically give you the relations.
# Categorize price movements into more general types. -->


Core Metrics

<!-- # Depth, Canceled Depth, Reinforced Depth
# --- Depth by levels
# --- Cumulative depth by levels
# --- Arrival rate of orders by multiple time ranges.
# --- Acceleraton rate of orders by multiple time ranges
# --- ORder cancelation rate
# --- ORder modification rate
# --- Imbalance ration
# --- Absolute depth/ bids asks
# --- Depth acceleration
# --- 

# Trades -->

Composite Metrics
<!-- # --- Volatility adjsuted depth : Order depth normalized by market volatility
# --- Price Momentum: The rate of price change combined with order book dynamics.
# --- Order Flow Imbalance: The difference between the number of buy orders and sell orders arriving within a given time frame.
# --- Liquidity Metrics: Ratios that measure market liquidity, such as the total volume of orders at the top 5 levels.
# --- The ratio of historical price volatility to order book depth, indicating how volatility impacts liquidity.
# --- Order Book Density: The concentration of orders within a specific price range.
# --- Order Book Slope: The rate of change in cumulative volume across price levels, indicating the steepness of the order book.
# --- Entropy of depth: Entropy of Order Book: A measure of the randomness or disorder in the distribution of orders across price levels.
# --- Fourier Transform of Depth: Analyzes the frequency components of order book changes to identify cyclical patterns.
# --- Fractal Dimension of Order Book: A measure of the complexity of the order book structure, indicating how detailed it is at different scales.
# --- Wavelet Transform : Identifying short-term volatility bursts or long-term trends.
# --- Hurst Exponent : Analyzing the persistence of trends in order book changes.
# --- Stochastic Differential Equations: Captures the stochastic nature of order arrivals and cancellations.
# --- Luapunov Exponent: Understanding the predictability of market movements.
# --- Stochastic differential equation
# --- Agent based modeling Helps in modeling the impact of different trading strategies on market dynamics.
# --- 
# --- Cluster everything you have


# Price aggressiveness. Proportion of market orders hitting/lifting the depth. Their volume
# BId ask spread to average tradesd volume
# Impact of large trades on price movements on orderbook dynamics
# For how long certain orders or price levels have remained in the orderbook 
# Correlation covarianve of prices, volumnes and orerbook



# Assumptions
# Market Depth
# Is precision metter? 
# Assumes that understanding micro-market trends and order flow changes at specific price points is crucial for strategy execution
# Assumes that rapid adaptation and flexibility in response to immediate market conditions are critical for achieving trading objectives.

# Price patters categorization by many features: 
# Break out
# Reversal
# Fluctualtion / volatility
# Trending
# Ranging
# prabolic
# Average True range
# Rate of change
# Candlestick Patters
# Cook with deep clustering, analyze the utility of clusters -->





<!-- # Trades

## Open
## Close
## High
## Low
# Market buys 
# market sells
# imbalace
# Volume-Weighted Average Price (VWAP):
# Price volume correlation
# Time-Weighted Average Price (TWAP):
# Intraday seasonality, any seasonality
# Volatility
# Rolling mean of standart deviation over n intervals
# Trends and exponential oving averages
# Average True range
# Bollinger Bands
# General market impact, caused by all trades
# Specific market impact, caused by specific trades
# Microstructure Noise Models, autoregressions, rollm odelsvarianvce models
# Number of trades per minute
# Gaps between consegutive trades
# Momentum indicators, any of these
# Average trade size
# Trade size variance
# Median absolute deviation of trade sizes
# skewness, kurtosis
# VWAP
# TWAP
# Detection of significant increases in traded volume compared to historical averages Z-score of traded volume to identify outliers

# Depth
# Quote Stuffing Detection


# Terades clustering

# price_impact: impact on price of this trade
# volume : amount traded
# execution_gap
# cumulative_price_impact: over-n intervals
# price_velocity:  Price impact divided by the time difference.
# volume_impact : the difference in traded volume between consecutive trades
# trade_intensity : Over n interval. Number of trades executed within a fixed time window.
# rolling_volume: over n intervals
# Volume_velocity: volume_impact / price_velocity
# volatility: any andicator of volatility like ATR over n intervals
# momentum: any momentum indicators over n intervals
# rolling execution gap

# Trade Size Relative to Rolling Volume:
# Trade Volume Skewness: Indicates the asymmetry in trade volume distribution, capturing the presence of outliers.
# Trade Volume Kurtosis: Measures the "tailedness" of the volume distribution, indicating the presence of extreme values.
# Rolling kurtosis
# Rolling skewness 
# Rolling price impact
# autocorrelation
# Entropy
# Hurrst exponent
# Fractal dimention
# GARCH -->

Correlation between trade volumes and the number of liquidations over a fixed time window. Formula:Corr(Trade Volume,Liquidations) Corr(Trade Volume,Liquidations)


Open Interest Clustering:

Definition: Identify clusters of open interest changes at various price levels.
Usage: High concentrations of open interest changes can indicate significant positions.
Trade Volume Clustering:

Definition: Identify clusters of trade volumes at various price levels.
Usage: High trade volumes at certain levels can indicate active trading and position building.
Position Density:

Definition: Calculate the density of positions at each price level based on open interest changes.
Formula: 
Position Density
=
Open Interest Change at Level
Total Open Interest Change
Position Density= 
Total Open Interest Change
Open Interest Change at Level
​
 
Price Attraction Levels:

Definition: Identify price levels with the highest concentrations of positions.
Usage: These levels can act as magnets for price movements.
Net Position Change:

Definition: Calculate the net change in positions at each price level over time.
Formula: 
Net Position Change = Cumulative Open Interest Change at Level − Cumulative Liquidation Volume at Level
Net Position Change = Cumulative Open Interest Change at Level − Cumulative Liquidation Volume at Level



wait I have a better idea. So I have ticks of open interest. Right? So suppouse total open interest is 100 000 contracts. Over time, I will just track every contract opened on every level. Once it reaches 100 000 bam, I have a complete map. 
