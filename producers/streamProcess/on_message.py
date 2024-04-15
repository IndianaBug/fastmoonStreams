from datetime import datetime
import time
import sys
import os
current_directory = os.path.dirname(os.path.abspath(__file__))
module_directory = os.path.join(current_directory, '')
sys.path.append(module_directory)
from utilis_streamProcess import *
from typing import Literal, Dict, Any
from typing import Dict, List, Tuple, Union, Literal, Callable
from typing import List, Dict, Union, Optional, Literal
import ijson
import rapidjson as json
import gzip

class on_message_helper():

    """
        depth : {"bids" : [[price, amount]], "asks" : [[price, amount]], "timestamp" : '%Y-%m-%d %H:%M:%S'}
        trades_liquidations : {"liquidations" : {"side" : str, "amount" : float, "price" : float, "timestamp" : '%Y-%m-%d %H:%M:%S'}, 
                                "asks" : {"side" : str, "amount" : float, "price" : float, "timestamp" : '%Y-%m-%d %H:%M:%S'}, 
                                "timestamp" : '%Y-%m-%d %H:%M:%S'}
        oi_funding_optionoi_tta_ttp_gta_pos : {symbol : {"some indicator" : value}, ....}


        you must pass at least 3 args to evry function : data, market_state, connection data

        market_state is a dictionary of characteristics per instrument : Ex: btcusdt@spot@binance : {"oi": someoi.....}

        connection_data is the ws identificatio data
        
        # TOdo
        you should randomly initialize market state / remove the data from the first minute
        you need to fetch initial binance futures prices. all futures

    """
    # depth: Dict[str, Union[List[List[float, float]], Union[List[List[float, float]]]]]
    # trades_liquidations: Dict[str, Union[List[List[str, float, float, str]], str]]
    # future_perp_oi_funding_pos_dict_oioption: Dict[str, Any]


    @classmethod
    def convert_books(cls, data):
        return list(map(lambda x: [float(x[0]), float(x[1])], data))

    @classmethod
    def books_multiplier(cls, data, multiplier:callable, current_price):
        return list(map(lambda x: [float(x[0]), multiplier(float(x[1]), current_price)], data))

    @classmethod
    def process_timestamp(cls, value, divide_value=1):
        return datetime.fromtimestamp(int(value) / divide_value).strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def process_timestamp_no_timestamp(cls):
        return datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
  
