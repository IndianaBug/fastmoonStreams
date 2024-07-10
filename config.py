# config.py

coinbase_secret = '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIDOVctxJpAI/hHtbUN9VrHej4bWPRuT9um9FoBlTgiyaoAoGCCqGSM49\nAwEHoUQDQgAEJt8JWIh8CHm045POImBF0ZvVuX5FbQjIDhIT82hE5r1+vb8cSQ3M\nfEjriBy1/ZD3EywPNxyGe6nO/Wsq0M8hXQ==\n-----END EC PRIVATE KEY-----\n'
coinbase_api = 'organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/697a8516-f2e2-4ec9-a593-464338d96f21'
kucoin_api = "65d92cc0291aa2000118b67b"
kucoin_secret = "3d449464-ab5e-4415-9950-ae31648fe90c"
kucoin_pass = "sN038-(!UK}4"
elastic_password = "P0H3MsMaUKy7=6jOi-Jx"

default_price_value = 70000

# okx are SWAP for pepretual, FUTURE for futures and OPTION for options
okx_liquidations_inst_types = ["perpetual", "future"] #Okx only provides a unique stream for all liquidations. Those symbol found here will be processed others omited
okx_liquidations_symbol = "BTC" # if empty nothing wil be processed, if only basecoin, only liquidations of that basecoin will be processed

backup_symbols = { # you may cross symbols from different exchanges
    "binance" : "BTCUSDT@perpetual@binance",
    "bybit" : "BTCUSDT@perpetual@bybit",
    "okx" : "BTC-USDT-SWAP@perpetual@okx",
    "deribit" : "BTC-PERPETUAL@perpetual@deribit",
    "bitget" : "BTCUSDT@perpetual@bitget",
    "bingx" : "BTC-USDT@perpetual@bingx",
    "htx" : "BTCUSDT@perpetual@binance",
    "kucoin" : "XBTUSDTM@perpetual@kucoin",
    "mexc" : "BTC_USDT@perpetual@mexc",
    "gateio" : "BTC_USDT@perpetual@gateio",

}

merge_types = [
    "depth_spot", 
    "depth_future", 
    "trades_spot", 
    "trades_future", 
    "trades_option", 
    "oi_delta_future", 
    "liquidations_future",
    "oi_options", 
    "cdepth_spot", 
    "cdepth_future", 
    "rdepth_spot", 
    "rdepth_future"
    ]


message_processor_fail_threshold = 0.1


# MULTIPLIER CONFIGURATION

## BINANCE ###

# Contract values for Binance linear contracts (stablecoin/fiat-margined contracts) are standardized to 1 BTC,
# so no multiplication is needed.

# However, for coin-margined contracts, the contract values vary:
# - BTC contracts are worth 100 USD
# - Altcoin (other) contracts are worth 10 USD
# - If binance changes the contract values, this config file will need to be updated. simply add the basecoin and the following multiplier (ex : {"RBNB : 12"})

# This same principle applies to options contracts. But, options are worth in native coin.
binance_inverse_multipliers = {
            "BTC" : 100,
            "other" : 10
        }
binance_option_multipliers = {
            "BTC" : 1,
            "ETH" : 1,
            "BNB" : 1,
            "XRP" : 100,
            "DOGE" : 1000,
        }


### BYBIT ###

# Bybit USDT and USDC contracts worth 1 BTC, no need to multiply. 
# But, coin-marginated (inverse) contracts worth 1 usd. No need to config
# Options also worth 1 btc

### OKX ###
# okx is simmilar to binance though a bit different.
# if there is a lambda function instead of multiplier, its because the multiplier is worth in native coin rather than the stablecoin
okx_future_multipliers = {
    "USDT" : {
        "BTC" : lambda amount : amount * 0.01, 
        "ETH" : lambda amount : amount * 0.1, 
        "XLM" : 100,
        "TRX" : 1000,
        "other" : 10,
    },
    "USDC" : {
        "BTC" : lambda amount : amount * 0.0001,
        "ETH" : lambda amount : amount * 0.001,
        "XLM" : 100,
        "TRX" : 1000,
        "other" : 10, 
    },
    "USD" : {
        "XLM" : 100,
        "BTC" : 100,
        "TRX" : 1000,
        "other" : 10
    }
}
# options are worth in native coin 
okx_option_multipliers = {
            "BTC" : 0.01,
            "ETH " : 0.1,
            "LTC" : 1,
            "LINK" : 10,
            "DOT" : 10,
            "SOL" : 10,
            "ADA" : 100,
        }


### DERIBIT ###

deribit_future_multipliers = {
    "perpetual" : {
        "BTC-PERPETUAL" : lambda amount, price : amount  / price / 10,
        "ETH-PERPETUAL" : lambda amount, price : amount  / price,
        "ADA_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 10,
        "ALGO_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 10,
        "AVAX_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 0.1,
        "BCH_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 0.02,
        "BTC_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 0.001,
        "ETH_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 0.01,
        "LINK_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount,
        "LTC_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 0.1,
        "MATIC_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 10,
        "LINK_USDT-PERPETUAL" : lambda amount, *args, **kwargs: amount,
        "LTC_USDT-PERPETUAL" : lambda amount, *args, **kwargs: amount * 0.1,
        "NEAR_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount,
        "SOL_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 0.1,
        "TRX_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 100,
        "UNI_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount ,
        "XRP_USDC-PERPETUAL" : lambda amount, *args, **kwargs: amount * 10
    },
    "future" : {
    "BTC" : lambda amount, price : amount  / price / 10,
    "ETH" : lambda amount, price : amount  / price  
 }
}


deribit_option_multipliers = {
            "BTC" : 1,
            "ETH" : 1,
            "MATIC" : 1000,
            "SOL" : 10,
            "XRP" : 1000,
        }


### KUCOIN ###

# https://www.kucoin.com/pt/futures/contract/detail/ACEUSDTM
# Find you coin here and then add
kucoin_future_multipliers = {
    "XBTUSDTM" : 0.001,
    "XBTUSDTP" : 0.001,
    "XBTUSDM" : lambda amount, price: amount / price,
}


### MEXC ###
# https://www.mexc.com/support/articles/17827791509072
mexc_future_multipliers = {
    "BTC_USDT" : 0.0001,
    "BTC_USD" : lambda amount, price : amount * 100  / price
}

### GATEIO ###
# https://www.gate.io/futures_info_new/futures/usdt/BTC_USDT#baseinfo
gateio_future_multipliers = {
    "BTC_USDT" : 0.0001,
    "BTC_USD" : lambda amount, price : amount / price
}

gateio_option_multipliers = {
    "BTC_USDT" : 0.01,
    "BTC_USD" : lambda amount, price : amount / price
}


fiats = [
    "usd", 
    "eur", 
    "rub", 
    "try", 
    "uah", 
    "kzt", 
    "inr", 
    "gbp", 
    "krw", 
    "aud", 
    "chf", 
    "czk", 
    "dkk", 
    "nok", 
    "nzd", 
    "pln", 
    "sek", 
    "zar", 
    "huf", 
    "ils"
]
stablecoins = [
    "usdt", 
    "usdc", 
    "busd", 
    "dai", 
    "tusd",
    "fdusd"
    ]