
coinbase_repeat_response_code = -1041

coinbase_api_endpoint = "api.coinbase.com"


coinbase_api_basepoints = {
                "depth" : "/api/v3/brokerage/product_book",
                "info" : "/api/v3/brokerage/products",
                    }

coinbase_api_product_types_map = {
    "spot" : "product_type=SPOT",
    "future" : "product_type=FUTURE"
}

coinbase_api_product_types_mapv2 = {
    "spot" : "SPOT",
    "future" : "FUTURE"
}


# ws # 


coinbase_ws_endpoint = "wss://advanced-trade-ws.coinbase.com" 


coinbase_stream_keys = {
            "trades" : "market_trades",
            "depth" : "product_book",
            "heartbeats" : "heartbeats"
            }


def coinbase_get_symbol_name(symbol):
    return symbol.replace("-", "").lower()



