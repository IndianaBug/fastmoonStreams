import time


gateio_repeat_response_code = 0

gateio_api_endpoint =  "https://api.gateio.ws/api/v4"

gateio_api_endpoint_alt = "https://fx-api-testnet.gateio.ws/api/v4"

gateio_api_headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

gateio_basepoints = {
    "spot" : {
        "depth" : "",
        "trades" : "",
    },
    "perpetual" : {
        "LinearPerpetual" : {
          "depth" : "/futures/usdt/order_book",   # not only usdt may be another coin  # contract=BTC_USDT" limit=1000
          "trades" : "/futures/usdt/trades",      # contract , limit=1000max
          "funding" : "/futures/usdt/funding_rate", # contract limit=1
          "oi" : "/futures/usdt/contract_stats",       # https://www.gate.io/docs/developers/apiv4/en/#futures-insurance-balance-history
          "tta" : "/futures/usdt/contract_stats",
          "liquidations" : "/futures/usdt/liq_orders"     # https://www.gate.io/docs/developers/apiv4/en/#futures-stats
        },
        "InversePerpetual" : {
          "depth" : "/futures/usdt/order_book",   # not only usdt may be another coin  # contract=BTC_USDT" limit=1000
          "trades" : "/futures/usdt/trades",      # contract , limit=1000max
          "funding" : "/futures/usdt/funding_rate", # contract limit=1
          "oi" : "/futures/usdt/contract_stats",       # https://www.gate.io/docs/developers/apiv4/en/#futures-insurance-balance-history
          "tta" : "/futures/usdt/contract_stats",
          "liquidations" : "/futures/usdt/liq_orders"     # https://www.gate.io/docs/developers/apiv4/en/#futures-stats
        },
    },
     "future" : {
         "depth" : "/delivery/usdt/order_book",  # 'contract=BTC_USDT_20200814' limit=1000
         "trades" : "/delivery/usdt/trades",      # https://www.gate.io/docs/developers/apiv4/en/#futures-trading-history-2
         "oifunding" : "/delivery/usdt/tickers",   # https://www.gate.io/docs/developers/apiv4/en/#get-futures-candlesticks-2
     },
     "option" : {
         "depth" : "/options/order_book",   # contract interval limit string string intereger
         "trades" : "/options/trades",      # contract type, limit, from to (int64)
         "oi" : "/options/tickers",         # lists all open interests per underlying asset   underlying=BTC_USDT
     },
}


gateio_ws_endpoint = {
    "spot" : "https://api.gateio.ws/api/v4",
    "perpetual" : lambda settle : f"wss://fx-ws.gateio.ws/v4/ws/{settle}",
    "future" : lambda settle : f"wss://fx-ws.gateio.ws/v4/ws/delivery/{settle}"
    }

gateio_ws_map = {
    "spot" : {
        "trades" : "spot.trades",
        "depth" : "spot.order_book_update" # 2 args
    },
    "perpetual" : {
        "trades" : "futures.trades",       # just symbol
        "depth" : "futures.order_book_update",   # not only, 3 args
        "oifunding" : "futures.tickers"        # just symbol
    },
    "future" : {
        "trades" : "futures.trades",
        "depth" : "futures.order_book_update",
        "oifunding" : "futures.tickers"
    }
}

# SPOT 
# ws.send(json.dumps({
#     "time": int(time.time()),
#     "channel": "spot.order_book_update",
#     "event": "subscribe",  # "unsubscribe" for unsubscription
#     "payload": ["BTC_USDT", "100ms"]
# }))

# Perpetual
# ws.send('{"time" : 123456, "channel" : "futures.order_book_update",
#         "event": "subscribe", "payload" : ["BTC_USD", "1000ms", "20"]}')

def gateio_build_ws_message(instType, objective, symbol):
    obj = gateio_ws_map.get(instType).get(objective)
    msg = {
        "time": int(time.time()),
        "channel": obj,
        "event": "subscribe",  
        "payload": [symbol]
        }
    return msg





# # example WebSocket signature calculation implementation in Python
# import hmac, hashlib, json, time
# def gen_sign(channel, event, timestamp):
#     # GateAPIv4 key pair
#     api_key = 'YOUR_API_KEY'
#     api_secret = 'YOUR_API_SECRET'

#     s = 'channel=%s&event=%s&time=%d' % (channel, event, timestamp)
#     sign = hmac.new(api_secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
#     return {'method': 'api_key', 'KEY': api_key, 'SIGN': sign}


# request = {
#     'id': int(time.time() * 1e6),
#     'time': int(time.time()),
#     'channel': 'spot.orders',
#     'event': 'subscribe',
#     'payload': ["BTC_USDT", "GT_USDT"]
# }
# request['auth'] = gen_sign(request['channel'], request['event'], request['time'])
# print(json.dumps(request))