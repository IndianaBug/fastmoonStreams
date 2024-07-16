# mode testing and production and explain everything that is done during testing and production




# App Configuration Documentation

This document explains various configuration parameters used in the application.

## Initial Price Configuration

### `initial_price`

**Description:** Defines the initial price configuration needed to start the app.

**Parameters:**
- `symbol`: The trading pair symbol.
- `exchange`: The exchange where the symbol is traded.
- `instrument_type`: The type of instrument (e.g., perpetual).

## OKX Liquidation Settings Filter

### `okx_liquidations_filter`

**Description:** Settings related to OKX liquidation data filters.

**Parameters:**
- `instrument_types`: A list of instrument types to process (e.g., perpetual, future).
- `basecoin`: Basecoin to filter the data. If commented out, the symbols list will be used instead.
- `symbols`: A list of specific symbols to process. Uncomment and fill this list if filtering by symbols instead of basecoin.

## Fallback Symbols

### `fallback_symbols`

**Description:** A list of fallback symbols with their respective exchange and instrument type. If there is a stream that doesn’t have the price metric but price is needed to merge, this price will be used as a proxy. There must also be a stream of trades with this exact symbol.

**Parameters:**
- `symbol`: The trading pair symbol.
- `exchange`: The exchange where the symbol is traded.
- `instrument_type`: The type of instrument (e.g., perpetual).

## Data Merge Types

### `data_merge_types`

**Description:** A list of data merge types used for various data operations.

**Available Data Merge Types:**

- `spot_depth`: Depth of the spot market order book.
- `future_depth`: Depth of the perpetual market order book.
- `spot_trades`: Trades occurring in the spot market.
- `future_trades`: Trades occurring in the futures market.
- `option_trades`: Trades occurring in the options market.
- `future_oi_delta`: Changes in open interest for perpetual and futures contracts.
- `future_liquidations`: Liquidation events in the perpetual nad future markets.
- `option_oi`: Open interest in options contracts.
- `spot_canceled_depth`: Canceled orders in the spot market order book.
- `future_canceled_depth`: Canceled orders in the futures market order book.
- `spot_reinforced_depth`: Reinforced depth of the spot market order book.
- `future_reinforced_depth`: Reinforced depth of the futures market order book.

## Merge Intervals

### `merge_intervals_seconds`

**Description:** Specifies the intervals (in seconds) for merging data for different types.

**Parameters:**
- `spot`: Interval for spot data.
- `future`: Interval for future data.
- `option`: Interval for option data.




## Option Data Aggregation Settings

### `option_data_aggregation`
- **Description**: Settings for aggregating option open_interest data based on price ranges and expiry windows.
- **Parameters**:
  - `price_ranges`: A list of price values to create ranges for aggregation. The list can start from 0 but it is not necessary. It will create ranges of prices to merge on, such as -inf to x, x to y, and so on.
  - `expiry_windows`: A list of expiry values to create windows for aggregation. This list must contain 0 and does not contain negative values.
  - `fallback_symbols`: A dictionary containing symbols for index prices of options.
- **Example**:
    ```yaml
    option_data_aggregation:
      price_ranges: [0, 50, 100, 150, 200]  # Aggregates option open_interest data based on price ranges
      expiry_windows: [0, 7, 14, 30, 60]  # Aggregates option open_interest data based on expiry windows
      fallback_symbols:
        BTCUSD:
          index_symbol: BTCUSD_INDEX
        ETHUSD:
          index_symbol: ETHUSD_INDEX
    ```




option_data_aggregation
This section defines settings for aggregating option open interest data based on price ranges and expiry intervals.

price_buckets: A list of price values to create ranges (buckets) for aggregation. The list can start from 0 but it is not necessary. It will create ranges of prices to merge on, such as -inf to x, x to y, and so on. Can be float
expiry_intervals: A list of expiry values to create intervals for aggregation. This list must contain 0 and does not contain negative values.
fallback_symbols: A dictionary containing symbols for index prices of options. Only integers
This structure uses the new variable names price_buckets and expiry_intervals to clearly describe the purpose of the data they represent.





if one level size, then same for every instrument type
else not the same
spot_perpetual_future_data_aggregation:
  price_level_size: 20
  # price_level_size :
  #   spot : 20
  #   future : 20
  #   perpetual : 20


merge_interval: 60
# merge_interval:
#   spot: 60
#   perpetual: 60
#   future: 60
#   option: 60


# It can be tricky to merge futures OI, we need to balance it as the 20% difference of futures price is ok.

merge_types:
  spot:
    - depth
    - trades
    - canceled_depth
    - reinforced_depth
  perpetual_future:
    - depth
    - trades
    - oi
    - liquidations
    - canceled_depth
    - reinforced_depth
  option:
    - oi
    - depth
    - future
    - perpetual

  future:
    - depth
    - trades
    - oi
    - liquidations
    - canceled_depth
    - reinforced_depth

  perpetual:
    - depth
    - trades
    - oi
    - liquidations
    - canceled_depth
    - reinforced_depth

There can not be both perpetual_future and perpetual/future. THese are mutually exclusive. Threw an error if you see this

# Doesnt make sense to merge spot with anything just like options. Futures and perpetual can be merged

# None
# or daily_volume
# or open_interest
# options do not have weight factor

# merge_interval:
#   spot: 60
#   perpetual: 60
#   future: 60
#   option: 60



merge_weighting_factor: 
  spot:
    - depth: None 
    - trades: None 
  perpetual:
    - depth: None  
    - trades: None 
    - oi: None     
    - liquidations: None 
  future:
    - depth: None  
    - trades: None 
    - oi: None     
    - liquidations: None     
  perpetual_future:
    - depth: None  
    - trades: None
    - oi: None     
    - liquidations: None    



# If you really enjoy pain then do this

  <!-- # price_level_size :
  #   spot : 20
  #   future : 20
  #   perpetual : 20
  #   perpetual_future : 20  # IF you merge future_perpetual instruments

# calculate_canceled_depth:
#   spot: True
#   # perpetual: True
#   # future: True 
#   # perpetual_future: True
#   # option : True
# calculate_reinforced_depth:
#   spot: True
#   # perpetual: True
#   # future: True 
#   # perpetual_future: True
#   # option : True -->