class binance_on_message(on_message_helper):

    def __init__ (self, binance_derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            https://www.binance.com/en/support/faq/binance-coin-margined-futures-contract-specifications-a4470430e3164c13932be8967961aede

            https://www.binance.com/en/support/faq/binance-options-contract-specifications-cdee5d43b70d4d2386980d41786a8533

            Be cautios with option, as units vary for XRP and DOGE
        """
        if binance_derivate_multiplier == None:
            self.binance_derivate_multiplier = {
                "BTCUSD" : lambda amount, price, *args, **kwargs: amount * 100 / price,  # the same for perp and any expiry future
                "BTCUSDT" : lambda amount, price, *args, **kwargs: amount,
                "BTCDOMUSDT" : lambda amount, price, *args, **kwargs : amount,
                "BTCUSDC" : lambda amount, price, *args, **kwargs : amount,
            }
        else:
            self.binance_derivate_multiplier = binance_derivate_multiplier
    
    async def binance_api_spot_depth(self, data:dict, *args, **kwargs): 
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp_no_timestamp(), "bids" : bids, "asks" : asks}
        return d

    async def binance_api_linearperpetual_linearfuture_depth(self, data:dict, *args, **kwargs):  #-> 'on_message_helper.depth':
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = ""
        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "E.item":
                timestamp = value
                break

        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "bids" : bids, "asks" : asks}
        return d

    async def binance_api_inverseperpetual_inversefuture_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> 'on_message_helper.depth':
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None
        symbol = None
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "T":
                timestamp = value
            if prefix == "symbol":
                symbol = value
            if timestamp != None and symbol != None:
                break
        
        
        ss = symbol.split("_")[0]

        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@binance"
        current_price = market_state.get(imid, {}).get("price", 1000000000000000000)

        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                helper_list.append(self.binance_derivate_multiplier.get(ss)(float(value), current_price))
                bids.append(helper_list)
                helper_list = []
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(self.binance_derivate_multiplier.get(ss)(float(value), current_price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        

        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "bids" : bids, "asks" : asks}
        return d

    async def binance_ws_spot_linearperpetual_linearfuture_depth(self, data:dict,  *args, **kwargs): # -> 'on_message_helper.depth':
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = ""

        for prefix, event, value in ijson.parse(data):
            if prefix == "T":
                timestamp = value
                break

        for prefix, event, value in ijson.parse(data):
            if prefix == "b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "b.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "a.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
            
        return {"timestamp" : self.process_timestamp(timestamp, 1000), "bids" : bids, "asks" : asks}
    
    async def binance_ws_inverseperpetual_inversefuture_depth(self, data:dict, market_state, connection_data, *args, **kwargs): # -> 'on_message_helper.depth':
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None
        symbol = None
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "T":
                timestamp = value
            if prefix == "s":
                symbol = value
            if timestamp != None and symbol != None:
                break
        
        ss = symbol.split("_")[0]

        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@binance"
        current_price = market_state.get(imid, {}).get("price", 1000000000000000000)

        for prefix, event, value in ijson.parse(data):
            if prefix == "b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "b.item.item" and previous_map_event == "string":
                helper_list.append(self.binance_derivate_multiplier.get(ss)(float(value), current_price))
                bids.append(helper_list)
                helper_list = []
            if prefix == "a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "a.item.item" and previous_map_event == "string":
                helper_list.append(self.binance_derivate_multiplier.get(ss)(float(value), current_price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        
        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "bids" : bids, "asks" : asks}
        return d

    async def binance_ws_spot_linearperpetual_linearfuture_option_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> 'on_message_helper.trades_liquidations':
        symbol = data.get("s")
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        instType = "option" if len(symbol.split("-")) == 4 else instType
        msid = f"{symbol}@{instType}@binance"
        quantity = float(data.get("q"))
        price = float(data.get("p"))
        side = "buy" if data.get("m") is True else "sell"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        receive_time = float(data.get("E")) / 1000

        return {"trades" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "liquidations" : [], "receive_time" : receive_time}

    async def binance_ws_inverseperpetual_inversefuture_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> 'on_message_helper.trades_liquidations':
        data = json.loads(data)
        symbol = data.get("s")
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        msid = f"{symbol}@{instType}@binance"
        price = float(data.get("p"))
        quantity = self.binance_derivate_multiplier.get(data.get("s").split("_")[0])(float(data.get("q")), price)
        side = "buy" if data.get("m") is True else "sell"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        if msid in market_state:
            market_state[msid]["price"] = price
        if msid not in market_state:
            market_state[msid] = {}
            market_state[msid]["price"] = price
        receive_time = float(data.get("E")) / 1000
        return {"trades" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "liquidations" : [], "receive_time" : receive_time}

    async def binance_ws_linearperpetual_linearfuture_option_liquidations(self, data:dict, *args, **kwargs): #  -> 'on_message_helper.trades_liquidations':
        data = json.loads(data)
        quantity = float(data.get("o").get("q"))
        price = float(data.get("o").get("p"))
        side = data.get("o").get("S").lower()
        timestamp = self.process_timestamp(data, ["E"], 1000)
        receive_time = float(data.get("E")) / 1000
        return {"liquidations" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "trades" : [], "receive_time" : receive_time}

    async def binance_ws_inverseperpetual_inversefuture_liquidations(self, data:dict, *args, **kwargs): # -> 'on_message_helper.trades_liquidations':
        data = json.loads(data)
        price = float(data.get("o").get("p"))
        quantity = self.binance_derivate_multiplier.get(data.get("o").get("ps"))(float(data.get("o").get("q")), price)
        side = data.get("o").get("S").lower()
        timestamp = self.process_timestamp(data, ["E"], 1000)
        receive_time = float(data.get("E")) / 1000
        return {"liquidations" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "trades" : [], "receive_time" : receive_time}

    async def binance_api_oifutureperp_perpetual_oi_linear_inverse(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        l = {}
        for symbol, oidata in data.items():
            oidata = json.loads(oidata)
            symbol = oidata.get("symbol")
            ss = symbol.split("_")[0]
            instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
            price = market_state.get(f"{symbol}@{instType}@binance", {}).get("price", 1000000000)
            amount = self.binance_derivate_multiplier.get(ss)(float(oidata.get("openInterest")), price)
            msid = f"{symbol}@{instType}@binance"
            l[msid] = {"oi" : amount}
            if msid in market_state:
                market_state[msid]["oi"] = amount
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid]["oi"] = amount
        l["timestamp"] = self.process_timestamp_no_timestamp()
        return l

    async def binance_api_oioption_oi_option(self, data:list, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            https://www.binance.com/en/support/faq/binance-options-contract-specifications-cdee5d43b70d4d2386980d41786a8533
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []
        for l in data:
            for prefix, event, value in ijson.parse(l):
                if prefix == "item.symbol":
                    option_data = value.split("-")
                    msids.append(f"{value}@option@binance")
                    symbols.append(value)
                    strikes.append(float(option_data[2]))
                    days_left.append(binance_option_timedelta(option_data[1]))
                if prefix == "item.sumOpenInterest":
                    ois.append(float(value))
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": days_left[i],
                "oi": ois[i],
            }
        return instruments_data
        
    async def binance_api_posfutureperp_perpetual_future_linear_inverse_gta_tta_ttp(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        pos_data = {}
        for key, value in data.items():
            objective = key.split("_")[-1]
            data_position = json.loads(value)
            if  data_position != []:
                data_position = data_position[0]
                symbol = data_position.get("symbol") if "symbol" in data_position else data_position.get("pair")
                instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
                msid = f"{symbol}@{instType}@binance"
                longAccount = float(data_position.get("longAccount")) if "longAccount" in data_position else float(data_position.get("longPosition"))
                shortAccount = float(data_position.get("shortAccount")) if "shortAccount" in data_position else float(data_position.get("shortPosition"))
                longShortRatio = float(data_position.get("longShortRatio"))
                if msid in market_state:
                    market_state[msid][f"{objective}_long_ratio"] = longAccount
                    market_state[msid][f"{objective}_short_ratio"] = shortAccount
                    market_state[msid][f"{objective}_ratio"] = longShortRatio
                if msid not in market_state:
                    market_state[msid] = {}
                    market_state[msid][f"{objective}_long_ratio"] = longAccount
                    market_state[msid][f"{objective}_short_ratio"] = shortAccount
                    market_state[msid][f"{objective}_ratio"] = longShortRatio
                pos_data[msid] = {}
                pos_data[msid][f"{objective}_long_ratio"] = longAccount
                pos_data[msid][f"{objective}_short_ratio"] = shortAccount
                pos_data[msid][f"{objective}_ratio"] = longShortRatio
        pos_data.update({"timestamp" : self.process_timestamp_no_timestamp()})
        return pos_data    

    async def binance_api_fundperp_perpetual_funding_linear_inverse(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        d = {}
        for funddata in data.values():
            funddata = json.loads(funddata)[0]
            symbol = funddata.get("symbol")
            funding = funddata.get("fundingRate")
            msid = f"{symbol}@perpetual@binance"
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["funding"]  = float(funding)
            if msid not in d:
                d[msid] = {}
            d[msid]["funding"] = float(funding)
        d.update({"timestamp" : self.process_timestamp_no_timestamp()})
        return d

class bybit_on_message(on_message_helper):

    def __init__ (self, bybit_derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            https://www.bybit.com/en/announcement-info/transact-parameters
        """
        if bybit_derivate_multiplier == None:
            self.bybit_derivate_multiplier = {
                "BTCUSD" : lambda amount, price : amount / price,  # the same for perp and any expiry future
                "BTCUSDT" : lambda amount, price : amount,
                "BTCPERP" : lambda amount, price : amount,
                "BTCUSDM24" : lambda amount, price : amount / price,
                "BTCUSDU24" : lambda amount, price : amount / price,
                "BTC" : lambda amount, price : amount,   # expiry futures

            }
        else:
            self.bybit_derivate_multiplier = bybit_derivate_multiplier

    async def bybit_api_fundperp_linear_inverse_perpetual_funding_future(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        d = {}
        for instrument, funddata in data.items():
            funddata = json.loads(funddata)
            msid = f"{instrument}@perpetual@bybit"
            funding = float(funddata.get("result").get("list")[0].get("fundingRate"))
            d[msid] = {"funding" : funding}
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["funding"] = funding
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    async def bybit_api_oifutureperp_linear_inverse_perpetual_future_oi(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        d = {}
        for oidata in data.values():
            oidata = json.loads(oidata)
            symbol = oidata.get("result").get("symbol")
            underlying = symbol.split("-")[0]
            instType = "future" if len(symbol.split("-")) == 2 else "perpetual"
            oi = float(oidata.get("result").get("list")[0].get("openInterest"))
            msid = f"{symbol}@{instType}@bybit"
            price = market_state.get(msid, {}).get("price", 100000000) if msid in market_state else market_state.get(f"{msid.split('-')[0]}USDT@spot@bybit", {}).get("price", 100000000)
            oi = self.bybit_derivate_multiplier.get(underlying)(oi, price)
            d[msid] = {"oi" : oi}
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["oi"] = oi       
            d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    async def bybit_api_posfutureperp_perpetual_linear_inverse_future_gta(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        d = {}
        for k, posdata in data.items():
            posdata = json.loads(posdata)
            symbol = posdata.get("result").get("list")[0].get("symbol")
            msid = f"{symbol}@perpetual@bybit"
            buyRatio = float(posdata.get("result").get("list")[0].get("buyRatio"))
            sellRatio = float(posdata.get("result").get("list")[0].get("sellRatio"))
            d[msid] = {
                "gta_long_ratio" : buyRatio,
                "gta_short_ratio" : sellRatio
            }
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["gta_long_ratio"] = buyRatio
            market_state[msid]["gta_short_ratio"] = sellRatio
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    async def bybit_api_spot_linear_perpetual_future_option_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "result.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.b.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "result.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.a.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp_no_timestamp(), "bids" : bids, "asks" : asks}
        return d    

    async def bybit_api_inverse_perpetual_future_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None
        symbol = None
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.ts":
                timestamp = value
            if prefix == "result.s":
                symbol = value
            if timestamp != None and symbol != None:
                break
        
        ss = symbol.split("_")[0]

        instType = "future" if symbol.split("-")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@bybit"
        current_price = market_state.get(imid, {}).get("price", 1000000000000000000)

        for prefix, event, value in ijson.parse(data):
            if prefix == "result.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.b.item.item" and previous_map_event == "string":
                helper_list.append(self.bybit_derivate_multiplier.get(ss)(float(value), current_price))
                helper_list = []
                bids.append(helper_list)
            if prefix == "result.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.a.item.item" and previous_map_event == "string":
                helper_list.append(self.bybit_derivate_multiplier.get(ss)(float(value), current_price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        

        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "bids" : bids, "asks" : asks}
        return d

    async def bybit_ws_spot_linear_perpetual_future_option_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None 

        for prefix, event, value in ijson.parse(data):
            if prefix == "ts":
                timestamp = value
            if prefix == "data.s":
                symbol = value

                
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.b.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.a.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        
        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "bids" : bids, "asks" : asks}
        return d

    async def bybit_ws_inverse_perpetual_future_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None        
        symbol = None       

        for prefix, event, value in ijson.parse(data):
            if prefix == "ts":
                timestamp = value
            if prefix == "data.s":
                symbol = value
            if timestamp != None and symbol != None:
                break

        ss = symbol.split("_")[0]

        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@binance"
        current_price = market_state.get(imid, {}).get("price", 1000000000000000000)
                
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.b.item.item" and previous_map_event == "string":
                helper_list.append(self.bybit_derivate_multiplier.get(ss)(float(value), current_price))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.a.item.item" and previous_map_event == "string":
                helper_list.append(self.bybit_derivate_multiplier.get(ss)(float(value), current_price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        
        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "bids" : bids, "asks" : asks}
        return d

    async def bybit_ws_linear_spot_perpetual_future_option_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        data = json.loads(data)
        trades = []
        liquidations = []
        for trade in data.get("data"):
            timestamp = self.process_timestamp(trade, ["T"], 1000)
            receive_time = float(trade.get("T")) / 1000
            side = trade.get("S").lower()
            price = float(trade.get("p"))
            size = float(trade.get("v"))
            trades.append([{"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp}])

            symbol = trade.get("s")
            instType = "perpetual" if len(symbol.split("_")) == 1 else "future"
            instType = "option" if len(symbol.split(symbol)) > 3 else instType
            msid = f"{symbol}@{instType}@bybit"
            if instType != "option":
                if msid in market_state:
                    market_state[msid]["price"] = price
                if msid not in market_state:
                    market_state[msid] = {}
                    market_state[msid]["price"] = price
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

    async def bybit_ws_inverse_perpetual_future_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        for trade in data.get("data"):
            symbol = trade.get("s")
            timestamp = self.process_timestamp(trade, ["T"], 1000)
            receive_time = float(trade.get("T")) / 1000
            side = trade.get("S").lower()
            price = float(trade.get("p"))
            size = self.bybit_derivate_multiplier.get(symbol)(float(trade.get("v")), price)
            trades.append([{"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp}])
            instType = "perpetual" if len(symbol.split("_")) == 1 else "future"
            instType = "option" if len(symbol.split(symbol)) > 3 else instType
            msid = f"{symbol}@{instType}@bybit"
            if msid in market_state:
                market_state[msid]["price"] = price
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid]["price"] = price
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

    async def bybit_ws_linear_perpetual_future_option_liquidations(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        trade = data.get("data")
        timestamp = self.process_timestamp(trade, ["updatedTime"], 1000)
        receive_time = float(trade.get("updatedTime")) / 1000
        side = trade.get("side").lower()
        price = float(trade.get("price"))
        size = float(trade.get("size"))
        liquidations.append([{"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp}])
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

    async def bybit_ws_inverse_perpetual_future_liquidations(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        data = json.loads(data)
        trades = []
        liquidations = []
        trade = data.get("data")
        symbol = trade.get("symbol")
        timestamp = self.process_timestamp(trade, ["updatedTime"], 1000)
        receive_time = float(trade.get("updatedTime")) / 1000
        side = trade.get("side").lower()
        price = float(trade.get("price"))
        size = self.bybit_derivate_multiplier.get(symbol)(float(trade.get("size")), price)
        liquidations.append([{"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp}])
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

    async def bybit_api_oioption_oi_option(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): # -> Tuple[np.array, np.array, np.array, float, str]:
        """
            https://blog.bybit.com/post/everything-you-need-to-know-about-bybit-s-usdc-options-blt905124bb9461ab21/
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.list.item.symbol":
                option_data = value.split("-")
                msids.append(f"{value}@option@bybit")
                symbols.append(value)
                strikes.append(float(option_data[2]))
                days_left.append(calculate_option_time_to_expire_bybit(option_data[1]))
            if prefix == "result.list.item.openInterest":
                ois.append(float(value))
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": days_left[i],
                "oi": ois[i],
            }
        return instruments_data

class okx_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            https://www.okx.com/trade-market/info/futures
            https://www.okx.com/help/i-okx-options-introduction
        """
        if derivate_multiplier == None:
            self.okx_derivate_multiplier = {
                "perpetual@future" : {
                    "BTC-USDT" : lambda amount, *args, **kwargs : amount * 0.01,  
                    "BTC-USDC" : lambda amount, *args, **kwargs : amount * 0.0001,  
                    "BTC-USD" : lambda amount, price, *args, **kwargs : amount / price * 100,
                },
                "option" : {
                    "BTC-USD" : lambda amount, *args, **kwargs : amount * 0.01
                }
            }
        else:
            self.okx_derivate_multiplier = derivate_multiplier

    async def okx_api_fundperp_perpetual_future_funding(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
        """
        d = {}
        for key, oidata in data.items():
            oidata = json.loads(oidata)
            symbol = oidata.get("data")[0].get("instId")
            instType = get_okx_insttype(symbol)
            msid = f"{symbol}@{instType}@okx"
            funding = float(oidata.get("data")[0].get("fundingRate"))
            d[msid] = {"funding" : funding}
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["funding"] = funding
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    async def okx_api_gta_perpetual_future(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
        """
        label = "BTC@future@perpetual@okx" 
        if label not in market_state:
            market_state[label] = {}
        count = 0
        for prefix, event, value in ijson.parse(data):
            if event == "string":
                count += 1
            if prefix == "data.item.item" and count == 2:
                timestamp = value
            if prefix == "data.item.item" and count == 3:
                gta = float(value)
                break
        d = {}            
        d["timestamp"] = self.process_timestamp_no_timestamp()
        d["gta_ratio"] = gta
        market_state[label] = {"gta_ratio" : gta}
        return d

    async def okx_api_oifutureperp_perpetual_future_oi(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
        """
        d = {}
        for key, oidata in data.items():
            oidata = json.loads(oidata)
            symbol = oidata.get("data")[0].get("instId")
            instType = "perpetual" if "SWAP" in symbol else "future"
            msid = f"{symbol}@{instType}@okx"
            oi = float(oidata.get("data")[0].get("oiCcy"))
            d[msid] = {"oi" : oi}
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["oi"] = oi  
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    async def okx_api_option_oi(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs): 
        """
            https://www.okx.com/help/i-okx-options-introduction
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.instId":
                option_data = value.split("-")
                msids.append(f"{value}@option@okx")
                symbols.append(value)
                strikes.append(float(option_data[-2]))
                days_left.append(calculate_option_time_to_expire_okx(option_data[2]))
            if prefix == "data.item.oi":
                ois.append(self.okx_derivate_multiplier.get("option").get("-".join(option_data[:2]))(float(value)))
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": days_left[i],
                "oi": ois[i],
            }
        return instruments_data

    async def okx_api_ws_spot_option_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        string_count = 0

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
                string_count += 1
            if prefix == "data.item.bids.item.item" and previous_map_event == "string" and string_count == 1:
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
                string_count = 0
            if prefix == "data.item.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
                string_count += 1
            if prefix == "data.item.asks.item.item" and previous_map_event == "string" and string_count == 1:
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
                string_count = 0
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp_no_timestamp(), "bids" : bids, "asks" : asks}
        return d
    
    async def okx_api_ws_linear_inverse_perpetual_future_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None
        string_count = 0
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.ts":
                timestamp = value

        symbol = connection_data.get("exchange_symbols")[0]
        ss = "-".join(symbol.split("-")[:2])
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        imid = f"{symbol}@{instType}@okx"
        current_price = market_state.get(imid, {}).get("price", 1000000000000000000)

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
                string_count += 1
            if prefix == "data.item.bids.item.item" and previous_map_event == "string" and string_count == 1:
                helper_list.append(self.okx_derivate_multiplier.get("perpetual@future").get(ss)(float(value), current_price))
                helper_list = []
                bids.append(helper_list)
                string_count = 0
            if prefix == "data.item.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
                string_count += 1
            if prefix == "data.item.asks.item.item" and previous_map_event == "string"  and string_count == 1:
                helper_list.append(self.okx_derivate_multiplier.get("perpetual@future").get(ss)(float(value), current_price))
                asks.append(helper_list)
                helper_list = []
                string_count = 0
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp_no_timestamp(), "bids" : bids, "asks" : asks}
        return d

    async def okx_ws_option_trades_optionTrades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
        """
        data = json.loads(data)
        trades = []
        liquidations = []        
        for trade in data.get("data"):
            side = trade.get('side')
            price =float(trade.get('idxPx'))
            receive_time = float(trade.get("ts")) / 1000
            timestamp = self.process_timestamp(trade, ["ts"], 1000)
            amount = float(trade.get('fillVol'))
            trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}   
    
    async def okx_ws_spot_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []           
        for trade in data.get("data"):
            side = trade.get('side')
            price =float(trade.get('px'))
            timestamp = self.process_timestamp(trade, ["ts"], 1000)
            receive_time = float(trade.get("ts")) / 1000
            amount = float(trade.get('sz'))
            trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])
            msid = f"{trade.get('instId')}@spot@okx"
            if msid in market_state:
                market_state[msid]["price"] = price
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid]["price"] = price
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}     
    
    async def okx_ws_linear_inverse_perpetual_future_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []           
        for trade in data.get("data"):
            multiplier_symbol = "-".join(trade.get('instId').split("-")[0:2])
            side = trade.get('side')
            price =float(trade.get('px'))
            timestamp = self.process_timestamp(trade, ["ts"], 1000)
            receive_time = float(trade.get("ts")) / 1000
            amount = self.okx_derivate_multiplier.get("perpetual@future").get(multiplier_symbol)(float(trade.get('sz')), price)
            trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}]) 

            instType = connection_data.get("instType")
            msid = f"{trade.get('instId')}@{instType}@okx"
            if msid in market_state:
                market_state[msid]["price"] = price
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid]["price"] = price

        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}          

    async def okx_ws_future_perpetual_option_liquidations(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []           
        for liquidation in data.get("data"):
            instType = liquidation.get("instType")
            instId = liquidation.get("instId")
            multiplier_symbol = liquidation.get('instFamily')
            if "BTC" in instId:
                for l2 in liquidation.get("details"):
                    side = l2.get('side')
                    price =float(l2.get('bkPx'))
                    receive_time = float(l2.get("ts")) / 1000
                    timestamp = self.process_timestamp(l2, ["ts"], 1000)
                    if instType != "OPTION":
                        amount = self.okx_derivate_multiplier.get("perpetual@future").get(multiplier_symbol)(float(l2.get("sz")), price)
                    if instType == "OPTION":
                        amount = self.okx_derivate_multiplier.get("option").get(multiplier_symbol)(float(l2.get("sz")), price)
                    liquidations.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])    
                return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}   

class deribit_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            https://www.deribit.com/kb/deribit-linear-perpetual

            https://static.deribit.com/files/USDCContractSpecsandmargins.pdf
        """
        if derivate_multiplier == None:
            self.deribit_derivate_multiplier = {
                 "BTC" : lambda amount, price=1, objective="",*args, **kwargs: amount  / price / 10 if objective == "oifuture" else amount  / price / 10,    # bullshit deribit api for oi
                "BTC_USDC" : lambda amount, *args, **kwargs : amount * 0.001,  # any swap or future
                "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.001,

            }
        else:
            self.deribit_derivate_multiplier = derivate_multiplier

    async def deribit_api_option_oi_oifunding(self, data:dict, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
        """
            https://static.deribit.com/files/USDCContractSpecsandmargins.pdf
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.item.instrument_name":
                option_data = value.split("-")
                msids.append(f"{value}@option@deribit")
                symbols.append(value)
                strikes.append(float(option_data[2]))
                days_left.append(calculate_option_time_to_expire_deribit(option_data[1]))
            if prefix == "result.item.open_interest":
                ois.append(float(value))
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": days_left[i],
                "oi": ois[i],
            }
        instruments_data["timestamp"] = self.process_timestamp_no_timestamp()
        return instruments_data

    async def deribit_api_perpetual_future_oi_funding_oifunding(self, data:dict, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
        msids = []
        symbols = []
        prices = []
        ois = []
        this_symbol = ""
        fundings = {}
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.item.instrument_name":
                this_symbol = value
                instType = "future" if any(char.isdigit() for char in value.split("-")[-1]) else "perpetual"
                msids.append(f"{value}@{instType}@deribit")
                symbols.append(value)
            if prefix == "result.item.mid_price":
                prices.append(float(value))
            if prefix == "result.item.funding_8h":
                instType = "future" if any(char.isdigit() for char in this_symbol.split("-")[-1]) else "perpetual"
                fundings[f"{this_symbol}@{instType}@deribit"] = {}
                fundings[f"{this_symbol}@{instType}@deribit"]["funding"] = float(value)
            if prefix == "result.item.open_interest":
                ois.append(float(value))
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "oi": self.deribit_derivate_multiplier.get(symbols[i].split('-')[0])(ois[i], prices[-1], "oifuture"),
            }
        
        for key, item in fundings.items():
            for key_2, fun in item.items():
                instruments_data[key][key_2] = fun

        for msid, data in instruments_data.items():
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid].update(data)
        instruments_data["timestamp"] = self.process_timestamp_no_timestamp()
        return instruments_data

    async def deribit_ws_future_perpetual_linear_inverse_option_trades_tradesagg_liquidations(self, data:dict, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
        """
            https://docs.deribit.com/#trades-kind-currency-interval -- contains liquidations
        """
        data = json.loads(data)
        trades = []
        liquidations = []
        for trade in data.get("params").get("data"):
            symbol = trade.get("instrument_name").split("-")[0]
            side = trade.get("direction")
            price = float(trade.get("price"))
            amount = self.deribit_derivate_multiplier.get(symbol)(float(trade.get("amount")), price)
            timestamp = self.process_timestamp(trade, ["timestamp"], 1000)
            receive_time = float(trade.get("timestamp")) / 1000
            if "liquidation" not in trade:
                trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])
            if "liquidation" in trade:
                liquidations.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])

            instType = "future" if any(char.isdigit() for char in trade.get("instrument_name").split("-")[-1]) else "perpetual"
            instType = "option" if len(trade.get("instrument_name").split("-")) > 2 else instType
            msid = f"{trade.get('instrument_name')}@{instType}@deribit"
            if instType != "option":
                if msid in market_state:
                    market_state[msid]["price"] = price
                if msid not in market_state:
                    market_state[msid] = {}
                    market_state[msid]["price"] = price
            
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

    async def deribit_api_perpetual_future_depth(self, data:dict, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        symbol = None
        price = None
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.instrument_name":
                symbol = value
            if prefix == "result.mark_price":
                price = float(value)
            if symbol != None and price != None:
                break
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.bids.item.item" and previous_map_event == "number":
                helper_list.append(self.deribit_derivate_multiplier.get(symbol.split("-")[0])(float(value), price))
                bids.append(helper_list)
                helper_list = []
            if prefix == "result.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.asks.item.item" and previous_map_event == "number":
                helper_list.append(self.deribit_derivate_multiplier.get(symbol.split("-")[0])(float(value), price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp_no_timestamp(), "bids" : bids, "asks" : asks}
        return d
        
    async def deribit_ws_perpetual_future_depth(self, data:dict, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:

        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None
        symbol = None

        for prefix, event, value in ijson.parse(data):
            if prefix == "params.data.instrument_name":
                symbol = value
            if prefix == "params.data.timestamp":
                timestamp = float(value)
            if symbol != None and timestamp != None:
                break

        instType = "future" if any(char.isdigit() for char in symbol.split("-")[-1]) else "perpetual"
        price = market_state.get(f"{symbol}@{instType}@deribit", {}).get("price", 10000000000)
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "params.data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "params.data.bids.item.item" and previous_map_event == "number":
                helper_list.append(self.deribit_derivate_multiplier.get(symbol.split("-")[0])(float(value), price))
                bids.append(helper_list)
                helper_list = []
            if prefix == "params.data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "params.data.asks.item.item" and previous_map_event == "number":
                helper_list.append(self.deribit_derivate_multiplier.get(symbol.split("-")[0])(float(value), price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "receive_time" : timestamp / 1000, "bids" : bids, "asks" : asks}
        return d

class bitget_on_message(on_message_helper):

    def __init__ (self):
        """
            Contract multipliers not needed 
            
            I didnt find any documentations. ANd with api fetch and comparing the data with coinmarketcap it seems they are not necessary
        """
        pass

    async def bitget_api_spot_linear_inverse_perpetual_future_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "number":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "number":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        return {"timestamp" : self.process_timestamp_no_timestamp(), "bids" : bids, "asks" : asks}

    async def bitget_ws_spot_linear_inverse_perpetual_future_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.ts":
                timestamp = float(value)
                break

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.item.bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.item.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.item.asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp(timestamp, 1000), "receive_time" : timestamp/1000, "bids" : bids, "asks" : asks}
        return d

    async def bitget_ws_inverse_perpetual_future_spot_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        symbol = data.get("arg").get("instId")
        instType = "spot" if data.get("arg").get("instType") == "SPOT" else "perpetual"
        for trade in data.get("data"):
            side = trade.get("side")
            price = float(trade.get("price"))
            amount = float(trade.get("size"))
            timestamp = self.process_timestamp(data, ["ts"], 1000)
            receive_time = float(data.get("ts")) / 1000 
            trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])

            msid = f"{symbol}@{instType}@bitget"
            if msid in market_state:
                market_state[msid]["price"] = price
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid]["price"] = price
            
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

    async def bitget_api_oi_perpetual_oifutureperp(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        d = {}
        for instrument_name, instrument_data in data.items():
            instrument_data = json.loads(instrument_data).get("data")
            symbol = instrument_data.get("openInterestList")[0].get("symbol")
            msid = f"{symbol}@perpetual@bitget"
            d[msid] = {}
            oi = float(instrument_data.get("openInterestList")[0].get("size"))
            d[msid]["oi"] = oi
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["oi"] = oi
        timestamp = self.process_timestamp_no_timestamp()
        d["timestamp"] = timestamp
        return d

    async def bitget_api_funding_perpetual_fundperp(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            [[side, price, size, timestamp]]
        """
        d = {}
        for instrument_name, instrument_data in data.items():
            instrument_data = json.loads(instrument_data).get("data")[0]
            symbol = instrument_data.get("symbol")
            msid = f"{symbol}@perpetual@bitget"
            funding = float(instrument_data.get("fundingRate"))
            d[msid] = {}
            d[msid]["funding"] = funding
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid]["funding"] = funding
        timestamp = self.process_timestamp_no_timestamp()
        d["timestamp"] = timestamp
        return d

class bingx_on_message(on_message_helper):

    def __init__ (self):
        """
            No need, calls provide data in native coin
        """
        pass

    async def bingx_api_perpetual_linear_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs) -> Tuple[list, str]:
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bidsCoin.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bidsCoin.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.asksCoin.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asksCoin.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  self.process_timestamp_no_timestamp(), "receive_time" :time.time(), "bids" : bids, "asks" : asks}
        return d

    async def bingx_ws_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):

        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : self.process_timestamp_no_timestamp(), "receive_time" : time.time(), "bids" : bids, "asks" : asks}
        return d

    async def bingx_api_perpetual_oi(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        timestamp = self.process_timestamp(data.get("data"), ["time"], 1000)
        openInterest = float(data.get("data").get("openInterest"))
        ss = str(data.get('data').get('symbol'))
        s = f"{ss}@perpetual@bingx"
        openInterest = openInterest / market_state.get(s, {}).get("price", 100000)
        d = {s : {"oi" : openInterest}}
        if s not in market_state:
            market_state[s] = {}
        market_state[s]["oi"] = openInterest
        return d

    async def bingx_api_perpetual_funding(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        funding = float(data.get("data").get("lastFundingRate"))
        ss = str(data.get('data').get('symbol'))
        s = f"{ss}@perpetual@bingx"
        d = {s : {"oi" : funding}}
        if s not in market_state:
            market_state[s] = {}
        market_state[s]["funding"] = funding
        return d
    
    async def bingx_ws_trades_perpetual(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        trades = []
        liquidations = []
        symbol = data.get("dataType").split("@")[0]
        for trade in data.get("data"):
            side = "buy" if trade.get("m") is True else "sell"
            price = float(trade.get("p"))
            amount = float(trade.get("q"))
            timestamp = self.process_timestamp(trade, ["T"], 1000)
            receive_time = float(data.get("T")) / 1000 
            trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])

            msid = f"{symbol}@perpetual@bingx"
            if msid in market_state:
                market_state[msid]["price"] = price
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid]["price"] = price
            
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}
    
    async def bingx_ws_trades_spot(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        trades = []
        liquidations = []
        trade = data.get("data")
        symbol = trade.get("s")
        side = "buy" if trade.get("m") is True else "sell"
        price = float(trade.get("p"))
        amount = float(trade.get("q"))
        timestamp = self.process_timestamp(trade, ["t"], 1000)
        receive_time = float(trade.get("t")) / 1000 
        trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])
        msid = f"{symbol}@spot@bingx"
        if msid in market_state:
            market_state[msid]["price"] = price
        if msid not in market_state:
            market_state[msid] = {}
            market_state[msid]["price"] = price
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

class htx_on_message(on_message_helper):

    def __init__ (self):
        """
            Contract multipliers not needed (I couldnt find the documentation for htem)
        """
        pass

    async def htx_api_perpetual_oi(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        d = {}
        for marginType in data:
            data_per_marginType = json.loads(data.get(marginType)).get("data")
            for data_instrument in data_per_marginType:
                symbol = data_instrument.get("contract_code")
                oi = float(data_instrument.get("amount"))
                instType = "future" if data_instrument.get("business_type") == "futures" else "perpetual"
                msid = f"{symbol}@{instType}@htx"
                d[msid] = {"oi" :  oi}

                if msid not in market_state:
                    market_state[msid] = {}
                market_state[msid]["oi"] = oi

        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    async def htx_api_perpetual_pos_posfutureperp_gta(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        d = {}
        for instrument in data:
            indicator_type = instrument.split("_")[-1]
            pos_data = json.loads(data.get(instrument)).get("data")
            if "contract_code" in pos_data:
                symbol = pos_data.get("contract_code")
                instType = "linear@future" if "FUTURES" in symbol else "linear@perpetual"
            elif "symbol" in pos_data:
                symbol = pos_data.get("symbol")
                instType = "inverse@future@perpetual"
            msid = f"{symbol}@{instType}@htx"

            long_ratio = float(pos_data.get("list")[0].get("buy_ratio"))
            short_ratio = float(pos_data.get("list")[0].get("sell_ratio"))
            d[msid] = {f"{indicator_type}_long_ratio" : long_ratio, f"{indicator_type}_short_ratio" : short_ratio}

            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid][f"{indicator_type}_long_ratio"] = long_ratio
            market_state[msid][f"{indicator_type}_short_ratio"] = short_ratio

        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    async def htx_api_perpetual_funding_fundperp(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        d = {}
        for marginCoin in data:
            instData = json.loads(data.get(marginCoin)).get("data")[0]
            funding = float(instData.get("funding_rate"))
            contract_code = instData.get("contract_code")
            msid = f"{contract_code}@perpetual@htx"
            d[msid] = {"funding" : funding}
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid][f"funding"] = funding
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

class kucoin_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier=None):
        """
            https://www.kucoin.com/pt/futures/contract/detail/XBTUSDTM
        """
        if derivate_multiplier == None:
            self.kucoin_derivate_multiplier = {
                "XBTUSDTM" : lambda amount, *args, **kwargs : amount * 0.001,  
            }
        else:
            self.kucoin_derivate_multiplier = derivate_multiplier

    async def kucoin_ws_spot_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        symbol = data.get("data").get("symbol")
        side = data.get("data").get("side")
        price = float(data.get("data").get("price"))
        amount = float(data.get("data").get("size"))
        timestamp = self.process_timestamp(data.get("data"), ["time"], 10**9)
        receive_time = float(data.get("data").get("time")) / 10**9 
        trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])

        msid = f"{symbol}@spot@kucoin"
        if msid in market_state:
            market_state[msid]["price"] = price
        if msid not in market_state:
            market_state[msid] = {}
            market_state[msid]["price"] = price
            
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}

    async def kucoin_ws_perpetual_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        symbol = data.get("data").get("symbol")
        side = data.get("data").get("side")
        price = float(data.get("data").get("price"))
        amount = self.kucoin_derivate_multiplier.get(symbol)(float(data.get("data").get("size")), price)
        timestamp = self.process_timestamp(data.get("data"), ["ts"], 10**9)
        receive_time = float(data.get("data").get("ts")) / 10**9 
        trades.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])

        msid = f"{symbol}@perpetual@kucoin"
        if msid in market_state:
            market_state[msid]["price"] = price
        if msid not in market_state:
            market_state[msid] = {}
            market_state[msid]["price"] = price
            
        return {"trades" : trades, "liquidations" : liquidations, "receive_time" : receive_time}
    
    async def kucoin_api_perpetual_oi_funding_oifunding(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        d = {}
        data = data.get("data")
        symbol = data.get("symbol")
        multiplier = float(data.get("multiplier"))
        timestamp = self.process_timestamp_no_timestamp()
        oi = float(data.get("openInterest")) * multiplier
        funding = float(data.get("fundingFeeRate"))
        msid = f"{symbol}@perpetual@kucoin"
        d[msid] = {"oi" : oi, "funding" : funding}
        if msid not in market_state:
            market_state[msid] = {}
        market_state[msid]["oi"] = oi
        market_state[msid]["funding"] = funding
        d["timestamp"] = timestamp
        return d

    async def kucoin_api_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):

        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  self.process_timestamp_no_timestamp(), "receive_time" :time.time(), "bids" : bids, "asks" : asks}
        return d

    async def kucoin_api_perpetual_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        symbol = None
        price = market_state.get(f"{symbol}@perpetual@kucoin", {}).get("price", 1000000000)

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.symbol":
                symbol = value
                break

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "number":
                helper_list.append( self.kucoin_derivate_multiplier.get(symbol)(float(value), price))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "number":
                helper_list.append( self.kucoin_derivate_multiplier.get(symbol)(float(value), price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  self.process_timestamp_no_timestamp(), "receive_time" :time.time(), "bids" : bids, "asks" : asks}
        return d

    async def kucoin_ws_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        d = {}
        for side in ["asks", "bids"]:
            books = [[x[0], x[1]] for x in self.convert_books(data.get("data").get("changes").get(side))]
            d[side] = books
        print(data.get("data").get("time"))
        d["timestamp"] = self.process_timestamp(data.get("data"), ["time"], 1000)
        d["receive_time"] = data.get("data").get("time") / 1000
        return d

    async def kucoin_ws_perpetual_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        d = {}
        symbol = data.get("topic").split(":")[-1]
        change = data.get("data").get("change").split(",")
        for side in ["asks", "bids"]:
            side2 = "buy" if side == "bids" else "sell"
            price = market_state.get(f"{symbol}@perpetual@kucoin", 10000000)
            books = [float(change[0]), self.kucoin_derivate_multiplier.get(symbol)(float(change[-1]), price)] if side2 == change[1] else [[]]
            d[side] = books
        print(data.get("data").get("time"))
        d["timestamp"] = self.process_timestamp(data.get("data"), ["timestamp"], 10**3)
        d["receive_time"] = data.get("data").get("timestamp") / 1000
        return d
    
class mexc_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier=None):
        """
            https://www.mexc.com/support/articles/17827791509072
        """
        if derivate_multiplier == None:
            self.mexc_derivate_multiplier = {
                "BTC-USDT" : lambda amount, *args, **kwargs : amount * 0.0001,  
                "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.0001, # some unstandart symbols in API, maybe not needed just in case
            }
        else:
            self.mexc_derivate_multiplier = derivate_multiplier

    async def mexc_ws_spot_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = data.get("d").get("deals")
        symbol = data.get("c").split("@")[-1]
        ttt = []
        lll = []
        for trade in trades:
            price = float(trade.get("p"))
            side = "buy" if int(trade.get("S")) == 1 else "sell"
            amount = float(trade.get("v"))
            timestamp = self.process_timestamp(trade, ["t"], 10**3)
            receive_time = float(trade.get("t")) / 10**3 
            ttt.append([{"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}])

            msid = f"{symbol}@spot@mexc"
            if msid in market_state:
                market_state[msid]["price"] = price
            if msid not in market_state:
                market_state[msid] = {}
                market_state[msid]["price"] = price
        return {"trades" : ttt, "liquidations" : lll, "receive_time" : receive_time}

    async def mexc_ws_perpetual_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        symbol = data.get("symbol") 
        trade = data.get("data")
        trades = []
        liquidations = []
        price = float(trade.get("p"))
        side = "buy" if int(trade.get("T")) == 1 else "sell"
        amount = self.mexc_derivate_multiplier.get(symbol)(float(trade.get("v")), price)
        timestamp = self.process_timestamp(trade, ["t"], 10**3)
        receive_time = float(trade.get("t")) / 10**3 
        trades.append([side, amount, price, timestamp])

        msid = f"{symbol}@perpetual@mexc"
        if msid in market_state:
            market_state[msid]["price"] = price
        if msid not in market_state:
            market_state[msid] = {}
            market_state[msid]["price"] = price
        return {"trades" : trades, "liquidations" : [], "receive_time" : receive_time}

    async def mexc_api_perpetual_oi_funding_oifunding(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        d = {}
        symbol = data.get("data").get("symbol")
        msid = f"{symbol}@perpetual@mexc"
        oi = self.mexc_derivate_multiplier.get(symbol)(float(data.get("data").get("holdVol")))
        timestamp = self.process_timestamp_no_timestamp()
        funding = float(data.get("data").get("fundingRate"))
        d[msid] = {"oi" : oi, "funding" : funding, "timestamp" : timestamp}

        if msid in market_state:
            market_state[msid]["funding"] = funding
            market_state[msid]["oi"] = oi
        if msid not in market_state:
            market_state[msid] = {}
            market_state[msid]["funding"] = funding
            market_state[msid]["oi"] = oi
        return d

    async def mexc_api_perpetual_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
    
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        symbol = connection_data.get("exchange_symbols")[0]
        current_price = market_state.get(f"{symbol}@perpetual@mexc", {}).get("price", 10000000000000000)

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "number":
                helper_list.append(self.mexc_derivate_multiplier.get(symbol)(float(value), current_price))
                helper_list = []
                bids.append(helper_list)
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "number":
                helper_list.append(self.mexc_derivate_multiplier.get(symbol)(float(value), current_price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  self.process_timestamp_no_timestamp(), "receive_time" :time.time(), "bids" : bids, "asks" : asks}
        return d

    async def mexc_api_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):

        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  self.process_timestamp_no_timestamp(), "receive_time" :time.time(), "bids" : bids, "asks" : asks}
        return d

    async def mexc_ws_perpetual_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
    
        data = json.loads(data)

        timestamp = float(data.get("ts"))
        symbol = data.get("symbol")

        data = data.get("data")

        asks = [[ask[0], self.mexc_derivate_multiplier.get(symbol)(ask[1])] for ask in data.get("asks")] if data.get("asks") != [] else []
        bids = [[ask[0], self.mexc_derivate_multiplier.get(symbol)(ask[1])] for ask in data.get("bids")] if data.get("bids") != [] else []

        d = {"timestamp" :  self.process_timestamp(timestamp, 1000), "receive_time" :timestamp/1000, "bids" : bids, "asks" : asks}
        return d

    async def mexc_ws_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):

        data = json.loads(data)

        timestamp = float(data.get("t"))

        bidsdata = data.get("d").get("bids") if "bids" in data.get("d") else []
        bids = [[float(bid.get("p")), float(bid.get("v"))] for bid in bidsdata] if bidsdata != [] else bidsdata
        asksdata = data.get("d").get("asks") if "asks" in data.get("d") else []
        asks = [[float(bid.get("p")), float(bid.get("v"))] for bid in asksdata] if asksdata != [] else asksdata
        d = {"timestamp" :  self.process_timestamp(timestamp, 1000), "receive_time" :timestamp/1000, "bids" : bids, "asks" : asks}
        return d

class gateio_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier=None):
        """
            Options multiplier was fetched via api

            https://www.gate.io/help/futures/perpetual/22147/Calculation-of-Position-Value
        """
        if derivate_multiplier == None:
            self.gateio_derivate_multiplier = {
                "option" : {
                    "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.01, 
                },
                "perpetual_future" : {
                    "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.0001, 
                    "BTC_USD" : lambda amount, *args, **kwargs : amount * 0.0001, 
                },
            }
        else:
            self.gateio_derivate_multiplier = derivate_multiplier

    async def gateio_api_option_oi_oioption(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            btc_price_data : dictionary with all prices of bitcoin instruments from every exchange
        """
        data = data.get("list")
        ddd = {}
        for instData in data:
            name_data = instData.get("name").split("-")
            symbol = name_data[0]
            oi = self.gateio_derivate_multiplier.get("option").get(symbol)(instData.get("position_size"))
            strike = float(name_data[2])
            days_left = calculate_option_time_to_expire_gateio(name_data[1])
            side = name_data[-1]
            index_price = market_state.get(f"{symbol}@future@gateio", {}).get("price", 1000000)
            ddd[f"{instData.get('name')}@option@gateio"] = {"symbol" : instData.get("name"), "side" : side, "index_price" : index_price, "strike" : strike, "underlying_price" : index_price, "oi" : oi, "days_left" : days_left}
        return ddd
    
    async def gateio_api_perpetual_future_oi(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            https://www.gate.io/docs/developers/apiv4/en/#futures-stats
        """
        ddd = {}
        for instrument, str_data in data.items():
            if "open_interest_usd" in str_data:
                instrument_data = json.loads(str_data)[0]
                price = instrument_data.get("mark_price")
                oi = instrument_data.get("open_interest_usd") / price
                msid = f"{instrument}@perpetual@gateio"
                ddd[msid] = {"price" : price, "oi" : oi}
                if msid not in market_state:
                    market_state[msid] = {}
                market_state[msid].update(ddd[msid]) 
            if "total_size" in str_data:
                instrument_data = json.loads(str_data)[0]
                sdm = "_".join(instrument.split("_")[:-1])
                price = float(instrument_data.get("mark_price"))
                oi = float(instrument_data.get("total_size"))
                oi = self.gateio_derivate_multiplier.get("perpetual_future").get(sdm)(oi)
                msid = f"{instrument}@future@gateio"
                ddd[msid] = {"price" : price, "oi" : oi}
                if msid not in market_state:
                    market_state[msid] = {}
                market_state[msid].update(ddd[msid])
        ddd["timestamp"] = self.process_timestamp_no_timestamp()         
        return ddd

    async def gateio_api_perpetual_future_tta(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            https://www.gate.io/docs/developers/apiv4/en/#futures-stats
        """
        ddd = {}
        for instrument, instrument_data in data.items():
            instrument_data = json.loads(instrument_data)[0]
            price = instrument_data.get("mark_price")
            oi = instrument_data.get("open_interest_usd") / price
            lsr_taker = instrument_data.get("lsr_taker") # Long/short taker size ratio
            lsr_account = instrument_data.get("lsr_account")   # Long/short account number ratio
            top_lsr_account = instrument_data.get("top_lsr_account") # Top trader long/short account ratio
            top_lsr_size = instrument_data.get("top_lsr_size")   #  	Top trader long/short position ratio
            symbol = instrument
            msid = f"{symbol}@perpetual@gateio"
            ddd[msid]  = {"ttp_size_ratio" : top_lsr_size , "tta_ratio" : top_lsr_account, "gta_ratio" : lsr_account, "gta_size_ratio" : lsr_taker, "price" : price}
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid].update(ddd[msid]) 
        ddd["timestamp"] = self.process_timestamp_no_timestamp()  
        return ddd
    
    async def gateio_api_perpetual_funding(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        ddd = {}
        for instrument, instrument_data in data.items():
            instrument_data = json.loads(instrument_data)[0]
            msid = f"{instrument}@perpetual@gateio"
            ddd[msid]  = {"funding" : float(instrument_data.get("r"))}
            if msid not in market_state:
                market_state[msid] = {}
            market_state[msid].update(ddd[msid]) 
        ddd["timestamp"] = self.process_timestamp_no_timestamp()   
        return ddd

    async def gateio_api_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            side : bids, asks
        """
        d = {}
        d["timestamp"] = self.process_timestamp(data, ["update"], 1000)
        d["receive_time"] = float(data.get("update")) / 1000   
        for side in ["bids", "asks"]:
            d[side] = self.convert_books(data.get(side))
        return d

    async def gateio_api_perpetual_future_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        d = {}
        d["timestamp"] = self.process_timestamp(data, ["update"])
        d["receive_time"] = float(data.get("update"))   
        symbol = connection_data.get("exchange_symbol")
        current_price = (float(data.get("bids")[0].get("p")) + float(data.get("asks")[0].get("p"))) / 2
        for side in ["bids", "asks"]:
            d[side] = self.books_multiplier([[x.get("p"), x.get("s")] for x in data.get(side)], self.gateio_derivate_multiplier.get("perpetual_future").get(symbol), current_price)
        return d

    async def gateio_ws_spot_depth(self, data:dict, market_state:dict,  connection_data:dict, *args, **kwargs):
        data = data.get("result")
        d = {}
        d["receive_time"] = float(data.get("t")) / 1000   
        d["timestamp"] = self.process_timestamp(data, ["t"], 1000)
        for side in ["a", "b"]:
            sss = "asks" if side == "a" else "bids" 
            d[sss] = self.convert_books(data.get(side))
        return d

    async def gateio_ws_perpetual_future_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            side : bids, asks
        """
        d = {}
        data = data.get("result")
        d["timestamp"] = self.process_timestamp(data, ["t"], 1000)
        d["receive_time"] = float(data.get("t")) / 1000   
        symbol = data.get("s")
        current_price = (float(data.get("a")[0].get("p")) + float(data.get("b")[0].get("p"))) / 2
        for side in ["a", "b"]:
            sss = "asks" if side == "a" else "bids" 
            d[sss] = self.books_multiplier([[x.get("p"), x.get("s")] for x in data.get(side)], self.gateio_derivate_multiplier.get("perpetual_future").get(symbol), current_price)
        return d

    async def gateio_ws_spot_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            side : bids, asks
        """
        data = data.get("result")
        trades = []
        liquidations = []
        timestamp = self.process_timestamp(data, ["create_time"])
        receive_time = float(data.get("create_time"))  
        side = data.get("side")
        amount =  float(data.get("amount"))
        price = float(data.get("price"))
        trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "quantity" : amount})

        msid = f"{connection_data.get('exchange_symbol')}@spot@gateio"
        if msid not in market_state:
            market_state[msid] = {}
        market_state[msid]["price"] = price

        return {"liquidations" : liquidations, "trades" : trades, "receive_time" : receive_time}

    async def gateio_ws_perpetual_future_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        """
            https://www.gate.io/docs/developers/futures/ws/en/#trades-notification
        """
        msid = f"{connection_data.get('exchange_symbol')}@spot@gateio"
        if msid not in market_state:
            market_state[msid] = {}

        data = data.get("result")
        trades = []
        liquidations = []
        for trade in data:
            timestamp = self.process_timestamp(trade, ["create_time"])
            receive_time = float(trade.get("create_time"))
            side = "sell" if trade.get("size") < 0 else "buy"
            amount =  abs(float(trade.get("size")))
            price = float(trade.get("price"))
            if "is_internal" in trade and trade.get("is_internal") is True:
                liquidations.append({"side" : side, "timestamp" : timestamp, "price" : price, "quantity" : amount})
            else:
                trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "quantity" : amount})
            market_state[msid]["price"] = price

        return {"liquidations" : liquidations, "trades" : trades, "receive_time" : receive_time}

class coinbase_on_message(on_message_helper):

    def __init__ (self):
        pass

    async def coinbase_api_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        helper_list = []
        timestamp = None

        for prefix, event, value in ijson.parse(data):
            if prefix == "pricebook.time":
                timestamp = value

        for prefix, event, value in ijson.parse(data):
            if prefix == "pricebook.asks.item.price":
                helper_list.append(float(value))
            if prefix == "pricebook.asks.item.size":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "pricebook.bids.item.price":
                helper_list.append(float(value))
            if prefix == "pricebook.bids.item.size":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []

        timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")

        d = {"timestamp" :  self.process_timestamp_no_timestamp(), "receive_time" :time.time(), "bids" : bids, "asks" : asks}
        return d

    async def coinbase_ws_spot_depth(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        bids = []
        asks = []
        helper_list = []
        timestamp = None

        for prefix, event, value in ijson.parse(data):
            if prefix == "events.item.updates.item.event_time":
                timestamp = value
                break
        
        side = ""

        for prefix, event, value in ijson.parse(data):
            if prefix == "events.item.updates.item.price_level"  and side == "bid":
                helper_list.append(float(value))
            if prefix == "events.item.updates.item.new_quantity" and side == "bid":
                helper_list.append(float(value))
                helper_list = []
                bids.append(helper_list)
            if prefix == "events.item.updates.item.price_level" and side == "offer":
                helper_list.append(float(value))
            if prefix == "events.item.updates.item.new_quantity" and side == "offer":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            if prefix == "events.item.updates.item.side":
                side = value

        timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        receive_time = datetime.strptime(data.get("timestamp"), "%Y-%m-%dT%H:%M:%S.%fZ")

        d = {"timestamp" :  timestamp, "receive_time" :receive_time, "bids" : bids, "asks" : asks}
        return d

    async def coinbase_ws_spot_trades(self, data:dict, market_state:dict, connection_data:dict, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        data = data.get("events")[0].get("trades")
        msid = f"{connection_data.get('exchange_symbol')}@spot@coinbase"
        if msid not in market_state:
            market_state[msid] = {}
        for trade in data:
            timestamp = datetime.strptime(trade.get("time"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
            receive_time = datetime.strptime(trade.get("time"), "%Y-%m-%dT%H:%M:%S.%fZ")
            side = trade.get("side").lower()
            amount =  float(trade.get("size"))
            price = float(trade.get("price"))
            trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "quantity" : amount})
            market_state[msid]["price"] = price

        return {"liquidations" : liquidations, "trades" : trades, "receive_time" : receive_time}

class on_message(binance_on_message, bybit_on_message, okx_on_message, deribit_on_message, bitget_on_message, 
                 bingx_on_message, htx_on_message, kucoin_on_message, mexc_on_message, gateio_on_message, coinbase_on_message):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        bybit_on_message.__init__(self, *args, **kwargs)
        okx_on_message.__init__(self, *args, **kwargs)
        deribit_on_message.__init__(self, *args, **kwargs)
        bitget_on_message.__init__(self, *args, **kwargs)
        bingx_on_message.__init__(self, *args, **kwargs)
        htx_on_message.__init__(self, *args, **kwargs)
        kucoin_on_message.__init__(self, *args, **kwargs)
        mexc_on_message.__init__(self, *args, **kwargs)
        gateio_on_message.__init__(self, *args, **kwargs)
        coinbase_on_message.__init__(self, *args, **kwargs)

    def get_methods(self):
        return [method for method in dir(self) if callable(getattr(self, method)) and not method.startswith("__")]

import sys
import asyncio
directory_path = "C:\coding\SatoshiVault\producers"
directory_path = "/workspaces/fastmoonStreams/producers"
sys.path.append(directory_path)

from clients import gateio

cd = gateio.gateio_build_api_connectionData("perpetual", "tta", "BTC", 15, special_method="posfutureperp")
cd = cd.get("api_call_manager")
asyncio.run(cd.get_symbols())
asyncio.run(cd.aiomethod())
data = cd.data

# for k, e in data.items():
#     print(k, e)
#     print("-------")

# data = json.dumps(json.load(open("C:/coding/SatoshiVault/producers/mockdb/coinbase/coinbase_api_spot_depth_btcusd.json"))[0])

# my_object = on_message()

# md = {}
# cd = {}
# async def sss():
#     d = await my_object.coinbase_api_spot_depth(data, md, {"exchange_symbols" : ["BTC-USDT"]})  
#     print(d)

# asyncio.run(sss())
