from syncer import ExchangeAPIClient, binance_get_marginType, bybit_get_marginType
from config import coinbase_secret, coinbase_api, kucoin_api, kucoin_pass, kucoin_secret

client = ExchangeAPIClient(
    coinbase_api, 
    coinbase_secret,
    kucoin_api,
    kucoin_secret, 
    kucoin_pass, 
    price_level_size=20, 
    process_interval=10,
    mode="testing",
    option_process_interval=2
    )

# Inspect what binance and bybit derivate symbols you may bulk with binance_get_marginType and binance_get_marginType
# If those are of the same margin, you may mix the. Any websocet except depth

ws = {
    "binance" : [
        "spot.depth.BTCUSDT.snap",                                        #  api ok   # ok
        "spot.depth.BTCFDUSD.snap",                                       #  api ok  # ok
        "spot.trades.BTCUSDT.BTCTUSD.BTCUSDC.BTCUSDS.BTCBUSD.BTCFDUSD",   # ok
        "perpetual.depth.BTCUSDT.snap",                                   # api ok  ws ok
        "perpetual.depth.BTCUSD_PERP.snap",                               # api ok  ws ok
        "perpetual.trades.BTCUSDT.BTCUSDC",                               # ok
        "perpetual.liquidations.BTCUSDT.BTCUSDC",                         # ok
        "perpetual.trades.BTCUSD_PERP",                                   # ok
        "perpetual.liquidations.BTCUSD_PERP",                             # ok
        "option.trades.BTC",                                              # ok
        ],
    "bybit" : [
        # "spot.trades.BTCUSDT.BTCUSDC",                                      # ok           
        # "spot.depth.BTCUSDT.snap",                                          # ok ok
        # "spot.depth.BTCUSDC.snap",                                          # ok ok 
        # "perpetual.depth.BTCUSDT.snap",                                     # ok ok
        # "perpetual.depth.BTCUSD.snap",                                      # ok ok
        # "perpetual.trades.BTCUSDT.BTCPERP",                                 # ok
        # "perpetual.trades.BTCUSD",                                          # ok
        # "perpetual.liquidations.BTCUSDT.BTCPERP",                           # ok
        # "perpetual.liquidations.BTCUSD",                                    # ok
        # "option.trades.BTC",                                                # ok
        ],
    # "okx" : [
    #     "spot.depth.BTC-USDT.snap",                                             # ok ok
    #     "spot.trades.BTC-USDT.BTC-USDC",                                        # ok
    #     "perpetual.depth.BTC-USDT-SWAP.snap",                                   # ok ok 
    #     "perpetual.trades.BTC-USD-SWAP.BTC-USDT-SWAP.BTC-USDC-SWAP",            # ok
    #     "perpetual.liquidations.SWAP.FUTURES.OPTION",                           # ok
    #     "option.optionTrades.BTC-USD",                                          # ok
    #     ],
    # "deribit" : [                                                               
    #     "perpetual.heartbeats.BTC-PERPETUAL",                                   # ok 
    #     "perpetual.depth.BTC-PERPETUAL.snap",                                   # ok # ok 
    #     "future.tradesagg.BTC",                                                 # ok
    #     "option.tradesagg.BTC",                                                 # ok
    #     # liquidations                                                          # ok
    #     ],
    # "bitget" : [
    #     "spot.depth.BTCUSDT.snap",                                              # ok ok
    #     "spot.trades.BTCUSDT.BTCUSDC",                                          # ok
    #     "perpetual.depth.BTCUSDT.snap",                                         # ok ok
    #     "perpetual.trades.BTCUSDT.BTCPERP.BTCUSD",                              # ok
    #     ],
    # "bingx" : [
    #     "spot.trades.BTC-USDT",                                                 # ok
    #     "perpetual.trades.BTC-USDT",                                            # ok
    #     "spot.depth.BTC-USDT.snap"                                              # ok ok
    #     ],
    # "kucoin" : [
    #     "spot.depth.BTC-USDT.snap",                                             # ok ok
    #     "spot.trades.BTC-USDT",                                                 # ok
    #     "perpetual.depth.XBTUSDTM.snap",                                        # ok ok
    #     "perpetual.trades.XBTUSDTM",                                            # ok
    #     ],
    # "gateio" : [
    #     "spot.depth.BTC_USDT.snap",                                             # ok ok
    #     "spot.trades.BTC_USDT",                                                 # ok
    #     "perpetual.depth.BTC_USDT.snap",                                        # api ok ok
    #     "perpetual.trades.BTC_USDT",                                            # ok
    #     # liquidations                                                          # ok
    #     ],
    # "mexc" : [
    #     "spot.depth.BTCUSDT.snap",                                              # ok ok
    #     "spot.trades.BTCUSDT",                                                  # ok
    #    "perpetual.depth.BTC_USDT.snap",                                         # api ok
    #     "perpetual.trades.BTC_USDT",                                            # ok
    #     ],
    # "coinbase" : [
    #     "spot.depth.BTC-USD.snap",                                              # ok ok
    #     "spot.trades.BTC-USD",                                                  # ok
    #     "spot.heartbeats.BTC-USD",                                              # ok
    #     ],
}

