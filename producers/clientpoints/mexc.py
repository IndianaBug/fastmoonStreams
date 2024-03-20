mexc_repeat_response_code = 0

mexc_api_endpoints = {
    "spot" : "https://api.mexc.com",
    "perpetual" : "https://contract.mexc.com",
}

mexc_ws_endpoints = {
    "spot" : "wss://wbs.mexc.com/ws",
    "perpetual" : "wss://contract.mexc.com/edge",
}


# Symbols as in mexc.info
mexc_api_basepoints = {
    "spot" : {
        "depth" : "/api/v3/depth",     #?symbol=BTCUSDT&limit=5000
    },
    "perpetual" : {
        "depth" : "/api/v1/contract/depth", #?symbol=BTC_USDT
    }
}

def mexc_api_parseParams(instType, objective, symbol):
      


mexc_ws_stream_map = {
    "trades" : {
        "spot" : "deals",
        "perpetual" : "deal",
    },
    "depth" : "depth",                 
    "oifunding" : "ticker"  
}


def mexc_build_ws_msg(instType, objective, symbol):
        obj = mexc_ws_stream_map.get(objective) if objective!="trades" else mexc_ws_stream_map.get(objective).get(instType)
        if instType == "spot":
             if obj == "depth":
                   obj = f"increase.{obj}"
             msg = {
                    "method": "SUBSCRIPTION",
                    "params": [
                        f"spot@public.{obj}.v3.api@{symbol}"
                    ]
                }
        if instType == "perpetual":
             msg = {
                "method": f"sub.{obj}",
                "param":{
                    "symbol": symbol
                }
            }
        return msg
