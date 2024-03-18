
coinbase_repeat_response_code = -1041

coinbase_api_endpoint = "api.coinbase.com"

coinbase_api_product_type_map = {
        "spot" : "SPOT",
        "future" : "FUTURE"
                            }

coinbase_api_basepoints = {
                "depth" : "/api/v3/brokerage/product_book"
                    }



# ws # 


coinbase_ws_endpoint = "wss://advanced-trade-ws.coinbase.com" 


coinbase_stream_keys = {
            "trades" : "market_trades",
            "depth" : "product_book",
            }


def coinbase_get_symbol_name(d):
    if "product_id" in d:
        symbol = d.get("product_id")
    return symbol.replace("-", "").lower()