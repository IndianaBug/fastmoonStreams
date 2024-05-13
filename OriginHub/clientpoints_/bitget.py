bitget_repeat_response_code = -1130

bitget_api_endpoint = "https://api.bitget.com"

bitget_productType_map = {
    "perpetual" : {
        "LinearPerpetual" : {
            "usdt" : "USDT-FUTURES", 
            "usdc" : "USDC-FUTURES"
        },
        "InversePerpetual" : "COIN-FUTURES"
    },
    "spot" : "SPOT"
}

bitget_api_basepoints = {
    "spot" : {  
        "depth" : "/api/v2/spot/market/merge-depth",  # symbol=BTCUSDT&type=step0&limit=150"
    },
    "perpetual" : {  
        "depth" : "/api/v2/mix/market/merge-depth", # ?productType=usdt-futures&symbol=BTCUSDT&limit=1000
        "oi" : "/api/v2/mix/market/open-interest",
        "funding" : "/api/v2/mix/market/history-fund-rate",
    },
        }

bitget_api_params_map = {
    "perpetual" : {
        "depth" : lambda symbol, productType: {"symbol" : symbol, "productType" :  productType, "precision" : "scale0", "limit" : "max"},  
        "oi" : lambda symbol, productType: {"symbol" : symbol, "productType" :  productType},  
        "funding" : lambda symbol, productType: {"symbol" : symbol, "productType" :  productType, "pageSize" : "1"},   
    },
    "spot" : {
        "depth" : lambda symbol, productType=None: {"symbol" : symbol, "precision" : "scale0", "limit" : "max"},  
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

def bitget_get_productType(instType, marginType, marginCoin):
    if instType == "spot":
        productType = bitget_productType_map.get(instType) 
    if instType == "perpetual" and marginType=="InversePerpetual":
        productType = bitget_productType_map.get(instType).get(marginType) 
    if instType == "perpetual" and marginType=="LinearPerpetual":
        productType = bitget_productType_map.get(instType).get(marginType).get(marginCoin)  
    return productType


def bitget_get_symbol_name(symbol):
    return symbol.replace("-", "").lower()

def bitget_get_marginType(instrument):
    marginType = ""
    if "USDT" in instrument:
        marginType = "LinearPerpetual"
    if "PERP" in instrument:
        marginType = "LinearPerpetual"
    if "USD" in instrument and "USDT" not in instrument:
        marginType = "InversePerpetual"
    return marginType

def bitget_get_marginCoin(instrument):
    marginCoin = "coinM"
    if "USDT" in instrument:
        marginCoin = "usdt"
    if "PERP" in instrument:
        marginCoin = "usdc"
    return marginCoin

bitget_productType_map = {
    "perpetual" : {
        "LinearPerpetual" : {
            "usdt" : "USDT-FUTURES", 
            "usdc" : "USDC-FUTURES"
        },
        "InversePerpetual" : "COIN-FUTURES"
    },
    "spot" : "SPOT"
}





def get_bitget_instType(params, instType):
    instrument, symbol_name, marginType, marginCoin, productType = bitget_get_variables(params, instType)
    if instType == "spot" :
        bitgetInstType = "SPOT"
    if instType == "perpetual" and marginType=="LinearPerpetual" and marginCoin == "usdt":
        bitgetInstType = "USDT-FUTURES"
    if instType == "perpetual" and marginType=="LinearPerpetual" and marginCoin == "usdc":
        bitgetInstType = "USDC-FUTURES"
    if instType == "perpetual" and marginType=="InversePerpetual":
        bitgetInstType = "COIN-FUTURES"
    return bitgetInstType