
import time
import re

bybit_api_endpoint = "https://api.bybit.com"
bybit_repeat_response_code = [10001]

bybit_api_category_map = {
                        "spot" : "spot",
                        "perpetual" : {
                            "LinearPerpetual" : "linear",
                            "InversePerpetual" : "inverse"
                        },
                        "future" : {
                            "LinearFuture" : "linear",
                            "InverseFuture" : "inverse"
                        },
                        "option" : "option"
                    }

bybit_api_basepoints = {
                        "depth" : "/v5/market/orderbook",
                        "gta" : "/v5/market/account-ratio",
                        "oioption" : "/v5/market/tickers",  
                        "funding" : "/v5/market/funding/history", 
                        "oi" : "/v5/market/open-interest"
                        }



bybit_api_params_map_derivates = {
    "gta" : lambda category, symbol : {"category" : category, "symbol" : symbol, "period" : "1h", "limit" : 1},
    "funding" : lambda category, symbol : {"category" : category, "symbol" : symbol, "period" : "1h", "limit" : 1},
    "depth" : lambda category, symbol : {"category" : category, "symbol" : symbol, "limit" : 500},
    "oifunding" : lambda category, symbol : {"category" : category, "symbol" : symbol},
    "oi" : lambda category, symbol : {"category" : category, "symbol" : symbol,  "intervalTime" : "5min", "limit" : 1},
} 

bybit_api_params_map = {
    "spot" : {
         "depth" : lambda category, symbol : {"category" : category, "symbol" : symbol, "limit" : 200},
    },
    "perpetual" : bybit_api_params_map_derivates,
    "future" : bybit_api_params_map_derivates, 
    "option" : {
        "oioption" : lambda category, baseCoin : {"category" : category, "baseCoin" : baseCoin},
    }
}

# ws # 


bybit_ws_endpoints = {
                    "spot" : "wss://stream.bybit.com/v5/public/spot",
                    "perpetual" : {
                        "LinearPerpetual" : "wss://stream.bybit.com/v5/public/linear",
                        "InversePerpetual" : "wss://stream.bybit.com/v5/public/inverse"
                    },
                    "future" : {
                        "LinearFuture" : "wss://stream.bybit.com/v5/public/linear",
                        "InverseFutures" : "wss://stream.bybit.com/v5/public/inverse"
                    },
                    "option" : "wss://stream.bybit.com/v5/public/option",
                    "Linear" : "wss://stream.bybit.com/v5/public/linear",
                    "Inverse" : "wss://stream.bybit.com/v5/public/inverse",
                }



bybit_ws_payload_map = {
    "spot" : {
        "depth" : lambda symbol : f"orderbook.200.{symbol}",
        "trades" : lambda symbol : f"publicTrade.{symbol}",
    },
    "perpetual" : {
        "depth" : lambda symbol : f"orderbook.500.{symbol}",
        "trades" : lambda symbol : f"publicTrade.{symbol}",
        "liquidations" : lambda symbol : f"liquidation.{symbol}",
    },
    "future" : {
        "depth" : lambda symbol : f"orderbook.500.{symbol}",
        "trades" : lambda symbol : f"publicTrade.{symbol}",
        "liquidations" : lambda symbol : f"liquidation.{symbol}",
    },
    "option" : {
        "oioption" : lambda symbol : f"tickers.{symbol}",
        "trades" : lambda symbol : f"publicTrade.{symbol}", # publicTrade.BTC
    },
}

def bybit_get_marginType(instType, symbol):
    marginType = None
    if instType == "perpetual" and "USDT" not in symbol:    
        marginType = "InversePerpetual"
    if instType == "perpetual" and "USDT" in symbol: 
        marginType = "LinearPerpetual"
    if instType == "future" and "USDT" not in symbol:    
        marginType = "InverseFuture"
    if instType == "future" and "USDT" in symbol: 
        marginType = "LinearFuture"
    return marginType


def bybit_get_instrument_name(symbol):
    return symbol.replace("_", "").lower()