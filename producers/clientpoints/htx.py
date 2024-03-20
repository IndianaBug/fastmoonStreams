htx_repeat_response_code = 0

htx_api_endpoints = {
    "spot" : "https://api-aws.huobi.pro",
    "perpetual" : "https://api.hbdm.com",
    "future" : "https://api.hbdm.com"
}

htx_ws_endpoints = {
    "not_incremental" : {
        "spot" : "wss://api-aws.huobi.pro/ws",
        "perpetual" : {
            "LinearPerpetual" : "wss://api.hbdm.vn/linear-swap-ws"
        }
    },
    "incremental" : {
        "spot" : "wss://api-aws.huobi.pro/feed"
    }
}
# depth, funding, oi
htx_api_basepoints = {
    "spot" : {
        "depth" : "/market/depth",      # symbol, depth=20 type="step0"
    },
    "perpetual" : {
        "LinearPerpetual" : {
            "depth" : "/linear-swap-ex/market/depth",                            # ?contract_code=BTC-USDT&type=step0"
            "oi" : "/linear-swap-api/v1/swap_his_open_interest",                 # ?contract_code=BTC-USDT&period=60min&amount_type=2" 1:-cont，2:- cryptocurrency
            "tta" : "/linear-swap-api/v1/swap_elite_account_ratio",              # contract_code period=5m, 
            "ttp" : "/linear-swap-api/v1/swap_elite_position_ratio",             # contract_code period=5m, 
        },
        "InversePerpetual" : {
            "depth" : "/swap-ex/market/depth",                                  # contract_code=BTC-USD &type=step0"
            "oi" : "/swap-api/v1/swap_open_interest",                           # ?contract_code=BTC-USD" period=60min amount_type=2
            "tta" : "/swap-api/v1/swap_elite_account_ratio",                    # ?contract_code=BTC-USDT&period=1min&size=1,
            "ttp" : "/swap-api/v1/swap_elite_position_ratio",                   # ?contract_code=BTC-USDT&period=1min&size=1,

        },
    },
    "future" : {                                                                    # Contract code is supported to query data. e.g.: "BTC200918"(weekly), "BTC200925"(Bi-weekly),"BTC201225"(quarterly),"BTC210326"(next quarterly)
        "InverseFuture" : {                                                         # symbol "BTC_CW" BTC_NW BTC_CQ BTC_NQ type=step0
            "depth" : "/market/depth",                                              # ?symbol=BTC&contract_type=this_week&period=60min&amount_type=2"  Weekly:"this_week", Bi-weekly:"next_week", Quarterly:"quarter" Next Quarterly Contract: "next_quarter"
            "oi" : "/api/v1/contract_his_open_interest",                            # ?symbol=BTC&period=60min"
            "tta" : "/api/v1/contract_elite_account_ratio",                         # ?symbol=BTC&period=60min"
        },
        "LinearFuture" : {
            "depth" : "/linear-swap-ex/market/depth",                               # The same but there are nofutures therefore forget it
            "oi" : "/linear-swap-api/v1/swap_his_open_interest",                 
            "tta" : "/linear-swap-api/v1/swap_elite_account_ratio",              
            "ttp" : "/linear-swap-api/v1/swap_elite_position_ratio",
        },
    }
}

def htx_get_marginType(instrument):
    if "USD" in instrument and "USDT" not in instrument:
        return "InversePerpetual"
    if "USDT" in instrument :
        return "LinearPerpetual"
    if "USD" not in instrument :
        return "InverseFuture"


def htx_parse_params(objective, instType, marginType, symbol, futuresTimeHorizeon:int=None):
    """
        futuresTimeHorizeon :
            0 thisweek
            1- nex week
            2- this quarter
            3-next quarter
    """
    htx_InverseFuture_quarters_map = {
        "depth" : ["CW", "NW", "CQ", "NQ"],
        "oi" : ["this_week", "next_week", "quarter", "next_quarter"]
    }
    params = {}
    if instType == "spot" or (instType=="future" and marginType =="InverseFuture"):
        params["symbol"] = symbol
    if (instType=="perpetual" and marginType =="LinearPerpetual") or (instType=="future" and marginType =="LinearFuture") or (instType=="perpetual" and marginType =="InversePerpetual"):
        params["contract_code"] = symbol
    if objective == "depth":
        params["type"] = "step0"
        if (instType=="future" and marginType =="InverseFuture"):
            s = htx_InverseFuture_quarters_map.get('depth')[futuresTimeHorizeon]
            params["symbol"] = f"{params['symbol']}_{s}"
    if objective == "oi":
        params["period"] = "60min"
        params["amount_type"] = "2"
        if (instType=="future" and marginType =="InverseFuture"):
            s = htx_InverseFuture_quarters_map.get('oi')[futuresTimeHorizeon]
            params["contract_type"] = s
    if objective == "tta" or objective == "ttp":
        params["period"] = "60min"
    return params


htx_ws_stream_map = {
    "trades" : "market.$symbol.trade.detail  ",   
    "depth" : "market.depth.$symbol.size_20.high_freq ",        
    "liquidations" : "public.$contract_code.liquidation_orders",         
    "funding" : "public.$contract_code.funding_rate"  
}

htx_basecoins = ["BTC", "ETH", "TRX"]   # update via info.htx_info("future.InverseFuture")

htx_InverseFuture_quarters_map = {
    "depth" : ["BTC_CW", "BTC_NW", "BTC_CQ," "BTC_NQ"],
    "oi" : ["this_week", "next_week", "quarter", "next_quarter"]
} 


def htx_symbol_name(symbol):
    return symbol.lower().replace("-", "")

def htx_get_ws_topic(instType, objective, symbol):
    if instType == "spot" and objective=="depth":
        msg = {
            "sub": f"market.{symbol}.depth.size_20.high_freq",
            "data_type":"incremental",
            "id": generate_random_integer(10)
            }
    else:
        topic = htx_ws_stream_map.get(objective).split(".")
        topic[1] = symbol
        msg = {
            "sub": f"market.{symbol}.depth.size_20.high_freq",
            "id": generate_random_integer(10)
            }
    return msg

def kucoin_build_ws_message_f(stream):
    msg = {
            "sub": stream,
            "id":"id1"
            }
    return msg

def kucoin_build_ws_message_spot_depth(symbol):
    msg = {
            "sub": f"market.{symbol}.depth.size_20.high_freq",
            "data_type":"incremental",
            "id": "id1"
            }
    return msg
