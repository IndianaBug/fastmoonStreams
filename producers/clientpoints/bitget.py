bitget_repeat_response_code = -1130

bitget_api_endpoint = "https://api.bitget.com"

bitget_productType_map = {
    "LinearPerpetual" : {
        "usdt" : "USDT-FUTURES", # productType=
        "usdc" : "USDC-FUTURES"
    },
    "InversePerpetual" : "COIN-FUTURES"
}

bitget_api_basepoints = {
    "spot" : {  
        "depth" : "/api/v2/spot/market/orderbook",  # symbol=BTCUSDT&type=step0&limit=150"
    },
    "perpetual" : {  
        "depth" : "/api/v2/mix/market/merge-depth", # ?productType=usdt-futures&symbol=BTCUSDT&limit=1000
    },
        }

# ws # 


bitget_ws_endpoint = "wss://ws.bitget.com/v2/ws/public"



bitget_stream_keys = {
        "trades" : "trade",
        "depth" : "books",
        "oifunding" : "ticker"
}

# Symbol and margin type mapping

def bitget_get_instrument(d):
    if "instId" in d:
        symbol = d.get("instId")
    if "symbol" in d:
        symbol = d.get("symbol")
    return symbol

def bitget_get_symbol_name(d):
    if "instId" in d:
        symbol = d.get("instId")
    if "symbol" in d:
        symbol = d.get("symbol")
    return symbol.replace("-", "").lower()

def bitget_get_marginType(instrument):
    if "USDT" in instrument:
        marginType = "LinearPerpetual"
    if "PERP" in instrument:
        marginType = "LinearPerpetual"
    if "USD" in instrument and "USDT" not in instrument:
        marginType = "InversePerpetual"
    return marginType

def bitget_get_marginCoin(instrument):
    if "USDT" in instrument:
        marginCoin = "usdt"
    if "PERP" in instrument:
        marginCoin = "usdc"
    if "USD" in instrument and "USDT" not in instrument:
        marginCoin = "any_except_usdc_usdt"
    return marginCoin

def bitget_get_productType(instType, marginType, marginCoin):
    productType = ""
    if instType == "perpetual":
        if marginCoin != "any_except_usdc_usdt":
            productType = bitget_productType_map.get(marginType).get(marginCoin)
        if marginCoin == "any_except_usdc_usdt":
            productType = bitget_productType_map.get(marginType)
    return productType