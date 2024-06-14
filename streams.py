from syncer import ExchangeAPIClient, binance_get_marginType, bybit_get_marginType
from config import coinbase_secret, coinbase_api, kucoin_api, kucoin_pass, kucoin_secret, fiats, stablecoins

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
        # "spot.depth.BTCFDUSD.snap",                                       #  api ok  # ok
        # "spot.trades.BTCUSDT.BTCTUSD.BTCUSDC.BTCUSDS.BTCBUSD.BTCFDUSD",   # ok
        # "perpetual.depth.BTCUSDT.snap",                                   # api ok  ws ok
        # "perpetual.depth.BTCUSD_PERP.snap",                               # api ok  ws ok
    #     "perpetual.trades.BTCUSDT.BTCUSDC",                               # ok
    #     "perpetual.liquidations.BTCUSDT.BTCUSDC",                         # ok
    #     "perpetual.trades.BTCUSD_PERP",                                   # ok
    #     "perpetual.liquidations.BTCUSD_PERP",                             # ok
    #     "option.trades.BTC",                                              # ok
        ],
    "bybit" : [
        "spot.trades.BTCUSDT.BTCUSDC",                                      # ok           
    #     "spot.depth.BTCUSDT.snap",                                          # ok ok
    #     "spot.depth.BTCUSDC.snap",                                          # ok ok 
    #     "perpetual.depth.BTCUSDT.snap",                                     # ok ok
    #     "perpetual.depth.BTCUSD.snap",                                      # ok ok
    #     "perpetual.trades.BTCUSDT.BTCPERP",                                 # ok
    #     "perpetual.trades.BTCUSD",                                          # ok
    #     "perpetual.liquidations.BTCUSDT.BTCPERP",                           # ok
    #     "perpetual.liquidations.BTCUSD",                                    # ok
    #     "option.trades.BTC",                                                # ok
        ],
    # "okx" : [
    #     "spot.depth.BTC-USDT.snap",                                             # ok ok
    #     "spot.trades.BTC-USDT.BTC-USDC",                                        # ok
    #     "perpetual.depth.BTC-USDT-SWAP.snap",                                   # ok ok 
    #     "perpetual.trades.BTC-USD-SWAP.BTC-USDT-SWAP.BTC-USDC-SWAP",            # ok
    #     "perpetual.liquidations.SWAP.FUTURES.OPTION",                           # ok
    #     "option.optionTrades.BTC-USD",                                          # ok
    #     ],
    "deribit" : [                                                               
    #     "perpetual.heartbeats.BTC-PERPETUAL",                                   # ok 
    #     "perpetual.depth.BTC-PERPETUAL.snap",                                   # ok # ok 
        "future.tradesagg.BTC",                                                 # ok
    #     "option.tradesagg.BTC",                                                 # ok
    #     # liquidations                                                          # ok
        ],
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


    