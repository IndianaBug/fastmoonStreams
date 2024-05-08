from syncer import ExchangeAPIClient, binance_get_marginType, bybit_get_marginType
from config import coinbase_secret, coinbase_api, kucoin_api, kucoin_pass, kucoin_secret

client = ExchangeAPIClient(coinbase_api, coinbase_secret, kucoin_api, kucoin_secret, kucoin_pass)

# Inspect what binance and bybit derivate symbols you may bulk with binance_get_marginType and binance_get_marginType
# If those are of the same margin, you may mix the. Any websocet except depth

ws = {
    # "binance" : [
    #     "spot.depth.BTCUSDT.snap", 
    #     "spot.depth.BTCFDUSD.snap", 
    #     "spot.trades.BTCUSDT.BTCTUSD.BTCUSDC.BTCUSDS.BTCBUSD.BTCFDUSD", 
    #     "perpetual.depth.BTCUSDT.snap", 
    #     "perpetual.depth.BTCUSD_PERP.snap", 
    #     "perpetual.trades.BTCUSDT.BTCUSDC", 
    #     "perpetual.liquidations.BTCUSDT.BTCUSDC",
    #     "perpetual.trades.BTCUSD_PERP", 
    #     "perpetual.liquidations.BTCUSD_PERP",
    #     "option.trades.BTC",
    #     ],
    # "bybit" : [
    #     "spot.trades.BTCUSDT.BTCUSDC",
    #     "spot.depth.BTCUSDT.snap", 
    #     "spot.depth.BTCUSDC.snap", 
    #     "perpetual.depth.BTCUSDT.snap", 
    #     "perpetual.depth.BTCUSD.snap", 
    #     "perpetual.trades.BTCUSDT.BTCPERP", 
    #     "perpetual.trades.BTCUSD", 
    #     "perpetual.liquidations.BTCUSDT.BTCPERP", 
    #     "perpetual.liquidations.BTCUSD", 
    #     "option.trades.BTC",
    #     ],
    # "okx" : [
    #     "spot.depth.BTC-USDT.snap", 
    #     "spot.trades.BTC-USDT.BTC-USDC",
    #     "perpetual.depth.BTC-USDT-SWAP.snap", 
    #     "perpetual.trades.BTC-USD-SWAP.BTC-USDT-SWAP.BTC-USDC-SWAP", 
    #     "perpetual.liquidations.SWAP.FUTURES.OPTION",
    #     "option.optionTrades.BTC-USD",
    #     ],
    
    # "deribit" : [
    #     "perpetual.depth.BTC-PERPETUAL.snap", 
    #     "future.tradesagg.BTC",
    #     "option.tradesagg.BTC", 
    #     "perpetual.heartbeats.BTC.BTC-PERPETUAL"
    #     ],
    # "bitget" : [
    #     "spot.depth.BTCUSDT.snap", 
    #     "perpetual.trades.BTCUSDT.BTCUSDC",
    #     "perpetual.depth.BTCUSDT.snap", 
    #     "perpetual.trades.BTCUSDT.BTCPERP.BTCUSD",
    #     ],
    # "bingx" : [
    #     "spot.trades.BTC-USDT", 
    #     "perpetual.trades.BTC-USDT",
    #     "spot.depth.BTC-USDT"
    #     ],
    "kucoin" : [
        "spot.depth.BTC-USDT.snap", 
    #     "spot.trades.BTC-USDT",
    #     "perpetual.depth.XBTUSDTM.snap", 
    #     "perpetual.trades.XBTUSDTM",
        ],
    # "gateio" : [
    #     "spot.depth.BTC_USDT.snap", 
    #     "spot.trades.BTC_USDT",
    #     "perpetual.depth.BTC_USDT.snap", 
    #     "perpetual.trades.BTC_USDT", 
    #     ],
    # "mexc" : [
    #     "spot.depth.BTCUSDT.snap", 
    #     "spot.trades.BTCUSDT",
    #    "perpetual.depth.BTC_USDT.snap",  
    #     "perpetual.trades.BTC_USDT",
    #     ],
    "coinbase" : [
        # "spot.depth.BTC-USD.snap", 
        # "spot.trades.BTC-USD", 
        # "spot.heartbeats.BTC-USD",
        ],
}

api = {
    # "binance" : [
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.oi.BTC.15.spec", 
    #     "perpetual.gta.BTC.15.spec",
    #     "option.oi.BTC.15.spec",
    #     ],
    # "bybit" : [
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.oi.BTC.15.spec", 
    #     "perpetual.gta.BTC.15.spec",
    #     "option.oioption.BTC.15"
    #     ],
    # "okx" : [
    #     "perpetual.oi.BTC.15.spec", 
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.gta.BTC.15",
    #     "option.oi.BTC-USD.15",
    #     ],
    # "deribit" : [
    #     "future.oifunding.BTC.15",  
    #     "option.oifunding.BTC.15",
    #     ],
    # "bitget" : [
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.oi.BTC.15.spec", 
    # ],
    # "bingx" : [
    #     "perpetual.funding.BTC-USDT.15", 
    #     "perpetual.oi.BTC-USDT.15",  
    #     "perpetual.depth.BTC-USDT.30",  
    #     ],
    # "kucoin" : [
    #     "perpetual.oifunding.XBTUSDTM.15",
    #     ],
    # "gateio" : [
    #     "perpetual.funding.BTC.20.spec",  
    #     "perpetual.oi.BTC.20.spec",    
    #     "perpetual.tta.BTC.20.spec",    
    #     "option.oi.BTC_USDT.20",
    #     ],
    # "mexc" : [
    #     "perpetual.oifunding.BTC_USDT.15",
    #     ],
    # "htx" : [
    #     "perpetual.oi.BTC.20.spec", 
    #     "perpetual.funding.BTC.60.spec", 
    #     "perpetual.gta.BTC.60.spec",
    #     ],
}

connectionData = client.build_connection_data(ws, api)

a, b = connectionData[0].get("url_method")()

print(b)


# for e in connectionData:
#     print("----")
#     print(e)