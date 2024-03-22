

bybit_api_endpoint = "https://api.bybit.com"


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

bybit_api_basepoint = {
                        "depth" : "/v5/market/orderbook",
                        "gta" : "/v5/market/account-ratio",
                        "oi" : "/v5/market/tickers",  # only for option
                        "funding" : "/v5/market/funding/history", # linear inverse
                        }



bybit_api_params_map_derivates = {
    "gta" : lambda category, symbol : {"category" : category, "symbol" : symbol, "startTime" : time.time()-20, "endTime" : time.time(), "limit" : 1},
    "funding" : lambda category, symbol : {"category" : category, "symbol" : symbol, "period" : "1h", "limit" : 1},
    "depth" : lambda category, symbol : {"category" : category, "symbol" : symbol, "limit" : 500},
    "tickers" : lambda category, symbol : {"category" : category, "symbol" : symbol},
    "oi" : lambda category, symbol : {"category" : category, "symbol" : symbol, "intervalTime" : "5min"}, # Call
}

bybit_api_params_map = {
    "spot" : {
         "depth" : lambda category, symbol : {"category" : category, "symbol" : symbol, "limit" : 200},
    },
    "perpetual" : bybit_api_params_map_derivates,
    "future" : bybit_api_params_map_derivates, 
    "option" : {
        "oi" : lambda category, baseCoin : {"category" : category, "baseCoin" : baseCoin},
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
                    "option" : "wss://stream.bybit.com/v5/public/option"
                }


def build_ws_message(symbol, objective):
    arg = 
    msg = {
    "req_id": "test", 
    "op": "subscribe",
    "args": [arg]
    }


bybit_ws_payload_map = {
    "spot" : {
        "depth" : "",
        "trades" : "", 
    },
    "perpetual" : {
        "depth" : "",
        "trades" : "", 
        "oifunding" : "",
    },
    "future" : {
        "depth" : "",
        "trades" : "", 
    },
    "option" : {
        "oi" : 
    },
}



bybit_ws_params_map  = {

    }




# WS methods

# ticker for OI, trades (unserlyingAsset for options)/ fetches everything