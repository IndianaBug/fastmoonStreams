
kucoin_repeat_response_code = -1130

kucoin_api_endpoints = {
            "spot" : "https://api.kucoin.com",
            "perpetual" : "https://api-futures.kucoin.com",
        }


kucoin_api_basepoints = {
            "spot" : {
                "depth" : "/api/v3/market/orderbook/level2"
            },
            "perpetual" : {
                "depth" : "/api/v1/level2/snapshot",
                "oifunding" : "/api/v1/contracts/",
            }
        }


# ws # 


kucoin_ws_endpoint = "https://api.kucoin.com/api/v1/bullet-public"


kucoin_stream_keys = {
    "spot" : {
        "trades" : "/market/match:",
        "depth" : "/market/level2:",
    },
    "perpetual" : {
        "trades" : "/contractMarket/execution:",
        "depth" : "/contractMarket/level2:",
    },
}


def kucoin_get_symbol_name(d):
    if "symbol" in d:
        symbol = d.get("symbol")
    return symbol.replace("-", "").lower()