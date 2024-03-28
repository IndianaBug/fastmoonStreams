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
            "LinearPerpetual" : "wss://api.hbdm.vn/linear-swap-ws",
            "InversePerpetual" : "wss://api.hbdm.vn/swap-ws"
        },
        "future" : {
            "LinearFuture" : "wss://api.hbdm.vn/linear-swap-ws",
            "InverseFuture" : "wss://api.hbdm.vn/ws"
        }
    },
    "incremental" : {
        "spot" : "wss://api-aws.huobi.pro/feed"
    }
}


htx_api_basepoints = {
    "spot" : {
        "depth" : "/market/depth",      
    },
    "perpetual" : {
        "LinearPerpetual" : {
            "info" : "/linear-swap-api/v1/swap_contract_info",
            "oi" : "/linear-swap-api/v1/swap_his_open_interest",
            "tta" : "/linear-swap-api/v1/swap_elite_account_ratio",              
            "ttp" : "/linear-swap-api/v1/swap_elite_position_ratio",
            "funding" : "/linear-swap-api/v1/swap_batch_funding_rate"             
        },
        "InversePerpetual" : {
            "info" : "/swap-api/v1/swap_contract_info",
            "oi" : "/swap-api/v1/swap_open_interest",                           
            "tta" : "/swap-api/v1/swap_elite_account_ratio",                  
            "ttp" : "/swap-api/v1/swap_elite_position_ratio",                  
            "funding" : "/swap-api/v1/swap_batch_funding_rat"             
        },
    },
    "future" : {     
        "LinearFuture" : {
            "info" : "/linear-swap-api/v1/swap_contract_info",
            "oi" : "/linear-swap-api/v1/swap_his_open_interest",
            "tta" : "/linear-swap-api/v1/swap_elite_account_ratio",              
            "ttp" : "/linear-swap-api/v1/swap_elite_position_ratio",
        },                                                              
        "InverseFuture" : {   
            "info" : "/linear-swap-api/v1/swap_contract_info",                                                    
            "oi" : "/api/v1/contract_his_open_interest",                           
            "tta" : "/api/v1/contract_elite_account_ratio",                      
            "ttp" : "/api/v1/contract_elite_position_ratio"
        },
    }
}

inverse_future_contract_types = ["this_week","next_week","quarter"]

htx_api_params = {
    "spot" : {
        "depth" : lambda symbol : {"symbol" : symbol, "depth" : 20, "type" : "spet0"},      
    },
    "perpetual" : {
        "LinearPerpetual" : {
            "info" : {"business_type" : "all"},  
            "oi" :  lambda symbol : {"pair" : symbol, "business_type" : "all"},      # gets all OIs of Linear Futures            
            "tta" : lambda symbol : {"contract_code" : symbol, "period" : "5min"},   # availabe BTC-USDT, BTC-USDT-FUTURES           
            "ttp" : lambda symbol : {"contract_code" : symbol, "period" : "5min"},   # availabe BTC-USDT, BTC-USDT-FUTURES 
            "funding" : lambda symbol : {"contract_code" : symbol}                
        },
        "InversePerpetual" : {
            "info" : {},
            "oi" :  lambda symbol : {"contract_code" : symbol},                    
            "tta" : lambda symbol : {"contract_code" : symbol, "period" : "5min"},    # BTC-USD                 
            "ttp" : lambda symbol : {"contract_code" : symbol, "period" : "5min"},    # BTC-USD
            "funding" : lambda symbol : {"contract_code" : symbol}          
        },
    },
    "future" : {
        "LinearFuture" : {   
            "info" : {"business_type" : "all"},  
            "oi" :  lambda symbol : {"pair" : symbol, "business_type" : "all"},      # gets all OIs of Linear Futures            
            "tta" : lambda symbol : {"contract_code" : symbol, "period" : "5min"},   # availabe BTC-USDT, BTC-USDT-FUTURES           
            "ttp" : lambda symbol : {"contract_code" : symbol, "period" : "5min"},   # availabe BTC-USDT, BTC-USDT-FUTURES 
        },                                                                 
        "InverseFuture" : { 
            "info" : {},                                                        
            "oi" :  lambda symbol, contract_type : {"symbol" : symbol, "contract_type" : contract_type},                    
            "tta" : lambda symbol : {"symbol" : symbol, "period" : "5min"},         # Only Underlying symbol (BTC)       
            "ttp" : lambda symbol : {"symbol" : symbol, "period" : "5min"},         # Only Underlying symbol (BTC) 
        },
    }
}

def htx_get_marginType(instType, instrument):
    if instType == "perpetual":
        marginType = "LinearPerpetual" if "USDT" in instrument else "InversePerpetual"
    if instType == "future":
        marginType = "LinearFuture" if "USDT" in instrument else "InverseFuture"
    return marginType

htx_ws_stream_map = {
    "trades" : "market.$symbol.trade.detail  ",   
    "depth" : "market.depth.$symbol.size_20.high_freq",        
    "liquidations" : "public.$contract_code.liquidation_orders",         
    "funding" : "public.$contract_code.funding_rate"  
}


def htx_symbol_name(symbol):
    return symbol.lower().replace("-", "")


def htx_get_ws_url(instType, objective, marginType=None):
    if instType=="spot" and objective == "depth":
        return htx_ws_endpoints.get("incremental").get(instType)
    else:
        return htx_ws_endpoints.get("not_incremental").get(instType).get(marginType)


