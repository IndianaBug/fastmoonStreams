from bridge import ExchangeAPIClient, binance_get_marginType, bybit_get_marginType
from WSConnectionManager import producer
import rapidjson as json
import asyncio

# binance_get_marginType(instType, symbol)
# binance_get_marginType(instType, symbol)

coinbaseSecret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbaseAPI = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'
kucoinAPI = "65d92cc0291aa2000118b67b"
kucoinSecret = "3d449464-ab5e-4415-9950-ae31648fe90c"
kucoinPass = "sN038-(!UK}4"


client = ExchangeAPIClient(coinbaseAPI, coinbaseSecret, kucoinAPI, kucoinSecret, kucoinPass)

# all_instruments = client.retrieve_all_instruments()
# symbols = client.get_related_instruments(all_instruments, ["BTC", "BTC", "XBT"], ["PERP", "USD", "USD"], ["option", "future"])
# print(symbols)

# print([x for x in client.okx_symbols_by_instType("future") if "BTC" in x])

# The Instruments must be of the same format (upper lower with hiphens) as in API calls. You may merge streams with the same channels (objectives). Bybit/Binance derivate perpetual futures must be sepparated by instrument type, use provided helpers

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
    # "kucoin" : [
    #     "spot.depth.BTC-USDT.snap", 
    #     "spot.trades.BTC-USDT",
    #     "perpetual.depth.XBTUSDTM.snap", 
    #     "perpetual.trades.XBTUSDTM",
    #     ],
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
    # "coinbase" : [
    #     "spot.depth.BTC-USD.snap", 
    #     "spot.trades.BTC-USD", 
    #     "spot.heartbeats.BTC-USD",
    #     ],
}

api = {
    "binance" : [
        "perpetual.funding.BTC.15.spec", 
        "perpetual.oi.BTC.15.spec", 
        "perpetual.gta.BTC.15.spec",
        "option.oi.BTC.15.spec",
        ],
    "bybit" : [
        "perpetual.funding.BTC.15.spec", 
        "perpetual.oi.BTC.15.spec", 
        "perpetual.gta.BTC.15.spec",
        "option.oioption.BTC.60"
        ],
    "okx" : [
        "perpetual.oi.BTC.15.spec", 
        "perpetual.funding.BTC.15.spec", 
        "perpetual.gta.BTC.15",
        "option.oi.BTC-USD.15",
        ],
    # "deribit" : [
    #     "future.oifunding.BTC.15",  
    #     "option.oifunding.BTC.15",
    #     ],
    # "bitget" : [
    #     "perpetual.funding.BTC.15.spec", 
    #     "perpetual.oi.BTC.15.spec", 
    # ],
    # "bingx" : [
    #     "perpetual.funding.BTC-USDT.30", 
    #     "perpetual.oi.BTC-USDT.30",  
        # "perpetual.depth.BTC-USDT.30",  
        # ],
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

# for e in connectionData:
#     print("----")
#     print(e)

# async def rr():
#     data = await connectionData[0]["1stBooksSnapMethod"]()
#     print(data)
# asyncio.run(rr())

__name__ = "__main__"

if __name__ == '__main__':
    cryptoProducer = producer(connectionData)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cryptoProducer.run_producer())
