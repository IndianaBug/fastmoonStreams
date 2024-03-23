import time

okx_repeat_response_code = -1041

okx_api_endpoint = "https://www.okx.com"

okx_api_instType_map = {
                        "spot" : "SPOT",
                        "perpetual" : "SWAP",
                        "future" : "FUTURE",
                        "option" : "OPTION",
                        "margin" : "MARGIN"
                    }

okx_api_basepoints = {
                        "gta" : "/api/v5/rubik/stat/contracts/long-short-account-ratio", 
                        "oifutperp" : "/api/v5/rubik/stat/contracts/open-interest-volume",
                        "oioption" : "/api/v5/public/open-interest",
                        "funding" : "/api/v5/public/funding-rate",
                        "depth" : "/api/v5/market/books-full",                            
                    }

okx_api_params_map = {
                        "gta" : lambda ccy: {"ccy" : ccy,  "period" : "5m"},
                        "oifutperp" : lambda ccy: {"ccy" : ccy, "period" : "5m"},   
                        "oioption" : lambda instType, instFamily: {"instType" : instType, "instFamily" : instFamily},   
                        "funding" : lambda instId: {"instId" : instId},
                        "depth" : lambda instId: {"instId" : instId, "sz" : "1000"},                    
                    }

# ws # 


okx_ws_endpoint = "wss://ws.okx.com:8443/ws/v5/public" 

# make liquidations for SWAP and FUTURES and options at once
# FILTER ONLY BTC TICKERS

okx_ws_objective_map = {
    "liquidations" : "liquidation-orders",      #  # 'channel': 'liquidation-orders', 'instType': 'SWAP' They have only general stream
    "trades" : "trades-all",         # no aggregation
    "depth" : "books",
    "oi" : "open-interest",
    "funding" : "funding-rate",
    "optionTrades" : "option-trades"           # single channel for all option trades
}
def okx_build_ws_message(instType=None, objective=None, instFamily=None, symbol=None):
    parsed_objective = okx_ws_objective_map.get(objective)
    if instType != None and instFamily != None:
        parsef_instType = okx_api_instType_map.get(instType)
        msg = {
                "op": "subscribe",
                "args": [{
                    "channel": parsed_objective,
                    "instType": parsef_instType, 
                    "instFamily": instFamily,    
                }]
            }
    if instType != None and instFamily == None:
        parsef_instType = okx_api_instType_map.get(instType)
        msg = {
                "op": "subscribe",
                "args": [{
                    "channel": parsed_objective,
                    "instType": parsef_instType, 
                }]
            }
    if symbol !=  None:
        msg = {
                "op": "subscribe",
                "args": [{
                    "channel": parsed_objective,
                    "instId": symbol, 
                }]
            }
    return msg

def okx_get_instrument_name(symbol):
    return symbol.replace("-", "").lower()