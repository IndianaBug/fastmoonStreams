import time

okx_repeat_response_code = -1041

okx_api_endpoint = "https://www.okx.com"

okx_api_instType_map = {
                        "spot" : "SPOT",
                        "perpetual" : "SWAP",
                        "future" : "FUTURES",
                        "option" : "OPTION",
                        "margin" : "MARGIN"
                    }

def create_minimal_query(ccy, period="1H"):
    current_time = int(round(time.time() * 100))
    if period == "5m":
        max_begin = current_time - (2 * 24 * 60 * 60) * 100  # Limit: 2 days
    elif period == "1H":
        max_begin = current_time - (30 * 24 * 60 * 60) * 100  # Limit: 30 days
    elif period == "1D":
        max_begin = current_time - (180 * 24 * 60 * 60) * 100  # Limit: 180 days
    else:
        raise ValueError(f"Invalid period: {period}")
    begin = min(current_time - 1200 * 100, max_begin)

    return {
        "ccy": ccy,
        "begin": begin,
        "end": current_time,
        "period": period
    }


okx_api_basepoints = {
                        "gta" : "/api/v5/rubik/stat/contracts/long-short-account-ratio", 
                        "oitotal" : "/api/v5/rubik/stat/contracts/open-interest-volume",
                        "oi" : "/api/v5/public/open-interest",
                        "funding" : "/api/v5/public/funding-rate",
                        "depth" : "/api/v5/market/books-full",                            
                    }

okx_api_params_map = {
                        "gta" : lambda ccy: {"ccy" : ccy},# "begin" : str(int(round((time.time()-610)*100))), "end" : str(int(round(time.time()*100)))},
                        "oitotal" : lambda ccy: {"ccy" : ccy, "period" : "5m"},   
                        "oi" : lambda instType, instId: {"instType" : instType, "instId" : instId},   
                        "funding" : lambda instId: {"instId" : instId},
                        "depth" : lambda instId: {"instId" : instId, "sz" : "1000"},                    
                    }

# ws # 


okx_ws_endpoint = "wss://ws.okx.com:8443/ws/v5/public" 

# make liquidations for SWAP and FUTURES and options at once
# FILTER ONLY BTC TICKERS

okx_ws_objective_map = {
    "liquidations" : "liquidation-orders",      #  # 'channel': 'liquidation-orders', 'instType': 'SWAP' They have only general stream
    "trades" : "trades",         # no aggregation
    "depth" : "books",
    "oi" : "open-interest",
    "funding" : "funding-rate",
    "optionTrades" : "option-trades"           # single channel for all option trades
}

def okx_get_instrument_name(symbol):
    return symbol.replace("-", "").lower()



def get_okx_marginType(instType, symbol):
    marginType = ""
    if instType in ["future", "perpetual"]:
        if "USD" in symbol and "USDT" not in symbol and "USDC" not in symbol:
            marginType = "linear"
        elif "USD" in symbol:
            marginType = "inverse"
        else:
            marginType = instType
    return marginType
