data = "/workspaces/fastmoonStreams/jsondata/raw/api/deribit/deribit_api_future_oifunding_btc.json"
import ijson

def deribit_api_perpetual_future_oi_funding_oifunding(data:str, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
    msids = []
    symbols = []
    prices = []
    ois = []
    this_symbol = ""
    fundings = {}
    for prefix, event, value in ijson.parse(data):
        if prefix == "item.result.item.instrument_name":
            if value != None:
                this_symbol = value
                instType = "future" if any(char.isdigit() for char in value.split("-")[-1]) else "perpetual"
                msids.append(f"{value}@{instType}@deribit")
                symbols.append(value)                
        if prefix == "item.result.item.mid_price":
            if value != None:
                prices.append(float(value))
        if prefix == "item.result.item.open_interest":
            if value != None:
                ois.append(float(value))
        
    counter_2 = 0
    for prefix, event, value in ijson.parse(data):
        if prefix == "item.result.item.funding_8h":
            instType = "future" if any(char.isdigit() for char in symbols[counter_2].split("-")[-1]) else "perpetual"
            if value != None:
                fundings[f"{symbols[counter_2]}@{instType}@deribit"] = {}
                fundings[f"{symbols[counter_2]}@{instType}@deribit"]["funding"] = float(value)
                counter_2 += 1
        
    instruments_data = {x : {} for x in msids}
    for i, msid in enumerate(msids):
        instruments_data[msid] = {
            "symbol": symbols[i],
            "oi": ois[i],
        }
            
    for key, item in fundings.items():
        for key_2, fun in item.items():
            if key!=None and key_2!=None:
                instruments_data[key][key_2] = fun

    for msid, data in instruments_data.items():
        if msid not in market_state:
            market_state[msid] = {}
        market_state[msid].update(data)
    instruments_data["timestamp"] = "ok"
    return instruments_data

with open(data, 'r') as file:
    # Read the entire content of the file
    content = file.read()
    
print(deribit_api_perpetual_future_oi_funding_oifunding(content, {}, {}))