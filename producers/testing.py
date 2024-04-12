from clients import binance
import asyncio
import ijson

# async def binance_api_oioption_oi_option(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
#     """
#         https://www.binance.com/en/support/faq/binance-options-contract-specifications-cdee5d43b70d4d2386980d41786a8533
#     """
#     data = [d for l in data.values() for d in l if isinstance(d, dict)]
#     ddd = {}
#     for instData in data:
#         symbol_list = instData.get("symbol").split("-")
#         symbol = symbol_list[0]
#         oi = float(instData.get("sumOpenInterest"))
#         strike = float(symbol_list[2])
#         days_left = binance_option_timedelta(symbol_list[1])
#         if float(days_left) >= 0 and oi > 0:
#             side = symbol_list[-1]
#             index_price = market_state.get(f"{symbol}USDT@spot@binance")
#             msid = f"{instData.get('symbol')}@option@binance"
#             option_data = {"symbol" : instData.get("symbol"),
#                                                     "side" :  side, "index_price" : index_price, 
#                                                     "strike" : strike, "underlying_price" : index_price, "oi" : oi, "days_left" : days_left}
#             ddd[msid] = option_data
#     ddd["timestamp"] = self.process_timestamp_no_timestamp()
#     return ddd

from datetime import datetime

def binance_str_to_date(date_str):
    date_format = "%y%m%d"
    date_obj = datetime.strptime(date_str, date_format)
    return date_obj  

def binance_option_timedelta(date_str):
    target_date = binance_str_to_date(date_str)
    today = datetime.now()
    difference = int((target_date - today).days)
    return difference 

def binance_api_oioption_oi_option(data:str, market_state:dict, connection_data:dict, *args, **kwargs):
    return_data = {}
    for prefix, event, value in ijson.parse(data):
        if prefix == "item.symbol":
            option_data = value.split("-")
            msid = f"{''.join(value)}@option@binance"
            return_data[msid] = {}
            return_data[msid]["symbol"] = value
            return_data[msid]["strike"] = float(option_data[2])
            return_data[msid]["days_left"] = binance_option_timedelta(option_data[1])
        if prefix == "item.sumOpenInterest":
            return_data[msid]["oi"] = float(value)
    return_data = {x : y for x, y in return_data.items() if y.get("days_left") >= 0}
    return_data[msid]["timestamp"] = "ur code here"
    market_state.update(return_data)

market_state = {}

async def main():
    data = await binance.binance_aiohttpFetch("option", "oi", "BTC", specialParam="240419")
    return binance_api_oioption_oi_option(data, market_state, {})

asyncio.run(main())    

print(len(market_state))




