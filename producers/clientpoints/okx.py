
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
                        # ?ccy=BTC&period=5m  They give only general GTA                                                                                         #  Note no category
                        "oi" : "/api/v5/public/open-interest"                            
                        # instType=OPTION&instFamily=BTC-USD"
                    }

# ws # 


okx_ws_endpoint = "wss://ws.okx.com:8443/ws/v5/public" 


okx_stream_keys = {
    "liquidations" : "liquidation-orders",      #  # 'channel': 'liquidation-orders', 'instType': 'SWAP' They have only general stream
    "trades" : "trades",
    "depth" : "books",
    "oi" : "open-interest",
    "funding" : "funding-rate"
}


def okx_get_symbol_name(d):
    if "ccy" in d:
        symbol = d.get("ccy")
    if "instId" in d:
        symbol = d.get("instId")
    if "instFamily" in d:
        symbol = d.get("instFamily")
    if "symbol" in d:
        symbol = d.get("symbol")
    return symbol.replace("-", "").lower()