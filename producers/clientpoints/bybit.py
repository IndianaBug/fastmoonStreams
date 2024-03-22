

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
                        }

bybit_api_params_map = {
    "gta" : lambda category, symbol : {"category" : category, "symbol" : symbol, "period" : "1d", "limit" : 50},
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


bybit_stream_keys = {
    "liquidations" : "liquidation",
    "trades" : "publicTrade",
    "depth" : "orderbook",
    "oifunding" : "tickers",
    "oi" : "tickers",
    "funding" : "tickers"
}



bybit_ws_request_params  = {
        "depth" : ["symbol", "depth", "1000ms" ], # 500ms for futures and 1000ms for spot
        "trades" : ["symbol", "aggTrade"],
        "liquidations" : ["symbol", "forceOrder"],
    }