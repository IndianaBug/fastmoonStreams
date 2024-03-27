import re

binance_repeat_response_codes = [-1130, -4021]

binance_api_endpoints = {
                    "spot" : "https://api.binance.com",
                    "perpetual" : {
                        "LinearPerpetual" : "https://fapi.binance.com",
                        "InversePerpetual" : "https://dapi.binance.com"
                    },
                    "future" : {
                        "LinearFuture" : "https://fapi.binance.com",
                        "InverseFuture" : "https://dapi.binance.com"
                    },
                    "option" : "https://eapi.binance.com"
                }

binance_api_linear_types = {
                        "depth" : "/fapi/v1/depth",
                        "funding" : "/fapi/v1/fundingRate",
                        "oi" : "/fapi/v1/openInterest",
                        "tta" : "/futures/data/topLongShortAccountRatio",
                        "ttp" : "/futures/data/topLongShortPositionRatio",
                        "gta" : "/futures/data/globalLongShortAccountRatio",
                        }
binance_api_inverse_types = {
                        "depth" : "/dapi/v1/depth",
                        "funding" : "/dapi/v1/fundingRate",
                        "oi" : "/dapi/v1/openInterest",
                        "tta" : "/futures/data/topLongShortAccountRatio",
                        "ttp" : "/futures/data/topLongShortPositionRatio",
                        "gta" : "/futures/data/globalLongShortAccountRatio",
                        "oisum" : "/futures/data/openInterestHist"
                        }


binance_api_basepoints = {
                    "spot" :  {
                        "depth" : "/api/v3/depth",
                    },
                    "perpetual" : {
                        "LinearPerpetual" : binance_api_linear_types,
                        "InversePerpetual" : binance_api_inverse_types,
                    },
                    "future" : {
                        "LinearFuture" : binance_api_linear_types,
                        "InverseFuture" : binance_api_inverse_types
                    },
                    "option" : {
                        "oi" : "/eapi/v1/openInterest"
                                }                
                    }

binance_api_linear_params = {
                        "depth" : lambda symbol: {"symbol" : symbol, "limit" : 1000},
                        "funding" : lambda symbol: {"symbol" : symbol, "limit" : 1},
                        "oi" : lambda symbol: {"symbol" : symbol},
                        "tta" : lambda symbol: {"symbol" : symbol, "period" : "5m", "limit" : 1},
                        "ttp" : lambda symbol: {"symbol" : symbol, "period" : "5m", "limit" : 1},
                        "gta" : lambda symbol: {"symbol" : symbol, "period" : "5m", "limit" : 1},    # do also for expiry futures
                        }
binance_api_inverse_params = {
                        "depth" : lambda symbol: {"symbol" : symbol, "limit" : 1000},
                        "funding" : lambda symbol: {"symbol" : symbol, "limit" : 1},
                        "oi" : lambda symbol: {"symbol" : symbol},
                        "tta" : lambda symbol: {"pair" : symbol, "period" : "5m", "limit" : 1},
                        "ttp" : lambda symbol: {"pair" : symbol, "period" : "5m", "limit" : 1},
                        "gta" : lambda symbol: {"pair" : symbol, "period" : "5m", "limit" : 1},
                        }


binance_api_params_map = {
                    "spot" :  {
                        "depth" : lambda symbol: {"symbol" : symbol, "limit" : 1000},
                    },
                    "perpetual" : {
                        "LinearPerpetual" : binance_api_linear_params,
                        "InversePerpetual" : binance_api_inverse_params,
                    },
                    "future" : {
                        "LinearFuture" : binance_api_linear_params,
                        "InverseFuture" : binance_api_inverse_params
                    },
                    "option" : {
                        "oi" : lambda underlyingAsset: {"underlyingAsset" : underlyingAsset, "expiration" : None},
                                },                
                    }

binance_future_contract_types = ["CURRENT_QUARTER", "NEXT_QUARTER"] # for the sum of open interest

# WS # 

binance_ws_endpoints = {
                    "spot" : "wss://stream.binance.com:9443/ws",
                    "perpetual" : {
                        "LinearPerpetual" : "wss://fstream.binance.com/ws",
                        "InversePerpetual" : "wss://dstream.binancefuture.com/ws"
                    },
                    "future" : {
                        "LinearFuture" : "wss://fstream.binance.com/ws",
                        "InverseFuture" : "wss://dstream.binancefuture.com/ws"
                    },
                    "option" : "wss://nbstream.binance.com/eoptions/ws",
                    "Linear" : "wss://fstream.binance.com/ws",
                    "Inverse" :  "wss://dstream.binancefuture.com/ws"
                }


ws_derivatepayload = {
            "trades" : lambda symbol : f"{symbol}@aggTrade",
        "depth" : lambda symbol : f"{symbol}@depth@500ms",
        "liquidations" : lambda symbol : f"{symbol}@forceOrder",
}

binance_ws_payload_map = {
    "spot" : {
        "trades" : lambda symbol : f"{symbol}@aggTrade",
        "depth" : lambda symbol : f"{symbol}@depth@1000ms",
    },
    "perpetual" : ws_derivatepayload,
    "future" : ws_derivatepayload,
    "option" : {
        "trades" : lambda underlyingAsset : f"{underlyingAsset}@trade",
    }
}

def binance_instType_help(symbol):
    return "Linear" if "USDT" in symbol else "Inverse"

def binance_get_symbol_name(symbol):
    return symbol.lower().replace("_", "")

usdMarginCoins = ["USDT", "USDC"]

def binance_get_marginType(instType, symbol):
    marginType=None
    if instType == "perpetual":
        marginType = "LinearPerpetual" if len([element for element in usdMarginCoins if element in symbol]) > 0 else "InversePerpetual"
    if instType == "future":
        marginType = "LinearFuture" if len([element for element in usdMarginCoins if element in symbol]) > 0  else "InverseFuture"
    return marginType


def binance_get_futperphelp(symbol):
    """
        helper for special we method
    """
    instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
    marginType = binance_get_marginType(instType, symbol)
    return instType, marginType

def split_list(lst, n):
    quotient = len(lst) // n
    remainder = len(lst) % n
    splits = []
    start = 0
    for i in range(n):
        length = quotient + (1 if i < remainder else 0)
        splits.append(lst[start:start+length])
        start += length
    return splits


def binance_build_ws_messages_optionTrades(expirations, number_websockets=4):
    """
        updates ar epushed every 50ms 
        make sure its not more than 100 updates per second
    """
    channels = [f"{expiration}@trade" for expiration in expirations]
    channels_splited = split_list(channels, number_websockets)
    messages = []
    for channels in channels_splited:
        msg = {
                "method": "SUBSCRIBE",
                "params": channels,
                "id": 1
                }
        messages.append(msg)
    return messages


def binance_build_ws_message_optionDepth(symbols, levels=100, number_websockets=20):
    """
        possible levels : 10, 20, 50, 100.
        number_websockets : whot many symbols to stream in a single websocket?
        binance wont allow you to stream more than 10?-100 messages per seccond
        THerefore, use like 50 or 100. There are around 2k options on binance
    """
    available_symbols = ""
    channels = [f"{symbol}@depth{levels}@1000ms" for symbol in available_symbols]
    channels_splited = split_list(channels, number_websockets)
    messages = []
    for channels in channels_splited:
        msg = {
                "method": "SUBSCRIBE",
                "params": channels,
                "id": 1
                }
        messages.append(msg)
    return messages

binance_stream_keys = {
    "liquidations" : "forceOrder",
    "trades" : "aggTrade",
    "depth" : "depth",
}
