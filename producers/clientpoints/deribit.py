deribit_repeat_response_code = -1130

deribit_endpoint = "wss://test.deribit.com/ws/api/v2"

deribit_marginCoins = ["BTC", "ETH", "USDC", "USDT", "EURR"]


deribit_jsonrpc_params_map = {
    "depth" : lambda symbol, kind : {"instrument_name" : symbol, "depth" : 1000},
    "oifunding" : lambda currency, kind : {"currency" : currency, "kind" : kind}
}

deribit_jsonrpc_channel_map = {
    "depth" : "public/get_order_book",
    "oifunding" : "public/get_book_summary_by_currency",
    "ws" : "public/subscribe",
}

deribit_instType_map = {
    "spot" : "spot",
    "perpetual" : "future",
    "future" : "future",
    "option" : "option"
}

deribit_ws_params_map = {
    "depth" : lambda symbol, kind: {"channels": [f"book.{symbol}.none.20.agg2"]},
    "trades" : lambda symbol, kind: {"channels": [f"trades.{symbol}.agg2"]},
    "tradesagg" : lambda symbol, kind: {"channels": [f"trades.{kind}.{symbol}.agg2"]}
}


def deribit_get_symbol_name(symbol):
    return symbol.replace("-", "").lower()