api = {
    # "binance" : [
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.oi.BTC.15.spec", 
    #     "perpetual.gta.BTC.15.spec",         # nein
    #     "option.oi.BTC.15.spec",
    #     ],
    # "bybit" : [                               # ok
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.oi.BTC.15.spec", 
    #     "perpetual.gta.BTC.15.spec",
    #     "option.oioption.BTC.15"
    #     ],
    # "okx" : [                                # ok
    #     "perpetual.oi.BTC.15.spec", 
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.gta.BTC.15",
    #     "option.oi.BTC-USD.15",
    #     ],
    # "deribit" : [
    #     "future.oifunding.BTC.60",            # ok
    #     "option.oifunding.BTC.60",
    #     ],
    # "bitget" : [                               # ok
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.oi.BTC.15.spec", 
    # ],
    # "bingx" : [                                 # ok
    #     "perpetual.funding.BTC-USDT.15", 
    #     "perpetual.oi.BTC-USDT.15",  
    #     "perpetual.depth.BTC-USDT.30",  
    #     ],
    # "kucoin" : [
    #     "perpetual.oifunding.XBTUSDTM.15",          # ok
    #     ],
    # "gateio" : [
    #     "perpetual.funding.BTC.20.spec",  
    #     "perpetual.oi.BTC.20.spec",    
    #     "perpetual.tta.BTC.20.spec",    
    #     "option.oi.BTC_USDT.60",            # nothing here
    #     ],
    # "mexc" : [                               # ok
    #     "perpetual.oifunding.BTC_USDT.15",
    #     ],
    # "htx" : [                                # ok
    #     "perpetual.oi.BTC.20.spec", 
    #     "perpetual.funding.BTC.60.spec", 
    #     "perpetual.gta.BTC.60.spec",
    #     ],
}


connection_data = client.build_connection_data(ws, api)

# print(connection_data)

def create_metrics_datastructure(self, 
                                 streams_data : dict,
                                 merge_spot_books:bool=False,
                                 merge_spot_trades:bool=False,
                                 merge_derivate_books:str=None,
                                 merge_derivate_trades:str=None,
                                 merge_derivate_oi_deltas:str=None,
                                 merge_liquidations:str=None,
                                 ):
    """ 
    Creates a metrics data structure based on the provided arguments and streams data.

    Args:
        streams_data (dict): The data streams to be used for metrics creation.
        merge_spot_books (bool, optional): 
            True - merges fiat and stablecoin books into one.
            False - separates fiat and stablecoin books. Defaults to False.
        merge_spot_trades (bool, optional): 
            True - merges fiat and stablecoin trades into one.
            False - separates fiat and stablecoin trades. Defaults to False.
        merge_derivative_books (str, optional): 
            Specifies the type of derivative books to merge. Options are:
                - 'future_perpetual'
                - 'future_perpetual_option'
                - None (default)
        merge_derivative_trades (str, optional): 
            Specifies the type of derivative trades to merge. Options are:
                - 'future_perpetual'
                - 'future_perpetual_option'
                - None (default)
        merge_derivative_oi_deltas (str, optional): 
            True - merges future and perpetual oi deltas.
            False - does not merge them.
            None - (default)
        merge_liquidations (str, optional): 
            Specifies the type of liquidations to merge. Options are:
                - 'future_perpetual'
                - 'future_perpetual_option'
                - None (default)
    """
    
    global_metrics = {}
    by_instrument = {}
    aggregated_maps = {}
    ticks = {}
    oi_option = {}
    
    for stream_data in streams_data:
        metric = stream_data.get("objective") if stream_data.get("objective") else stream_data.get("objectives")
        inst_type = stream_data.get("instType") if stream_data.get("instType") else stream_data.get("instTypes")
        
        if metric == "trades":
            for submetric in ["price", "buys", "sells"]:
                global_metrics[f"{submetric}_{inst_type}"] = 0
                if submetric != "price":
                    aggregated_maps[f"{submetric}_{inst_type}"] = {}
            by_instrument[f"price_{inst_type}"] = {}
            ticks[f"trades_{inst_type}"] = {}
            
        if metric == "depth":
            pass

        if metric == "oi":
            pass

        if metric == "liquidation":
            pass

        if metric == "funding":
            pass
        
        if metric in ["gta", "tta", "ttp"]:
            pass
        
