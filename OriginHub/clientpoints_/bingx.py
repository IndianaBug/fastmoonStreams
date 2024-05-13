bingx_repeat_response_code = -1130

bingx_api_endpoint = "https://open-api.bingx.com"


bingx_api_basepoints = {
            "spot" : {
                "depth" : "/openApi/spot/v2/market/depth"
            },
            "perpetual" : {
                "depth" : "/openApi/swap/v2/quote/depth",
                "oi" : "/openApi/swap/v2/quote/openInterest",
                "funding" : "/openApi/swap/v2/quote/premiumIndex",
            }
        }
bingx_pi_param_map = {
    "spot" : {
        "depth" : lambda symbol : {"symbol" : symbol.replace("-", "_"), "depth" : 1000, "type" : "step1"},
    },
    "perpetual" : {
        "depth" : lambda symbol : {"symbol" : symbol, "limit" : "1000"},
        "oi" : lambda symbol : {"symbol" : symbol},
        "funding" : lambda symbol : {"symbol" : symbol},
    }
}

# ws # 


bingx_ws_endpoints = {
    "spot" : "wss://open-api-ws.bingx.com/market",
    "perpetual" : "wss://open-api-swap.bingx.com/swap-market"
}



bingx_stream_keys = {
    "spot" : {
        "trades" : "trade",
        "depth" : "depth100",
    },
    "perpetual" : {
        "trades" : "trade",
        "depth" : "depth100",
    }
}


def bingx_get_symbol_name(symbol):
    return symbol.replace("-", "").lower()

