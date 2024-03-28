import time


gateio_repeat_response_code = 0

gateio_api_endpoint =  "https://api.gateio.ws/api/v4"

gateio_api_endpoint_alt = "https://fx-api-testnet.gateio.ws/api/v4"

gateio_api_headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

gateio_basepoints = {
    "spot" : {
        "depth" : "/spot/order_book",
        "trades" : "/spot/trades",
    },
    "perpetual" : {
        "LinearPerpetual" : {
          "depth" : "/futures/usdt/order_book",   
          "trades" : "/futures/usdt/trades",     
          "funding" : "/futures/usdt/funding_rate", 
          "oi" : "/futures/usdt/contract_stats",           # the same as tta 
          "tta" : "/futures/usdt/contract_stats",          # the same as oi
          "liquidations" : "/futures/usdt/liq_orders"     
        },
        "InversePerpetual" : {
          "depth" : "/futures/btc/order_book",   
          "trades" : "/futures/btc/trades",      
          "funding" : "/futures/btc/funding_rate",
          "oi" : "/futures/btc/contract_stats",       # the same as tta 
          "tta" : "/futures/btc/contract_stats",      # the same as oi
          "liquidations" : "/futures/usdt/liq_orders"    
        },
    },
     "future" : {
         "depth" : "/delivery/usdt/order_book",  
         "trades" : "/delivery/usdt/trades",
         "oi" : "/delivery/usdt/tickers",      
     },
     "option" : {
         "depth" : "/options/order_book",   
         "trades" : "/options/trades",      
         "oi" : "/options/tickers",     
     },
}


gateio_basepoints_standard_params = {
    "spot" : {
        "depth" : lambda symbol, interval : {"currency_pair" : symbol, "limit" : 300},
        "trades" : lambda symbol, interval : {"currency_pair" : symbol, "from" : int(time.time()-interval), "to" : int(time.time())}, 
    },
    "perpetual" : {
          "depth" : lambda symbol, interval : {"contract" : symbol, "limit" : 300},
          "trades" : lambda symbol, interval : {"contract" : symbol, "from" : int(time.time()-interval), "to" : int(time.time())}, 
          "funding" : lambda symbol, interval : {"contract" : symbol, "limit" : 1},
          "oi" : lambda symbol, interval : {"contract" : symbol, "from" : int(time.time()-interval), "to" : int(time.time())}, 
          "tta" : lambda symbol, interval : {"contract" : symbol, "from" : int(time.time()-interval), "to" : int(time.time())}, 
          "liquidations" : lambda symbol, interval : {"contract" : symbol, "from" : int(time.time()-interval), "to" : int(time.time())}, 
    },
     "future" : {
         "depth" : lambda symbol, interval : {"contract" : symbol, "limit" : 300},
         "trades" : lambda symbol, interval : {"contract" : symbol, "from" : int(time.time()-interval), "to" : int(time.time())}, 
         "oi" :lambda symbol, interval : {"contract" : symbol}, # if no params provided, fetches for everyone
     },
     "option" : {
         "depth" : lambda symbol, interval : {"contract" : symbol, "limit" : 300},
         "trades" : lambda symbol, interval : {"contract" : symbol, "from" : int(time.time()-interval), "to" : int(time.time())},    # if not provided, fetches every trades
         "oi" : lambda symbol, interval : {"underlying" : symbol},   # ticker snap of all options belonging to underlying asset
     },
}


def gateio_get_api_standard_params(instType, objective, symbol, interval=None):
    params = gateio_basepoints_standard_params.get(instType).get(objective)(symbol, interval)
    return params


gateio_ws_endpoints = {
    "spot" : "https://api.gateio.ws/api/v4",
    "perpetual" : {
        "LinearPerpetual" : "wss://fx-ws.gateio.ws/v4/ws/usdt",
        "InversePerpetual" : "wss://fx-ws.gateio.ws/v4/ws/btc",
    },
    "future" : "wss://fx-ws.gateio.ws/v4/ws/delivery/usdt",
    "option" : "wss://op-ws.gateio.live/v4/ws"
    }

gateio_ws_channel_map = {
    "spot" : {
        "trades" : "spot.trades",
        "depth" : "spot.order_book_update" 
    },
    "perpetual" : {
        "trades" : "futures.trades",       
        "depth" : "futures.order_book_update",  
        "oifunding" : "futures.tickers",
        "liquidations" : "futures.trades",          # the same as for tradeds       
    },
    "future" : {
        "trades" : "futures.trades",
        "depth" : "futures.order_book_update",
        "oifunding" : "futures.tickers",
        "liquidations" : "futures.trades",          # Expiry futures have no liquidations
    },
    "option" : {
        "trades" : "options.ul_trades", 
        "depth" : "futures.order_book_update",
        "oi" : "options.ul_tickers"
    },
}

gateio_ws_payload_map = {
    "spot" : {
        "trades" : lambda symbol : [symbol],
        "depth" : lambda symbol : [symbol, "1000ms"]
    },
    "perpetual" : {
        "trades" : lambda symbol : [symbol],             
        "depth" : lambda symbol : [symbol, "1000ms", "20"], 
        "oifunding" : lambda symbol : [symbol],  
        "liquidations" : lambda symbol : [symbol],    
    },
    "future" : {
        "trades" : lambda symbol : [symbol],             
        "depth" : lambda symbol : [symbol, "1000ms", "20"],                     # MAYBE IN BULK
        "oifunding" : lambda symbol : [symbol],   
    },
    "option" : {
        "trades" : lambda symbol : [symbol],                                     # use this for all trades
        "depth" : lambda symbol : [symbol, "1000ms", "20"],                                    # MAYBE IN BULK
        "oi" : lambda symbol : [symbol],     # use this for all          
    },
}

def gateio_get_basepoint(instType, objective, marginType, interval=None):
    """
        interval : seconds of the data to snap on
    """
    if marginType != None:
        basepoint = gateio_basepoints.get(instType).get(marginType).get(objective)
    else:
        basepoint = gateio_basepoints.get(instType).get(objective)
    return basepoint

def gateio_get_api_standard_params(instType, objective):
    params = gateio_basepoints_standard_params.get(instType).get(objective)
    return params

def gateio_build_ws_message(instType, objective, symbol):
    channel = gateio_ws_channel_map.get(instType).get(objective)
    payload = gateio_ws_payload_map.get(instType).get(objective)
    msg = {
        "time": int(time.time()),
        "channel": channel,
        "event": "subscribe",  
        "payload": payload(symbol)
        }
    return msg

def gateio_get_ws_url(instType, objective, marginType, symbol):
    if marginType != None:
        url = gateio_ws_endpoints.get(instType).get(marginType)
    else:
        url = gateio_ws_endpoints.get(instType)
    return url

def gateio_get_marginType(instType, symbol):
    if instType == "perpetual":
        marginType = "LinearPerpetual" if "USDT" in symbol else "InversePerpetual"
    else:
        marginType = ""
    return marginType

def gateio_get_symbolname(symbol):
    return symbol.replace("_", "").lower()

def gateio_build_ws_message_all_Options(instType, objective, symbols):
    channel = gateio_ws_channel_map.get(instType).get(objective)
    payload = [[symbol, "1000", "20"] for symbol in symbols]
    msg = {
        "time": int(time.time()),
        "channel": channel,
        "event": "subscribe",  
        "payload": payload
        }
    return msg