def create_global_datastructures(
                            metric, 
                            *args,
                            **kwargs,
                            ):
    """
    Arguments:
        metric: price, trades, oi, liquidations, funding
        *args : perpetual, future, fiat, option, spot, merge_spot_trades, merge_perpetual_future_trades
                merge_perpetual_future_option_trades, merge_perpetual_future_oi,
                merge_perpetual_future_liquidations, merge_perpetual_future_option_liquidations
        
    
    Possible Types of Global Metrics:

        price_fiat: Weighted average price of fiat currency pairs based on trading volume.
        price_stablecoin: Weighted average price of stablecoin pairs based on trading volume.
        price_spot: Combined weighted average price of fiat and stablecoin pairs by volume.
        price_perpetual: Weighted average price of perpetual contract pairs by volume.

        buys_spot: Aggregate volume of fiat and stablecoin spot instruments on market buy orders.
        buys_fiat: Total volume of fiat currency buys in the market.
        buys_stablecoin: Total volume of stablecoin buys in the market.
        buys_perpetual: Total volume of perpetual contract buys.
        buys_future: Total volume of futures contract buys.
        buys_perpetual_future: Aggregate buys in both perpetual and future contracts.
        buys_perpetual_future_option: Combination of buys in perpetual, future, and option contracts.
        buys_option: Total volume of option contract buys.

        sells_spot: Aggregate volume of fiat and stablecoin spot instruments on market sell orders.
        sells_fiat: Total volume of fiat currency sells in the market.
        sells_stablecoin: Total volume of stablecoin sells in the market.
        sells_perpetual: Total volume of perpetual contract sells.
        sells_future: Total volume of futures contract sells.
        sells_perpetual_future: Aggregate sells in both perpetual and future contracts.
        sells_perpetual_future_option: Combination of sells in perpetual, future, and option contracts.
        sells_option: Total volume of option contract sells.

        oi_perpetual: Open interest in perpetual contracts.
        oi_future: Open interest in futures contracts.
        oi_perpetual_future: Combined open interest in both perpetual and futures contracts.
        oi_option: Open interest in options contracts.
        oi_perpetual_future_option: Combined open interest in perpetual, futures, and options contracts.

        longs_perpetual: Total long positions in perpetual contracts.
        longs_future: Total long positions in futures contracts.
        longs_perpetual_future: Combined long positions in both perpetual and futures contracts.
        longs_perpetual_future_option: Combination of long positions in perpetual, futures, and options contracts.
        longs_option: Total long positions in options contracts.

        shorts_perpetual: Total short positions in perpetual contracts.
        shorts_future: Total short positions in futures contracts.
        shorts_perpetual_future: Combined short positions in both perpetual and futures contracts.
        shorts_perpetual_future_option: Combination of short positions in perpetual, futures, and options contracts.
        shorts_option: Total short positions in options contracts.

        funding_rate: Weighted average of funding rate over open interest.
    """
    global_data_structure = {}
    
    conditions = [
        ({"stablecoin", "fiat", "merge_spot_trades"}, "price_fiat_stablecoin_", True),
        ({"stablecoin"}, "price_stablecoin", False),
        ({"fiat"}, "price_fiat", False)
    ]
        
            
        
            
        

# Global :  price_fiat, # weighted price of fiat pairs
#           price_stablecoin, # weighted price of stable_coin pairs, by total volume
#           price_spot, # weighted price of stablecoin and fiat price by volume
#           price_perpetual # weighted price of perpetual pairs by volume

            # Chatgpt, do the same for buys (market_buys but lets call it buys and sells) and open interest