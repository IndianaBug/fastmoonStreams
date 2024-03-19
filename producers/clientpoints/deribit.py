deribit_repeat_response_code = -1130

deribit_endpoint = "wss://test.deribit.com/ws/api/v2"

deribit_marginCoins = ["BTC", "ETH", "USDC", "USDT", "EURR"]

deribit_methods = {
    "depth" : "public/get_order_book",
    "oifunding" : "public/get_book_summary_by_currency",
    "ws" : "public/subscribe",
}

deribit_stream_keys = {
        "trades" : "trades",    
        "liquidations" : "trades", # Trades Channel contains liquidations https://docs.deribit.com/#trades-instrument_name-interval
        "depth" : "book",
        "oifunding" : "ticker"
}

deribit_instType_keys = {
    "spot" : "spot",
    "perpetual" : "future",
    "future" : "future",
    "option" : "option"
}

ws = {
    "liquidations" : "https://docs.deribit.com/#trades-instrument_name-interval"
}


api_headers = {
    "jsonrpc": "2.0", "id": "generate_random_integer(10)",
    "method": "public/get_order_book",
    "params": { 
        "depth": 1000, 
        "instrument_name": "BTC-PERPETUAL"
        }
    }
            # "params": { 
            #     "currency": "BTC", 
            #     "kind": "option"
            #     }
            # }

def deribit_get_symbol_name(params):
    return params.get("symbol")


async def websocket_fetcher(link, headers):
    async with websockets.connect(link,  ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(headers))
        response = await websocket.recv()
        return response
