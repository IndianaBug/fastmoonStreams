import time
import requests

instType = ["derivate", "spot"]
derivateType = ["perp", "future", "option"]
marginType = ["coin-m", "coin-c"]

# option url binance "https://eapi.binance.com/eapi/v1/exchangeInfo"

exchange_infos = {
    "binance" : {
        "spot" : "https://api.binance.com/api/v1/exchangeInfo",
        "linear" : "https://fapi.binance.com/fapi/v1/exchangeInfo",
        "inverse" : "https://dapi.binance.com/dapi/v1/exchangeInfo",
        "option" : "https://eapi.binance.com/eapi/v1/exchangeInfo"
    },
    "bybit" : {
        "spot" : "https://api.bybit.com/v5/market/instruments-info?category=spot",
        "linear" : "https://api.bybit.com/v5/market/instruments-info?category=linear",
        "inverse" : "https://api.bybit.com/v5/market/instruments-info?category=inverse",
        "option" : "https://api.bybit.com/v5/market/instruments-info?category=option"
    },
    "okx" : {   # This one is different from others
        "spot" : "https://www.okx.com/api/v5/public/instruments?instType=SPOT",
        "perpetual" : "https://www.okx.com/api/v5/public/instruments?instType=SWAP",
        "futures" : "https://www.okx.com/api/v5/public/instruments?instType=FUTURES",
        "option" : "https://www.okx.com/api/v5/public/instruments?instType=OPTION&instFamily=BTC-USD",
    },

}

binance_productType = {
    "spot" : "BTCUSDT",
    "coin-m" : {
        "perp" : {
            "PERPETUAL" : "BTCUSD_PERP",
        },
        "future" : {
            "NEXT_QUARTER" : "BTCUSDT_240329",
            "CURRENT_QUARTER" : "BTCUSDT_240329",
        }
    },
    "coin-c" : {
        "perp" : {
            "PERPETUAL" : "BTCUSD_PERP",
            "PERPETUAL DELIVERING" : "BTCUSD_PERP"
        },
        "future" : {
            "NEXT_QUARTER" : "BTCUSDT_240329",
            "CURRENT_QUARTER" : "BTCUSDT_240329",
        },
    "option" : "BTC-210129-40000"
    }
}

bybit_productType = {
    "spot" : "BTCUSDT",
    "linear" : {
        "LinearPerpetual" : "BTCUSDT",
        "LinearFutures" : "BTC-29MAR24",
    },
    "inverse" : {    # The same as coin-c on binance
        "InversePerpetual" : "BTCUSD", 
        "InverseFutures" : "ETHUSDH24",
    },
    "option" : "ETH-3JAN23-1250-P"
}


okx_productType = {
    "spot" : "BTCUSDT",
    "swap" : {
        "LinearPerpetual" : "BTCUSDT",
        "LinearFutures" : "BTC-29MAR24",
    },
    "futures" : {    # The same as coin-c on binance
        "InversePerpetual" : "BTCUSD", 
        "InverseFutures" : "ETHUSDH24",
    },
    "option" : "ETH-3JAN23-1250-P"
}


# url = exchange_infos.get("oxk").get("perpetual")

# import requests

# r = requests.get(url)
# print(r.status_code)
# r = r.json()

# contract_type = set([x.get("contractType") for x in r.get("result").get("list")])

# symbols = [x.get("symbol") for x in r.get("result").get("list") if x.get("contractType") == "InverseFutures"]
# # symbols = set([x["symbol"] for x in r["optionSymbols"]])
# # contract_type = set([x["contractType"] for x in r["optionSymbols"]])

# # # NEXT_QUARTER = [x for x in r["symbols"] if x["contractType"] == "PERPETUAL DELIVERING"]

# print(symbols)

def simple_request(url):
    r = requests.get(url)
    print(r.status_code)
    r = r.json()
    return r


bybitContractTypeByProduct = {
    "spot" : "BTCUSDT",
    "perpetual" : {
        "LinearPerpetual" : "BTCUSDT",
        "InverseFutures" : "BTCUSD",
    },
    "future" : {
        "LinearPerpetual" : "BTCUSD",
        "InverseFutures" : "ETHUSDH24",
    },
    "option" : "ETH-3JAN23-1250-P"
}


print(get_bybit_symbols("option"))
