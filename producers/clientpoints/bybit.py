

bybit_api_endpoint = "https://api.bybit.com"


bybit_api_category_map = {
                        "spot" : "category=spot",
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
                        "oi" : "/v5/market/tickers",
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
}



bybit_ws_request_params  = {
        "depth" : ["symbol", "depth", "1000ms" ], # 500ms for futures and 1000ms for spot
        "trades" : ["symbol", "aggTrade"],
        "liquidations" : ["symbol", "forceOrder"],
    }