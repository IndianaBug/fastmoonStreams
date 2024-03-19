bingx_repeat_response_code = -1130

bingx_api_endpoint = "https://open-api.bingx.com"


bingx_api_basepoints = {
            "spot" : {
                "depth" : "/openApi/spot/v1/market/depth"
            },
            "perpetual" : {
                "depth" : "/openApi/swap/v2/quote/depth",
                "oi" : "/openApi/swap/v2/quote/openInterest",
                "funding" : "/openApi/swap/v2/quote/premiumIndex",
            }
        }


# ws # 


bingx_ws_endpoints = {
    "spot" : "wss://open-api-ws.bingx.com/market",
    "perpetual" : "wss://open-api-swap.bingx.com/swap-market"
}



bingx_stream_keys = {
        "trades" : "trade",
        "depth" : "depth100",
}


def bingx_get_symbol_name(d):
    if "symbol" in d:
        symbol = d.get("symbol")
    return symbol.replace("-", "").lower()