
kucoin_repeat_response_code = -1130

kucoin_api_endpoints = {
            "spot" : "https://api.kucoin.com",
            "perpetual" : "https://api-futures.kucoin.com",
        }

kucoin_api_product_type_map = {
        "spot" : "SPOT",
        "future" : "FUTURE"
                            }

kucoin_api_basepoints = {
            "spot" : {
                "depth" : "/api/v3/market/orderbook/level2"
            },
            "perp" : {
                "depth" : "/api/v1/level2/snapshot",
                "oifunding" : "/api/v1/contracts/",
            }
        }


# ws # 


kucoin_ws_endpoint = "wss://advanced-trade-ws.coinbase.com" 


kucoin_stream_keys = {
            "trades" : "market_trades",
            "depth" : "product_book",
            }


def kucoin_get_symbol_name(d):
    if "product_id" in d:
        symbol = d.get("product_id")
    return symbol.replace("-", "").lower()