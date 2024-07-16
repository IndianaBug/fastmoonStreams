deribit_repeat_response_code = -1130

deribit_endpoint = "wss://www.deribit.com/ws/api/v2"

deribit_marginCoins = ["BTC", "ETH", "USDC", "USDT", "EURR"]


deribit_jsonrpc_params_map = {
    "depth" : lambda symbol, kind : {"instrument_name" : symbol, "depth" : 1000},
    "oifunding" : lambda currency, kind : {"currency" : currency, "kind" : kind}
}

deribit_jsonrpc_channel_map = {
    "depth" : "public/get_order_book",
    "oifunding" : "public/get_book_summary_by_currency",
    "ws" : "public/subscribe",
    "heartbeats" : "/public/set_heartbeat"
}

deribit_instType_map = {
    "spot" : "spot",
    "perpetual" : "future",
    "future" : "future",
    "option" : "option"
}

deribit_ws_params_map = {
    "depth" : lambda symbol, kind: {"channels": [f"book.{symbol}.agg2"]},  
    "trades" : lambda symbol, kind: {"channels": [f"trades.{symbol}.100ms"]},
    "tradesagg" : lambda symbol, kind: {"channels": [f"trades.{kind}.{symbol}.100ms"]},
    "heartbeats": lambda symbol, kind: {},
}


def deribit_get_symbol_name(symbol):
    return symbol.replace("-", "").lower()

