binance_api_endpoints = {
                    "spot" : "https://api.binance.com",
                    "perpetual" : {
                        "LinearPerpetual" : "https://fapi.binance.com",
                        "InversePerpetual" : "https://dapi.binance.com"
                    },
                    "future" : {
                        "LinearFuture" : "https://fapi.binance.com",
                        "InverseFuture" : "https://dapi.binance.com"
                    },
                    "option" : "https://eapi.binance.com"
                }

binance_api_linear_types = {
                        "depth" : "/fapi/v1/depth",
                        "funding" : "/fapi/v1/fundingRate",
                        "oi" : "/fapi/v1/openInterest",
                        "tta" : "/futures/data/topLongShortAccountRatio",
                        "ttp" : "/futures/data/topLongShortPositionRatio",
                        "gta" : "/futures/data/globalLongShortAccountRatio",
                        }
binance_api_inverse_types = {
                        "depth" : "/dapi/v1/depth",
                        "funding" : "/dapi/v1/fundingRate",
                        "oi" : "/dapi/v1/openInterest",
                        "tta" : "/futures/data/topLongShortAccountRatio",
                        "ttp" : "/futures/data/topLongShortPositionRatio",
                        "gta" : "/futures/data/globalLongShortAccountRatio",
                        }


binance_api_basepoints = {
                    "spot" :  {
                        "depth" : "/api/v3/depth",
                    },
                    "perpetual" : {
                        "LinearPerpetual" : binance_api_linear_types,
                        "InversePerpetual" : binance_api_inverse_types,
                    },
                    "future" : {
                        "LinearFuture" : binance_api_linear_types,
                        "InverseFutures" : binance_api_inverse_types
                    },
                    "option" : {
                        "oi" : "/eapi/v1/openInterest"
                                }                
                    }

binance_api_basepoints_params  = {
        "depth" : {
                "symbol": {"type": str, "default": ""},
                "limit": {"type": int, "default": 1000}
            },
        "funding" : {
                "symbol": {"type": str, "default": ""},
                "limit": {"type": int, "default": 100}
            },
        "oi" : {
                "symbol": {"type": str, "default": ""}
            },
        "tta_ttp_gta" : {
            "coin-m" : {
                "symbol": {"type": str, "default": ""},
                "period": {"type": str, "default": "5m"},
                "limit": {"type": int, "default": 1},
                        },
            "coin-c" : {
                "pair": {"type": str, "default": ""},
                "period": {"type": str, "default": "5m"},
                "limit": {"type": int, "default": 1},
                        },
        },
        "oioption" : {
            "underlyingAsset": {"type": str, "default": "ETH/BTC"},
            "expiration": {"type": str, "default": "221225"},
        }
    }


# ws # 



binance_ws_endpoints = {
                    "spot" : "wss://stream.binance.com:9443/ws",
                    "perpetual" : {
                        "LinearPerpetual" : "wss://fstream.binance.com/ws",
                        "InversePerpetual" : "wss://dstream.binancefuture.com/ws"
                    },
                    "future" : {
                        "LinearFuture" : "wss://fstream.binance.com/ws",
                        "InverseFutures" : "wss://dstream.binancefuture.com/ws"
                    },
                    "option" : "wss://nbstream.binance.com/eoptions/ws"
                }

binance_ws_linear_types = {
                        "depth" : "/fapi/v1/depth",
                        "trades" : "/fapi/v1/fundingRate",
                        "liquidations" : "/fapi/v1/openInterest",
                        }
binance_ws_inverse_types = {
                        "depth" : "/fapi/v1/depth",
                        "trades" : "/fapi/v1/fundingRate",
                        "liquidations" : "/fapi/v1/openInterest",
                        },


binance_ws_basepoints = {
                    "spot" :  {
                        "depth" : "/api/v3/depth",
                    },
                    "perpetual" : {
                        "LinearPerpetual" : binance_ws_linear_types,
                        "InversePerpetual" : binance_ws_inverse_types,
                    },
                    "future" : {
                        "LinearFuture" : binance_ws_linear_types,
                        "InverseFutures" : binance_ws_inverse_types
                    },
                    "option" : {
                               
                                }                
                    }

binance_stream_keys = {
    "liquidations" : "forceOrder",
    "trades" : "aggTrade",
    "depth" : "depth",
}



binance_ws_request_params  = {
        "depth" : ["symbol", "depth", "1000ms" ], # 500ms for futures and 1000ms for spot
        "trades" : ["symbol", "aggTrade"],
        "liquidations" : ["symbol", "forceOrder"],
    }