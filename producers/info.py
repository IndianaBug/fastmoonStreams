from exchange_interaction import ExchangeAPIClient


coinbaseSecret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbaseAPI = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'
kucoinAPI = "65d92cc0291aa2000118b67b"
kucoinSecret = "3d449464-ab5e-4415-9950-ae31648fe90c"
kucoinPass = "sN038-(!UK}4"


client = ExchangeAPIClient(coinbaseAPI, coinbaseSecret, kucoinAPI, kucoinSecret, kucoinPass)
all_instruments = client.retrieve_all_instruments()
symbols = client.get_related_instruments(all_instruments, ["BTC", "BTC", "XBT"], ["PERP", "USD", "USD"], ["option", "future"])

# The Instruments must be of the same format (upper lower with hiphens) as in API calls
ws = {
    "binance" : [
        "spot.depth.BTCUSDT.snap", "spot.depth.BTCFDUSDT.snap", "spot.trades.BTCUSDT.BTCTUSD.BTCUSDC.BTCUSDS.BTCBUSD.BTCFDUSD", # if you want to mix different channels "spot.trades.BTCUSDT.liquidations.BTCTUSD,
        "perpetual.depth.BTCUSDT.snap", "perpetual.depth.BTCUSD_PERP.snap", "perpetual.trades.BTCUSD_PERP.BTCUSDT.BTCUSDC", "perpetual.liquidations.BTCUSD_PERP.BTCUSDT.BTCUSDC",
        "option.trades.BTC",
        ],
    "bybit" : [
        "spot.depth.BTCUSDT.snap", "spot.depth.BTCUSDC.snap", "spot.trades.BTCUSDT.BTCUSDC",
        "perpetual.depth.BTCUSDT.snap", "perpetual.depth.BTCUSD.snap", "perpetual.trades.BTCUSDT.BTCUSD.BTCPERP", "perpetual.liquidations.BTCUSDT.BTCUSD.BTCPERP",
        "option.trades.BTC", "option.oi.BTC",
        ],
    "okx" : [
        "spot.depth.BTC-USDT.snap", "spot.trades.BTC-USDT.BTC-USDC",
        "perpetual.depth.BTC-USDT-SWAP.snap", "perpetual.trades.BTC-USD-SWAP.BTC-USDT-SWAP.BTC-USDC-SWAP", "perpetual.liquidations.SWAP.FUTURES.OPTION",
        "option.trades.BTC",
        ],
    "deribit" : [
        "perpetual.depth.BTC-PERPETUAL.snap", "future.tradesagg.BTC", "perpetual.heartbeats.BTC.BTC-PERPETUAL",
        "option.tradesagg.BTC", "perpetual.heartbeats.BTC.BTC-PERPETUAL"
        ],
    "bitget" : [
        "spot.depth.BTCUSDT.snap", "future.trades.BTCUSDT.BTCUSDC",
        "perpetual.depth.BTCUSDT.snap", "perpetual.trades.BTCUSDT.BTCPERP.BTCUSD",
        ],
    "bingx" : [
        "spot.trades.BTC-USDT", "perpetual.trades.BTC-USDT",
        ],
    "kucoin" : [
        "spot.depth.BTC-USDT.snap", "spot.trades.BTC-USDT",
        "perpetual.depth.XBTUSDTM.snap", "perpetual.trades.XBTUSDTM",
        ],
    "gateio" : [
        "spot.depth.BTC_USDT.snap", "spot.trades.BTC_USDT",
        "perpetual.depth.BTC_USDT.snap", "perpetual.trades.BTC_USDT", 
        "option.trades.BTC", "option.oi.BTC",
        ],
    "mexc" : [
        "spot.depth.BTCUSDT.snap", "spot.trades.BTCUSDT",
        "perpetual.depth.BTC_USDT.snap", "perpetual.trades.BTC_USDT",
        ],
    "coinbase" : [
        "spot.depth.BTC-USD.snap", "spot.trades.BTC-USD", "spot.heartbeats.BTC-USD",
        ],
}

api = {
    "binance" : [
        "perpetual.funding.BTC.3600.spec", "perpetual.oi.BTC.15.spec", "perpetual.gta.BTC.300.spec",
        "option.oi.BTC.15.spec",
        ],
    "bybit" : [
        "perpetual.funding.BTC.3600.spec", "perpetual.oi.BTC.15.spec", "perpetual.gta.BTC.300.spec",
        "option.oifunding.15.BTC",
        ],
    "okx" : [
        "perpetual.funding.BTC.3600.spec", "perpetual.oi.BTC.15.spec", "perpetual.gta.BTC.300",
        "option.oi.BTC.15.spec",
        ],
    "deribit" : [
        "future.oifunding.BTC.15", "option.oifunding.BTC.15",
        ],
    "bitget" : [
        "perpetual.funding.BTC.3600.spec", "perpetual.oi.BTC.15.spec", 
    ],
    "bingx" : [
        "spot.depth.BTC-USDT.30", "perpetual.depth.BTC-USDT.30",
        ],
    "kucoin" : [
        "perpetual.oifunding.XBTUSDTM.15",
        ],
    "gateio" : [
        "perpetual.tta.BTC.300", "perpetual.oifunding.BTC.15", 
        "option.oi.BTC.15",
        ],
    "mexc" : [
        "perpetual.oifunding.BTC.15",
        ],
    "htx" : [
        "perpetual.oi.BTC.spec", "future.ttp.BTC", "future.tta.BTC",
        ],
}



