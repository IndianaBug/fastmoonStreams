from datetime import datetime
import time
import sys
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
module_directory = os.path.join(current_directory, '')
sys.path.append(module_directory)

from ProcessCenter.utilis import *
from typing import Dict, List, Tuple, Union, Callable, Any, Optional
import ijson
import rapidjson as json
import gzip

from config import (
    backup_symbols,
    default_price_value,
    binance_inverse_multipliers, 
    binance_option_multipliers,
    okx_future_multipliers, 
    okx_option_multipliers,
    okx_liquidations_inst_types,
    okx_liquidations_symbol,
    deribit_future_multipliers,
    deribit_option_multipliers,
    kucoin_future_multipliers,
    mexc_future_multipliers,
    gateio_future_multipliers,
    gateio_option_multipliers,
)

class on_message_helper():
    """
        return datatypes by metric:
            
            depth: {
                "bids" : [[price, amount]...], 
                "asks" : [[price, amount]...], 
                "timestamp" : unix
                }
            trades/liquidations: {
                "trades" : [{"side" : str, "amount" : float, "price" : float, "timestamp" : unix} ... ],
                "liquidations" : [{"side" : str, "amount" : float, "price" : float, "timestamp" : unix} ... ],
                "timestamp" : unix
                }
            oi/funding/optionoi/tta/ttp/gta/oifunding : {
                                                symbol : {"metric" : value, "metric_2" : value, ... "timestamp" : unix},
                                                "symbol_2, : {"metric" : value, "metric_2" : value, ... "timestamp" : unix},
                                                .... 
                                                }

    """
    default_price_value = default_price_value

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

    def __init__ (self):
        """
            https://www.binance.com/en/support/faq/binance-coin-margined-futures-contract-specifications-a4470430e3164c13932be8967961aede
            https://www.binance.com/en/support/faq/binance-options-contract-specifications-cdee5d43b70d4d2386980d41786a8533
        """
        self.backup_symbol_binance = backup_symbols.get("binance")
        self.binance_inverse_multipliers = binance_inverse_multipliers
        self.binance_option_multipliers = binance_option_multipliers
    
    def binance_future_multiplier(self, symbol, amount, price, *args, **kwargs):
        msymbol = "BTC" if "BTC" in symbol else "other"
        multiplier = self.binance_inverse_multipliers[msymbol]
        return amount * multiplier / price
    
    def binance_option_multiplier(self, symbol, amount, *args, **kwargs):
        multiplier = self.binance_inverse_multipliers[symbol]
        return amount * multiplier 
    
    async def binance_api_spot_depth(self, data:str, *args, **kwargs): 
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : time.time(), "bids" : bids, "asks" : asks}
        return d

    async def binance_api_perpetual_future_linear_depth(self, data:str, *args, **kwargs):  #-> 'on_message_helper.depth':
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
                bids.append(helper_list)
                helper_list = []
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "E":
                timestamp = float(value)
                break
        
        d = {"timestamp" : timestamp/1000,  "bids" : bids, "asks" : asks}
        return d

    async def binance_api_perpetual_future_inverse_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): # -> 'on_message_helper.depth':
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None
        symbol = None
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "T":
                timestamp = float(value)
            if prefix == "symbol":
                symbol = value
            if timestamp != None and symbol != None:
                break

        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@binance"
        
        backup_price =  market_state.get_data("price_future", self.backup_symbol_binance, self.default_price_value)
        current_price = market_state.get_data("price_future", imid, backup_price)
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                amount = self.binance_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                bids.append(helper_list)
                helper_list = []
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                amount = self.binance_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        

        d = {"timestamp" : timestamp/1000,  "bids" : bids, "asks" : asks}
        return d

    async def binance_ws_spot_perpetual_future_linear_depth(self, data:str,  *args, **kwargs): # -> 'on_message_helper.depth':
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = ""

        for prefix, event, value in ijson.parse(data):
            if prefix == "E":
                timestamp = float(value)
                break

        for prefix, event, value in ijson.parse(data):
            if prefix == "b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "b.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "a.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event


        return {"timestamp" : timestamp/1000, "bids" : bids, "asks" : asks}
    
    async def binance_ws_perpetual_future_inverse_depth(self, data:str, market_state, connection_data, *args, **kwargs): # -> 'on_message_helper.depth':
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None
        symbol = None
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "T":
                timestamp = float(value)
            if prefix == "s":
                symbol = value
            if timestamp != None and symbol != None:
                break
        
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@binance"
        backup_price =  market_state.get_data("price_future", self.backup_symbol_binance, self.default_price_value)
        current_price = market_state.get_data("price_future", imid, backup_price)

        for prefix, event, value in ijson.parse(data):
            if prefix == "b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "b.item.item" and previous_map_event == "string":
                amount = self.binance_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                bids.append(helper_list)
                helper_list = []
            if prefix == "a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "a.item.item" and previous_map_event == "string":
                amount = self.binance_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        d = {"timestamp" : timestamp/1000, "bids" : bids, "asks" : asks}
        return d

    async def binance_ws_spot_perpetual_future_option_linear_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): # -> 'on_message_helper.trades_liquidations':

        data = json.loads(data)
        symbol = data.get("s")
        instType = connection_data.get("instType") or connection_data.get("instTypes") 
        msid = f"{symbol}@{instType}@binance"
        quantity = float(data.get("q"))
        price = float(data.get("p"))
        side = "buy" if data.get("m") is True else "sell"
        timestamp = float(data.get("E")) / 1000
        
        if instType != "option":
            instType = "future" if instType == "perpetual" else instType
            market_state.input_data(f"price_{instType}", msid, price)

        return {"trades" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "liquidations" : [], "timestamp" : timestamp}

    async def binance_ws_perpetual_future_inverse_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): # -> 'on_message_helper.trades_liquidations':
        data = json.loads(data)
        symbol = data.get("s")
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        msid = f"{symbol}@{instType}@binance"
        price = float(data.get("p"))
        quantity = self.binance_future_multiplier(symbol, float(data.get("q")), price)
        side = "buy" if data.get("m") is True else "sell"
        timestamp = float(data.get("E")) / 1000
        market_state.input_data("price_future", msid, price)
        receive_time = float(data.get("E")) / 1000
        return {"trades" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "liquidations" : [], "timestamp" : receive_time}

    async def binance_ws_option_liquidations(self, data:str, *args, **kwargs): 
        data = json.loads(data)
        quantity = float(data.get("o").get("q"))
        price = float(data.get("o").get("p"))
        side = data.get("o").get("S").lower()
        timestamp = float(data.get("E")) / 1000
        r =  {"liquidations" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "trades" : [], "timestamp" : timestamp}
        return r

    async def binance_ws_perpetual_future_linear_liquidations(self, data:str, *args, **kwargs):
        data = json.loads(data)
        quantity = float(data.get("o").get("q"))
        price = float(data.get("o").get("p"))
        side = data.get("o").get("S").lower()
        timestamp = float(data.get("E")) / 1000
        r =  {"liquidations" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "trades" : [], "timestamp" : timestamp}
        return r

    async def binance_ws_perpetual_future_inverse_liquidations(self, data:str, market_state, connection_data, *args, **kwargs): # -> 'on_message_helper.trades_liquidations':
        data = json.loads(data)
        symbol = data.get("o").get("ps")
        price = float(data.get("o").get("p"))
        quantity = self.binance_future_multiplier(symbol, float(data.get("o").get("q")), price)
        side = data.get("o").get("S").lower()
        timestamp = float(data.get("E")) / 1000
        receive_time = float(data.get("E")) / 1000
        r = {"liquidations" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "trades" : [], "timestamp" : receive_time}
        return r

    async def binance_api_perpetual_linear_inverse_oi_oifutureperp(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): # -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        oidata = json.loads(data)
        symbol = oidata.get("symbol")
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        msid = f"{symbol}@{instType}@binance"
        price =  market_state.get_data("price_future", self.backup_symbol_binance, self.default_price_value)
        amount = float(oidata.get("openInterest"))

        if "_PERP" in symbol:
            amount = self.binance_future_multiplier(symbol, amount, price)
        processed_data = {msid : {"oi" : amount, "price" : price, "timestamp" : time.time()}}    
        market_state.input_data("oi_future", msid, amount)
        return processed_data

    async def binance_api_oioption_oi_option(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            https://www.binance.com/en/support/faq/binance-options-contract-specifications-cdee5d43b70d4d2386980d41786a8533
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []

        symbol = connection_data.get("instrument") or connection_data.get("instruments")
        
        backup_price =  market_state.get_data("price_future", self.backup_symbol_binance, self.default_price_value)


        for prefix, event, value in ijson.parse(data):
            if prefix == "item.symbol":
                option_data = value.split("-")
                msids.append(f"{value}@option@binance")
                symbols.append(value)
                strikes.append(float(option_data[2]))
                days_left.append(binance_option_timedelta(option_data[1]))
            if prefix == "item.sumOpenInterest":
                amount = self.binance_option_multiplier(symbol, float(value))
                ois.append(amount)
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": int(days_left[i]),
                "oi": ois[i],
                "price":  backup_price,
            }
        instruments_data["timestamp"] = time.time()

        return instruments_data
        
    async def binance_api_posfutureperp_perpetual_future_linear_inverse_gta_tta_ttp(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): # -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        data = json.loads(data)
        objective = data.get("objective")
        data = data.get("data")[0]
        symbol = data.get("symbol") if "symbol" in data else data.get("pair")
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        msid = f"{symbol}@{instType}@binance"
        
        longAccount = float(data.get("longAccount")) if "longAccount" in data else float(data.get("longPosition"))
        shortAccount = float(data.get("shortAccount")) if "shortAccount" in data else float(data.get("shortPosition"))
        longShortRatio = float(data.get("longShortRatio"))
        
        market_state.input_data(f"{objective}_long_ratio", msid, longAccount)
        market_state.input_data(f"{objective}_short_ratio", msid, shortAccount)
        market_state.input_data(f"{objective}_ratio", msid, longShortRatio)

        pos_data = {msid : {f"{objective}_long_ratio" : longAccount, 
                            f"{objective}_short_ratio" : shortAccount,
                             f"{objective}_ratio" : longShortRatio, 
                             "timestamp" : time.time()} }
        return pos_data    

    async def binance_api_fundperp_perpetual_funding_linear_inverse(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): # -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        funddata = json.loads(data)[0]
        symbol = funddata.get("symbol")
        funding = funddata.get("fundingRate")
        msid = f"{symbol}@perpetual@binance"
        market_state.input_data(f"funding", msid, float(funding))
        processeda_data = {msid : {"funding" : float(funding), "timestamp" : time.time()}}
        return processeda_data

class bybit_on_message(on_message_helper):

    def __init__ (self):
        """
            https://www.bybit.com/en/announcement-info/transact-parameters
        """
        self.backup_symbol_bybit = backup_symbols.get("bybit")

    def bybit_future_multiplier(self, symbol, amount, price, *args, **kwargs):
        if "USD" in symbol and "USDT" not in symbol:
            return amount / price
        else:
            return amount

    async def bybit_api_fundperp_linear_inverse_perpetual_funding_future(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        d = {}
        funddata = json.loads(data).get("result").get("list")[0]
        instrument = funddata.get("symbol")
        msid = f"{instrument}@perpetual@bybit"
        funding = float(funddata.get("fundingRate"))
        d[msid] = {"funding" : funding, "timestamp" : time.time()}        
        market_state.input_data(f"funding", msid, funding)
        return d

    async def bybit_api_oifutureperp_linear_inverse_perpetual_future_oi(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        d = {}
        oidata = json.loads(data)
        symbol = oidata.get("result").get("symbol")
        instType = "future" if len(symbol.split("-")) == 2 else "perpetual"
        oi = float(oidata.get("result").get("list")[0].get("openInterest"))
        msid = f"{symbol}@{instType}@bybit"
        price =  market_state.get_data("price_future", self.backup_symbol_bybit, self.default_price_value)
        oi = self.bybit_future_multiplier(symbol, oi, price)
        market_state.input_data(f"oi_future", msid, oi)
        d[msid] = {"oi" : oi, "price" : price, "timestamp" : time.time()}    
        return d

    async def bybit_api_posfutureperp_perpetual_linear_inverse_future_gta(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        d = {}
        posdata = json.loads(data)
        symbol = posdata.get("result").get("list")[0].get("symbol")
        msid = f"{symbol}@perpetual@bybit"
        buyRatio = float(posdata.get("result").get("list")[0].get("buyRatio"))
        sellRatio = float(posdata.get("result").get("list")[0].get("sellRatio"))
        d[msid] = {
            "gta_long_ratio" : buyRatio,
            "gta_short_ratio" : sellRatio
        }
        
        market_state.input_data(f"gta_long_ratio", msid, buyRatio)
        market_state.input_data(f"gta_short_ratio", msid, sellRatio)
        
        d["timestamp"] = time.time()
        return d

    async def bybit_api_spot_linear_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "result.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.b.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "result.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.a.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : time.time(), "bids" : bids, "asks" : asks}
        return d    

    async def bybit_api_inverse_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
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
        
        instType = "future" if symbol.split("-")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@bybit"
        backup_price =  market_state.get_data("price_future", self.backup_symbol_bybit, self.default_price_value)
        current_price = market_state.get_data("price_future", imid, backup_price)
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.b.item.item" and previous_map_event == "string":
                amount = self.bybit_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                bids.append(helper_list)
                helper_list = []
            if prefix == "result.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.a.item.item" and previous_map_event == "string":
                amount = self.bybit_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : float(timestamp) / 1000,  "bids" : bids, "asks" : asks}
        return d

    async def bybit_ws_spot_linear_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None 

        for prefix, event, value in ijson.parse(data):
            if prefix == "ts":
                timestamp = float(value)
            if prefix == "data.s":
                symbol = value

                
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.b.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.a.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        
        d = {"timestamp" : timestamp / 1000, "bids" : bids, "asks" : asks}
        return d

    async def bybit_ws_inverse_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        timestamp = None        
        symbol = None       

        for prefix, event, value in ijson.parse(data):
            if prefix == "ts":
                timestamp = float(value)
            if prefix == "data.s":
                symbol = value
            if timestamp != None and symbol != None:
                break

        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        
        imid = f"{symbol}@{instType}@bybit"
        backup_price =  market_state.get_data("price_future", self.backup_symbol_bybit, self.default_price_value)
        current_price = market_state.get_data("price_future", imid, backup_price)
                
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.b.item.item" and previous_map_event == "string":
                amount = self.bybit_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.a.item.item" and previous_map_event == "string":
                amount = self.bybit_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        
        d = {"timestamp" : timestamp / 1000, "bids" : bids, "asks" : asks}
        return d

    async def bybit_ws_linear_spot_perpetual_future_option_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        data = json.loads(data)
        trades = []
        liquidations = []
        for trade in data.get("data"):
            timestamp = float(trade.get("T")) / 1000
            receive_time = float(trade.get("T")) / 1000
            side = trade.get("S").lower()
            price = float(trade.get("p"))
            size = float(trade.get("v"))
            trades.append({"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp})

            symbol = trade.get("s")
            instType = "perpetual" if len(symbol.split("_")) == 1 else "future"
            instType = "option" if len(symbol.split(symbol)) > 3 else instType
            msid = f"{symbol}@{instType}@bybit"
            
            if instType != "option":
                d = "future" if instType == "perpetual" else instType
                market_state.input_data(f"price_{d}", msid, price)
                    
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}
        
    async def bybit_ws_inverse_perpetual_future_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        for trade in data.get("data"):
            symbol = trade.get("s")
            timestamp = float(trade.get("T")) / 1000
            side = trade.get("S").lower()
            price = float(trade.get("p"))
            size = self.bybit_future_multiplier(symbol, float(trade.get("v")), price)
            trades.append({"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp})
            instType = "perpetual" if len(symbol.split("_")) == 1 else "future"
            instType = "option" if len(symbol.split(symbol)) > 3 else instType
            msid = f"{symbol}@{instType}@bybit"
            market_state.input_data(f"price_future", msid, price)

        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : timestamp}

    async def bybit_ws_linear_perpetual_future_option_liquidations(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        trade = data.get("data")
        timestamp = float(trade.get("updatedTime")) / 1000
        receive_time = float(trade.get("updatedTime")) / 1000
        side = trade.get("side").lower()
        price = float(trade.get("price"))
        size = float(trade.get("size"))
        liquidations.append({"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp})
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}

    async def bybit_ws_inverse_perpetual_future_liquidations(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        data = json.loads(data)
        trades = []
        liquidations = []
        trade = data.get("data")
        symbol = trade.get("symbol")
        timestamp = float(trade.get("updatedTime")) / 1000
        receive_time = float(trade.get("updatedTime")) / 1000
        side = trade.get("side").lower()
        price = float(trade.get("price"))
        size = self.bybit_future_multiplier(symbol, float(trade.get("size")), price)
        liquidations.append({"side" : side, "price" : price, "quantity" : size, "timestamp" : timestamp})
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}

    async def bybit_api_oioption_oi_option(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): # -> Tuple[np.array, np.array, np.array, float, str]:
        """
            https://blog.bybit.com/post/everything-you-need-to-know-about-bybit-s-usdc-options-blt905124bb9461ab21/
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []
        underlying_prices = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "result.list.item.symbol":
                option_data = value.split("-")
                msids.append(f"{value}@option@bybit")
                symbols.append(value)
                strikes.append(float(option_data[2]))
                days_left.append(calculate_option_time_to_expire_bybit(option_data[1]))
            if prefix == "result.list.item.openInterest":
                ois.append(float(value))
            if prefix == "result.list.item.underlyingPrice":
                underlying_prices.append(float(value))
                
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": int(days_left[i]),
                "oi": ois[i],
                "price" : underlying_prices[i],
            }
        instruments_data["timestamp"] =  time.time()
        return instruments_data

class okx_on_message(on_message_helper):

    okx_inst_type_map = {
        "SWAP" : "perpetual",
        "FUTURES" : "future",
        "OPTION" : "option",
        "SPOT" : "spot"
    }

    def __init__ (self):
        """
            https://www.okx.com/trade-market/info/futures
            https://www.okx.com/help/i-okx-options-introduction
        """
        self.okx_liquidation_symbol = okx_liquidations_symbol
        self.backup_symbol_okx = backup_symbols.get("okx")
        self.okx_multipliers = okx_future_multipliers
        self.okx_option_multipliers = okx_option_multipliers
    
    def okx_future_multiplier(self, symbol, amount, price, *args, **kwargs):
        base_coin = symbol.split("-")[0]
        margin_coin = symbol.split("-")[1]
        multiplier = self.okx_multipliers.get(margin_coin).get(base_coin)
        if callable(multiplier):
            return multiplier(amount)
        else:
            return amount * multiplier / price
    
    def okx_option_multiplier(self, symbol, amount, *args, **kwargs):
        base_coin = symbol.split("-")[0]
        multiplier = self.okx_option_multipliers.get(base_coin)
        return amount * multiplier


    async def okx_api_fundperp_perpetual_future_funding(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
        """
        d = {}
        funddata = json.loads(data).get("data")[0]
        symbol = funddata.get("instId")
        msid = f"{symbol}@perpetual@okx"
        funding = float(funddata.get("fundingRate"))
        d[msid] = {"funding" : funding, "timestamp" : time.time()}
        market_state.input_data(f"funding", msid, funding)
        return d

    async def okx_api_gta_perpetual_future(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
        """
        symbol = connection_data.get("instrument") or connection_data.get("instruments")
        label = f"{symbol}@perpetual@okx" 
        count = 0
        for prefix, event, value in ijson.parse(data):
            if event == "string":
                count += 1
            if prefix == "data.item.item" and count == 2:
                timestamp = value
            if prefix == "data.item.item" and count == 3:
                gta = float(value)
                break
        d = {label : {"gta_ratio" : gta, "timestamp" : time.time()}}            
        market_state.input_data(f"gta_ratio", label, gta)
        return d

    async def okx_api_oifutureperp_perpetual_future_oi(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
        """
        price = market_state.get_data("price_future", self.backup_symbol_okx, self.default_price_value)
        d = {}
        oidata = json.loads(data)
        symbol = oidata.get("data")[0].get("instId")
        instType = "perpetual" if "SWAP" in symbol else "future"
        msid = f"{symbol}@{instType}@okx"
        oi = float(oidata.get("data")[0].get("oiCcy"))
        # price = market_state.get_data("price_future", msid, backup_price)
        d[msid] = {"oi" : oi, "price" : price, "timestamp" : time.time()}
        market_state.input_data(f"oi_future", msid, oi)
        return d

    async def okx_api_option_oi(self, data:str, market_state:dict, connection_data:str, *args, **kwargs): 
        """
            https://www.okx.com/help/i-okx-options-introduction
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []

        backup_price =  market_state.get_data("price", self.backup_symbol_okx, self.default_price_value)

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.instId":
                option_data = value.split("-")
                msids.append(f"{value}@option@okx")
                symbols.append(value)
                strikes.append(float(option_data[-2]))
                days_left.append(calculate_option_time_to_expire_okx(option_data[2]))
            if prefix == "data.item.oi":
                symbol = "-".join(option_data[:2])
                oi = float(value)
                ois.append(self.okx_option_multiplier(symbol, oi))
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": int(days_left[i]),
                "oi": ois[i],
                "price" : backup_price
            }
        instruments_data["timestamp"] = time.time()
        return instruments_data

    async def okx_api_ws_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
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
                bids.append(helper_list)
                helper_list = []
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

        d = {"timestamp" : time.time(), "bids" : bids, "asks" : asks }
        return d
    
    async def okx_api_ws_linear_inverse_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
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
        instType = "future" if symbol.split("_")[-1].isdigit() else "perpetual"
        imid = f"{symbol}@{instType}@okx"
        
        backup_price =  market_state.get_data("price_future", self.backup_symbol_okx, self.default_price_value)
        current_price = market_state.get_data("price_future", imid, backup_price)

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.item.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
                string_count += 1
            if prefix == "data.item.bids.item.item" and previous_map_event == "string" and string_count == 1:
                amount = self.okx_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)                
                bids.append(helper_list)
                helper_list = []
                string_count = 0
            if prefix == "data.item.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
                string_count += 1
            if prefix == "data.item.asks.item.item" and previous_map_event == "string"  and string_count == 1:
                amount = self.okx_future_multiplier(symbol, float(value), current_price)
                helper_list.append(amount)   
                asks.append(helper_list)
                helper_list = []
                string_count = 0
            previous_map_event = event

        d = {"timestamp" : time.time(), "bids" : bids, "asks" : asks}
        return d

    async def okx_ws_option_trades_optionTrades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
        """
        data = json.loads(data)
        trades = []
        liquidations = []        
        for trade in data.get("data"):
            side = trade.get('side')
            price =float(trade.get('idxPx'))
            receive_time = float(trade.get("ts")) / 1000
            amount = float(trade.get('fillVol'))
            trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : receive_time})
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}   
    
    async def okx_ws_spot_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []           
        for trade in data.get("data"):
            side = trade.get('side')
            price =float(trade.get('px'))
            timestamp = float(trade.get("ts")) / 1000
            receive_time = float(trade.get("ts")) / 1000
            amount = float(trade.get('sz'))
            trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})
            msid = f"{trade.get('instId')}@spot@okx"
            market_state.input_data(f"price_spot", msid, price)
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}     
    
    async def okx_ws_linear_inverse_perpetual_future_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []           
        for trade in data.get("data"):
            symbol = trade.get('instId')
            side = trade.get('side')
            price =float(trade.get('px'))
            timestamp = float(trade.get("ts")) / 1000
            receive_time = float(trade.get("ts")) / 1000
            amount = self.okx_future_multiplier(symbol, float(trade.get('sz')), price)
            trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp}) 
            instType = connection_data.get("instType")
            msid = f"{symbol}@{instType}@okx"
            market_state.input_data(f"price_future", msid, price)

        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}          

    async def okx_ws_future_perpetual_option_liquidations(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        target_inst_type = connection_data.get("instType") or connection_data.get("instTypes")
        trades = []
        liquidations = []     
        for liq_by_inst in data.get("data"):
            this_inst_type = liq_by_inst.get("instType")
            this_inst_type = self.okx_inst_type_map.get(this_inst_type)
            if this_inst_type in okx_liquidations_inst_types:
                instId = liq_by_inst.get("instId")
                if okx_liquidations_symbol in instId and this_inst_type in target_inst_type:
                    multiplier_symbol = liq_by_inst.get('instFamily')
                    for liquidation in liq_by_inst.get("details"):
                        side = liquidation.get('side')
                        price =float(liquidation.get('bkPx'))
                        timestamp = float(liquidation.get("ts")) / 1000
                        helper = "perpetual@future" if this_inst_type != "option" else "option"
                        amount = float(liquidation.get("sz"))
                        amount = self.okx_derivate_multiplier.get(helper).get(multiplier_symbol)(amount, price)
                        liquidations.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})
        r = {"trades" : trades, "liquidations" : liquidations, "timestamp" : time.time()}   
        return r

class deribit_on_message(on_message_helper):

    def __init__ (self):
        """
            https://www.deribit.com/kb/deribit-linear-perpetual
            https://static.deribit.com/files/USDCContractSpecsandmargins.pdf
        """
        self.backup_symbol_deribit = backup_symbols.get("deribit")
        self.deribit_option_multipliers= deribit_option_multipliers
        self.deribit_future_multipliers = deribit_future_multipliers
    
    def deribit_option_multiplier(self, symbol, amount, *args, **kwargs):
        basecoin = symbol.split("-")[0]
        multiplier = self.deribit_option_multipliers.get(basecoin)
        return amount * multiplier

    def deribit_future_multiplier(self, symbol, amount, price, *args, **kwargs):
        inst_type = "perpetual" if "PERPETUAL" in symbol else "future"
        symbol = symbol.split("-")[0] if inst_type == "future" else symbol
        multiplier_function = self.deribit_future_multipliers.get(inst_type).get(symbol)
        return multiplier_function(amount, price)

    async def deribit_api_option_oi_oifunding(self, data:str, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
        """
            https://static.deribit.com/files/USDCContractSpecsandmargins.pdf
        """
        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []
        underlying_prices = []
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.item.base_currency":
                base_currency = value
            if prefix == "result.item.instrument_name":
                option_data = value.split("-")
                msids.append(f"{value}@option@deribit")
                symbols.append(value)
                strikes.append(float(option_data[2]))
                days_left.append(calculate_option_time_to_expire_deribit(option_data[1]))
            if prefix == "result.item.open_interest":
                oi = self.deribit_option_multiplier(base_currency, float(value))
                ois.append(oi)
            if prefix == "result.item.underlying_price":
                underlying_prices.append(float(value))
                
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": int(days_left[i]),
                "oi": ois[i],
                "price" : underlying_prices[i],
            }
        instruments_data["timestamp"] = time.time()
        return instruments_data

    async def deribit_api_perpetual_future_oi_funding_oifunding(self, data:str, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
        msids = []
        symbols = []
        prices = []
        ois = []
        fundings_symbols = []
        fundings_values = []

        backup_price = market_state.get_data("price_future", self.backup_symbol_deribit, self.default_price_value)

        helper_dict = {}

        for prefix, event, value in ijson.parse(data):
            if prefix == "result.item.instrument_name":
                if value != None:
                    instType = "future" if any(char.isdigit() for char in value.split("-")[-1]) else "perpetual"
                    msids.append(f"{value}@{instType}@deribit")
                    helper_dict["instrument_name"] = value
            if prefix == "result.item.mid_price":
                if value != None:
                    helper_dict["mid_price"] = float(value)
                    prices.append(float(value))
            if prefix == "result.item.open_interest":
                if value != None:
                    helper_dict["open_interest"] = float(value)
            if len(helper_dict) == 3:
                oi = self.deribit_future_multiplier(helper_dict.get("instrument_name"), helper_dict.get("open_interest"),helper_dict.get("mid_price"))
                ois.append(oi)
                helper_dict = {}
            
        counter_2 = 0
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.item.funding_8h":
                if value != None:
                    fundings_symbols.append(msids[counter_2])
                    fundings_values.append(float(value))

                
        instruments_data = {x : {} for x in msids}

        for index in range(len(msids)):
            s = msids[index].split('-')[0]
            oi = self.deribit_derivate_multiplier.get(s)(ois[index], prices[-1], "oifuture")
            instruments_data[msids[index]] = {
                "oi": oi,
                "price" : backup_price,
                "timestamp" : time.time(),
                "funding" : 0.0
            }       
            market_state.input_data("oi_future", msids[index], oi)
            market_state.input_data("price_future", msids[index], prices[index])
        
        for index in range(len(fundings_symbols)):
            instruments_data[fundings_symbols[index]]["funding"] = fundings_values[index]
            market_state.input_data("funding", fundings_symbols[index], fundings_values[index])
        
        return instruments_data

    async def deribit_ws_future_perpetual_linear_inverse_option_trades_tradesagg_liquidations(self, data:str, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
        """
            https://docs.deribit.com/#trades-kind-currency-interval -- contains liquidations
        """
        data = json.loads(data)
        trades = []
        liquidations = []
        for trade in data.get("params").get("data"):
            symbol = trade.get("instrument_name")
            side = trade.get("direction")
            price = float(trade.get("price"))
            amount = self.deribit_future_multiplier(symbol, float(trade.get("amount")), price)
            timestamp = float(trade.get("timestamp")) / 1000
            receive_time = float(trade.get("timestamp")) / 1000
            if "liquidation" not in trade:
                trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})
            if "liquidation" in trade:
                liquidations.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})

            instType = "future" if any(char.isdigit() for char in trade.get("instrument_name").split("-")[-1]) else "perpetual"
            instType = "option" if len(trade.get("instrument_name").split("-")) > 2 else instType
            msid = f"{trade.get('instrument_name')}@{instType}@deribit"
            
            if instType != "option":
                market_state.input_data("price_future", msid, price)
        r = {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}
            
        return r

    async def deribit_api_perpetual_future_depth(self, data:str, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:
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
                amount = self.deribit_future_multiplier(symbol, float(value), price)
                helper_list.append(amount)
                bids.append(helper_list)
                helper_list = []
            if prefix == "result.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.asks.item.item" and previous_map_event == "number":
                amount = self.deribit_future_multiplier(symbol, float(value), price)
                helper_list.append(amount)
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : time.time(), "bids" : bids, "asks" : asks}
        return d
        
    async def deribit_ws_perpetual_future_depth(self, data:str, market_state:dict, connection_data: dict, *args, **kwargs)-> dict:

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
        imid = f"{symbol}@{instType}@deribit"
        
        backup_price = market_state.get_data("price", self.backup_symbol_deribit, self.default_price_value)
        price = market_state.get_data("price", imid, backup_price)
        
        for prefix, event, value in ijson.parse(data):
            if prefix == "params.data.bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
            if prefix == "params.data.bids.item.item" and previous_map_event == "number":
                amount = self.deribit_future_multiplier(symbol, float(value), price)
                helper_list.append(amount)
                bids.append(helper_list)
                helper_list = []
            if prefix == "params.data.asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
            if prefix == "params.data.asks.item.item" and previous_map_event == "number":
                amount = self.deribit_future_multiplier(symbol, float(value), price)
                helper_list.append(amount)
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : timestamp / 1000, "receive_time" : timestamp / 1000, "bids" : bids, "asks" : asks}
        return d

class bitget_on_message(on_message_helper):

    def __init__ (self):
        """
            Contract multipliers not needed 
        """
        self.backup_symbol_bitget = backup_symbols.get("bitget")

    async def bitget_api_spot_linear_inverse_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "number":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "number":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event
        return {"timestamp" : time.time(), "bids" : bids, "asks" : asks}

    async def bitget_ws_spot_linear_inverse_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
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
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.item.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.item.asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : timestamp/1000,  "bids" : bids, "asks" : asks}
        return d

    async def bitget_ws_inverse_perpetual_future_spot_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        symbol = data.get("arg").get("instId")
        instType = "spot" if data.get("arg").get("instType") == "SPOT" else "perpetual"
        for trade in data.get("data"):
            side = trade.get("side")
            price = float(trade.get("price"))
            amount = float(trade.get("size"))
            timestamp = float(data.get("ts")) / 1000 
            receive_time = float(data.get("ts")) / 1000 
            trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})

            msid = f"{symbol}@{instType}@bitget"
            pit = "future" if instType == "perpetual" else instType
            market_state.input_data(f"price_{pit}", msid, price)

            
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}

    async def bitget_api_oi_perpetual_oifutureperp(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        instrument_data = json.loads(data).get("data")
        symbol = instrument_data.get("openInterestList")[0].get("symbol")
        msid = f"{symbol}@perpetual@bitget"
        oi = float(instrument_data.get("openInterestList")[0].get("size"))
        market_state.input_data(f"oi_future", msid, oi)
        backup_price =  market_state.get_data("price_future", self.backup_symbol_bitget, self.default_price_value)
        price = market_state.get_data(f"oi_future", msid, backup_price)
        d = {msid : {"oi" : oi, "timestamp" : time.time(), "price" : price}}
        return d

    async def bitget_api_funding_perpetual_fundperp(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            [[side, price, size, timestamp]]
        """
        instrument_data = json.loads(data).get("data")[0]
        symbol = instrument_data.get("symbol")
        msid = f"{symbol}@perpetual@bitget"
        funding = float(instrument_data.get("fundingRate"))
        market_state.input_data(f"funding", msid, funding)
        d = {msid : {"funding" : funding, "timestamp" : time.time()}}
        return d

class bingx_on_message(on_message_helper):

    def __init__ (self, backup_symbol_bingx=None):
        """
            No need, calls provide data in native coin
        """
        self.backup_symbol_bingx = backup_symbols.get("bingx")
        pass
        if not backup_symbol_bingx:
            self.backup_symbol_bingx = "BTC-USDT@perpetual@bingx"
        else:
            self.backup_symbol_bingx = backup_symbol_bingx
        pass

    async def bingx_api_perpetual_linear_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs) -> Tuple[list, str]:
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bidsCoin.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bidsCoin.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.asksCoin.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asksCoin.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  time.time(),  "bids" : bids, "asks" : asks}
        return d

    async def bingx_ws_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):

        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" : time.time(), "bids" : bids, "asks" : asks}
        return d

    async def bingx_api_perpetual_oi(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        timestamp = float(data.get("data").get("time")) / 1000
        openInterest = float(data.get("data").get("openInterest"))
        ss = str(data.get('data').get('symbol'))
        msid = f"{ss}@perpetual@bingx"
        backup_price =  market_state.get_data("price_future", self.backup_symbol_bingx, self.default_price_value)
        price = market_state.get_data(f"oi_future", msid, backup_price)
        oi = openInterest / price
        d = {msid : {"oi" : oi, "timestamp" : time.time(), "price" : price}}
        market_state.input_data(f"oi_future", msid, oi)
        return d

    async def bingx_api_perpetual_funding(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        funding = float(data.get("data").get("lastFundingRate"))
        ss = str(data.get('data').get('symbol'))
        s = f"{ss}@perpetual@bingx"
        d = {s : {"funding" : funding, "timestamp" : time.time()}}
        market_state.input_data(f"funding", s, funding)
        return d
    
    async def bingx_ws_trades_perpetual(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        symbol = data.get("dataType").split("@")[0]
        for trade in data.get("data"):
            side = "buy" if trade.get("m") is True else "sell"
            price = float(trade.get("p"))
            amount = float(trade.get("q"))
            timestamp = float(trade.get("T")) / 1000 
            receive_time = float(trade.get("T")) / 1000 
            trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})

            msid = f"{symbol}@perpetual@bingx"
            market_state.input_data(f"price_future", msid, price)
            
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}
    
    async def bingx_ws_trades_spot(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        trade = data.get("data")
        symbol = trade.get("s")
        side = "buy" if trade.get("m") is True else "sell"
        price = float(trade.get("p"))
        amount = float(trade.get("q"))
        timestamp = float(trade.get("T")) / 1000 
        trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})
        msid = f"{symbol}@spot@bingx"
        market_state.input_data(f"price_spot", msid, price)
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : timestamp}

class htx_on_message(on_message_helper):

    def __init__ (self):
        self.backup_symbol_htx = backup_symbols.get("htx")

    async def htx_api_perpetual_oi(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        d = {}
        data_per_marginType = json.loads(data).get("data")
        for data_instrument in data_per_marginType:
            symbol = data_instrument.get("contract_code")
            oi = float(data_instrument.get("amount"))
            instType = "future" if data_instrument.get("business_type") == "futures" else "perpetual"
            msid = f"{symbol}@{instType}@htx"
            price =  market_state.get_data("price_future", self.backup_symbol_htx, self.default_price_value)
            #price = market_state.get_data(f"oi_future", msid, backup_price)
            d[msid] = {"oi" :  oi, "price" : price, "timestamp" : time.time()}
            market_state.input_data(f"oi_future", msid, oi)
        return d

    async def htx_api_perpetual_pos_posfutureperp_gta(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        d = {}
        indicator_type = "gta"
        pos_data = json.loads(data).get("data")
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
        
        market_state.input_data(f"{indicator_type}_long_ratio", msid, long_ratio)
        market_state.input_data(f"{indicator_type}_short_ratio", msid, short_ratio)


        d["timestamp"] = time.time()
        return d

    async def htx_api_perpetual_funding_fundperp(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        d = {}
        instData = json.loads(data).get("data")[0]
        funding = float(instData.get("funding_rate"))
        contract_code = instData.get("contract_code")
        msid = f"{contract_code}@perpetual@htx"
        d[msid] = {"funding" : funding, "timestamp" : time.time()}
        market_state.input_data("funding", msid, funding)
        return d

class kucoin_on_message(on_message_helper):

    def __init__ (self):
        """
            https://www.kucoin.com/pt/futures/contract/detail/XBTUSDTM
        """
        self.backup_symbol_kucoin = backup_symbols.get("kucoin")

    def kucoin_future_multiplier(self, symbol, amount, price, *args, **kwargs):
        multiplier = kucoin_future_multipliers.get(symbol)
        if callable(multiplier):
            return multiplier(amount, price)
        else:
            return amount * multiplier

    async def kucoin_ws_spot_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        symbol = data.get("data").get("symbol")
        side = data.get("data").get("side")
        price = float(data.get("data").get("price"))
        amount = float(data.get("data").get("size"))
        timestamp = float(data.get("data").get("time")) / 10**9 
        receive_time = float(data.get("data").get("time")) / 10**9 
        trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})

        msid = f"{symbol}@spot@kucoin"
        market_state.input_data("price_spot", msid, price)
            
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}

    async def kucoin_ws_perpetual_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        symbol = data.get("data").get("symbol")
        side = data.get("data").get("side")
        price = float(data.get("data").get("price"))

        amount = self.kucoin_future_multiplier(symbol, float(data.get("data").get("size")), price)
        
        receive_time = float(data.get("data").get("ts")) / 10**9 
        trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : receive_time})

        msid = f"{symbol}@perpetual@kucoin"
        market_state.input_data("price_future", msid, price)            
        return {"trades" : trades, "liquidations" : liquidations, "timestamp" : receive_time}
    
    async def kucoin_api_perpetual_oi_funding_oifunding(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        d = {}
        data = data.get("data")
        symbol = data.get("symbol")
        multiplier = float(data.get("multiplier"))
        oi = float(data.get("openInterest")) * multiplier
        funding = float(data.get("fundingFeeRate"))
        msid = f"{symbol}@perpetual@kucoin"
        backup_price = market_state.get_data("price_future", self.backup_symbol_kucoin, self.default_price_value)
        price = market_state.get_data("price_future", msid, backup_price)
        d[msid] = {"oi" : oi, "funding" : funding, "price" : price, "timestamp" : time.time()}
        market_state.input_data(f"funding", msid, funding)
        market_state.input_data(f"oi_future", msid, oi)
        return d

    async def kucoin_api_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):

        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  time.time(), "bids" : bids, "asks" : asks}
        return d

    async def kucoin_api_perpetual_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        symbol = None
        
        msid = f"{symbol}@perpetual@kucoin"
        backup_price = market_state.get_data("price_future", self.backup_symbol_kucoin, self.default_price_value)
        price = market_state.get_data("price_future", msid, backup_price)
    

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.symbol":
                symbol = value
                break

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "number":
                amount = self.kucoin_future_multiplier(symbol, float(value), price)
                helper_list.append(amount)
                bids.append(helper_list)
                helper_list = []
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "number":
                amount = self.kucoin_future_multiplier(symbol, float(value), price)
                helper_list.append(amount)
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  time.time(),  "bids" : bids, "asks" : asks}
        return d

    async def kucoin_ws_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        d = {}
        for side in ["asks", "bids"]:
            books = [[x[0], x[1]] for x in self.convert_books(data.get("data").get("changes").get(side))]
            d[side] = books
        d["timestamp"] = float(data.get("data").get("time")) / 1000
        return d

    async def kucoin_ws_perpetual_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        
        backup_price = market_state.get_data("price_future", self.backup_symbol_kucoin, self.default_price_value)
        
        d = {}
        symbol = data.get("topic").split(":")[-1]
        msid = f"{symbol}@perpetual@kucoin"
        price = market_state.get_data("price_future", msid, backup_price)
        
        change = data.get("data").get("change").split(",")
        for side in ["asks", "bids"]:
            side2 = "buy" if side == "bids" else "sell"
                        
            books = [[float(change[0]), self.kucoin_future_multiplier(symbol, float(change[-1]), price)]] if side2 == change[1] else [[]]
            d[side] = books

        d["timestamp"] = float(data.get("data").get("timestamp")) / 1000

        return d
    
class mexc_on_message(on_message_helper):

    def __init__ (self):
        """
            https://www.mexc.com/support/articles/17827791509072
        """
        self.backup_symbol_mexc = backup_symbols.get("mexc")

    def mexc_futures_multiply(self, symbol:str, amount:float, price:float, *args, **kwargs):
        multiplier = mexc_future_multipliers.get(symbol)
        if callable(multiplier):
            return multiplier(amount, price)
        else:
            return amount * multiplier

    async def mexc_ws_spot_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = data.get("d").get("deals")
        symbol = data.get("c").split("@")[-1]
        ttt = []
        lll = []
        for trade in trades:
            price = float(trade.get("p"))
            side = "buy" if int(trade.get("S")) == 1 else "sell"
            amount = float(trade.get("v"))
            timestamp = float(trade.get("t")) / 10**3 
            receive_time = float(trade.get("t")) / 10**3 
            ttt.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})

            msid = f"{symbol}@spot@mexc"
            market_state.input_data("price_spot", msid, price)
            
        return {"trades" : ttt, "liquidations" : lll, "timestamp" : receive_time}

    async def mexc_ws_perpetual_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        symbol = data.get("symbol") 
        trade = data.get("data")
        trades = []
        liquidations = []
        price = float(trade.get("p"))
        side = "buy" if int(trade.get("T")) == 1 else "sell"
        amount = self.mexc_futures_multiply(symbol, float(trade.get("v")), price)
        timestamp = float(trade.get("t")) / 10**3 
        receive_time = float(trade.get("t")) / 10**3 
        trades.append({"side" : side, "price" : price, "quantity" : amount, "timestamp" : timestamp})

        msid = f"{symbol}@perpetual@mexc"
        market_state.input_data("price_future", msid, price)
        
        return {"trades" : trades, "liquidations" : [], "timestamp" : receive_time}

    async def mexc_api_perpetual_oi_funding_oifunding(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        
        data = json.loads(data)
        d = {}
        symbol = data.get("data").get("symbol")
        msid = f"{symbol}@perpetual@mexc"

        backup_price = market_state.get_data("price_future", self.backup_symbol_mexc, self.default_price_value)
        price = market_state.get_data("price_future", msid, backup_price)


        oi = self.mexc_futures_multiply(symbol, float(data.get("data").get("holdVol")), price)
        timestamp = time.time()
        funding = float(data.get("data").get("fundingRate"))
        d[msid] = {"oi" : oi, "funding" : funding, "timestamp" : timestamp, "price" : price}
        
        market_state.input_data("funding", msid, funding)
        market_state.input_data("oi_future", msid, oi)

        return d

    async def mexc_api_perpetual_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
    
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []
        number_count = 0

        symbol = connection_data.get("exchange_symbols")[0]
        msid = f"{symbol}@perpetual@mexc"
        backup_price =  market_state.get_data("price_future", self.backup_symbol_mexc, self.default_price_value)
        current_price = market_state.get_data("price_future", msid, backup_price)

        for prefix, event, value in ijson.parse(data):
            if prefix == "data.bids.item.item" and previous_map_event == "start_array":
                number_count += 1
                helper_list.append(float(value))
            if prefix == "data.bids.item.item" and previous_map_event == "number" and number_count == 1:
                helper_list.append(self.mexc_futures_multiply(symbol, float(value), current_price))
                bids.append(helper_list)
                helper_list = []
                number_count = 0
            if prefix == "data.asks.item.item" and previous_map_event == "start_array":
                number_count += 1
                helper_list.append(float(value))
            if prefix == "data.asks.item.item" and previous_map_event == "number" and number_count == 1:
                helper_list.append(self.mexc_futures_multiply(symbol, float(value), current_price))
                asks.append(helper_list)
                number_count = 0
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  time.time(), "bids" : bids, "asks" : asks}
        return d

    async def mexc_api_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):

        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  time.time(), "bids" : bids, "asks" : asks}
        return d

    async def mexc_ws_perpetual_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
    
        data = json.loads(data)

        price = market_state.get("price_future", self.backup_symbol_mexc, self.default_price_value)

        timestamp = float(data.get("ts"))
        symbol = data.get("symbol")

        data = data.get("data")

        asks = [[ask[0], self.mexc_futures_multiply(symbol, ask[1]), price] for ask in data.get("asks")] if data.get("asks") != [] else []
        bids = [[ask[0], self.mexc_futures_multiply(symbol, ask[1], price)] for ask in data.get("bids")] if data.get("bids") != [] else []

        d = {"timestamp" :  timestamp/ 1000,  "bids" : bids, "asks" : asks}
        return d

    async def mexc_ws_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):

        data = json.loads(data)

        timestamp = float(data.get("t"))

        bidsdata = data.get("d").get("bids") if "bids" in data.get("d") else []
        bids = [[float(bid.get("p")), float(bid.get("v"))] for bid in bidsdata] if bidsdata != [] else bidsdata
        asksdata = data.get("d").get("asks") if "asks" in data.get("d") else []
        asks = [[float(bid.get("p")), float(bid.get("v"))] for bid in asksdata] if asksdata != [] else asksdata
        d = {"timestamp" :  timestamp / 1000, "bids" : bids, "asks" : asks}
        return d

class gateio_on_message(on_message_helper):

    def __init__ (self):
        """
            Options multiplier was fetched via api

            https://www.gate.io/help/futures/perpetual/22147/Calculation-of-Position-Value
        """
        self.backup_symbol_gateio = backup_symbols.get("gateio")

    def gateio_futures_multiply(self, symbol:str, amount:float, price:float, *args, **kwargs):
        symbol = "_".join(symbol.split("_")[:2])
        multiplier = mexc_future_multipliers.get(symbol)
        if callable(multiplier):
            return multiplier(amount, price)
        else:
            return amount * multiplier
    
    def gateio_option_multiply(self, symbol, amount):
        symbol = symbol.split("-")[0]
        multiplier = gateio_option_multipliers.get(symbol)
        return amount * multiplier


    async def gateio_api_option_oi_oioption(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            btc_price_data : dictionary with all prices of bitcoin instruments from every exchange
        """

        symbol = connection_data.get("exchange_symbol")

        backup_price =  market_state.get_data("price_future", self.backup_symbol_gateio, self.default_price_value)

        msids = []
        symbols = []
        strikes = []
        days_left = []
        ois = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "item.name":
                option_data = value.split("-")
                msids.append(f"{value}@option@gateio")
                symbols.append(value)
                strikes.append(float(option_data[2]))
                days_left.append(calculate_option_time_to_expire_gateio(option_data[1]))
            if prefix == "item.position_size":
                ois.append(self.gateio_option_multiply(symbol, float(value)))
        instruments_data = {x : {} for x in msids}
        for i, msid in enumerate(msids):
            instruments_data[msid] = {
                "symbol": symbols[i],
                "strike": strikes[i],
                "days_left": int(days_left[i]),
                "oi": ois[i],
                "price": backup_price
            }
        instruments_data["timestamp"] = time.time()
        return instruments_data
    
    async def gateio_api_perpetual_future_oi(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            https://www.gate.io/docs/developers/apiv4/en/#futures-stats
        """
        price =  market_state.get_data("price_future", self.backup_symbol_gateio, self.default_price_value)

        ddd = {}

        data_dict = json.loads(data)[0]
        data = data_dict.get("data")
        instrument = data_dict.get("instrument")
        
        if "open_interest_usd" in data:
            #price = float(data.get("mark_price"))
            oi = float(data.get("open_interest_usd")) / price
            msid = f"{instrument}@perpetual@gateio"
            ddd[msid] = {"price" : price, "oi" : oi, "timestamp" : time.time()}
            
            market_state.input_data("oi_future", msid, oi)
            
        if "total_size" in data:
            #price = float(data.get("mark_price"))
            oi = float(data.get("total_size"))
            oi = self.gateio_futures_multiply(instrument, oi, price)
            msid = f"{instrument}@future@gateio"
            ddd[msid] = {"price" : price, "oi" : oi, "timestamp" : time.time()}

            market_state.input_data("oi_future", msid, oi)

        return ddd

    async def gateio_api_perpetual_future_tta(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            https://www.gate.io/docs/developers/apiv4/en/#futures-stats
        """
        ddd = {}
        
        data_dict = json.loads(data)
        
        instrument_data = data_dict.get("data")[0]
        symbol = data_dict.get("instrument")

        lsr_taker = float(instrument_data.get("lsr_taker")) # Long/short taker size ratio
        lsr_account = float(instrument_data.get("lsr_account"))   # Long/short account number ratio
        top_lsr_account = float(instrument_data.get("top_lsr_account")) # Top trader long/short account ratio
        top_lsr_size = float(instrument_data.get("top_lsr_size"))   #  	Top trader long/short position ratio
        msid = f"{symbol}@perpetual@gateio"
        ddd[msid]  = {
                      "tta_size_ratio" : top_lsr_size , 
                      "tta_ratio" : top_lsr_account, 
                      "gta_ratio" : lsr_account, 
                      "gta_size_ratio" : lsr_taker
                      }
                
        market_state.input_data("tta_size_ratio", msid, top_lsr_size)
        market_state.input_data("tta_ratio", msid, top_lsr_account)
        market_state.input_data("gta_ratio", msid, lsr_account)
        market_state.input_data("gta_size_ratio", msid, lsr_taker)
        
        return ddd
    
    async def gateio_api_perpetual_funding(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        ddd = {}
        data = json.loads(data)
        instrument_data = data.get("data")[0]
        instrument = data.get("instrument")
        msid = f"{instrument}@perpetual@gateio"
        ddd[msid]  = {"funding" : float(instrument_data.get("r")), "timestamp" : time.time()}
        market_state.input_data("funding", msid, ddd[msid])
        return ddd

    async def gateio_api_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            side : bids, asks
        """
        bids = []
        asks = []
        previous_map_event = ""
        helper_list = []

        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "bids.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "asks.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "asks.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  time.time(),  "bids" : bids, "asks" : asks}

        return d

    async def gateio_api_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        bids = []
        asks = []
        price = market_state.get_data("price_future", self.backup_symbol_gateio, self.default_price_value)

        previous_map_event = ""
        helper_list = []
        symbol = connection_data.get("exchange_symbols")[0]
        for prefix, event, value in ijson.parse(data):
            if prefix == "bids.item.p" and previous_map_event == "map_key":
                helper_list.append(float(value))
            if prefix == "bids.item.s" and previous_map_event == "map_key":
                helper_list.append(self.gateio_futures_multiply(symbol, float(value), price))
                bids.append(helper_list)
                helper_list = []
            if prefix == "asks.item.p" and previous_map_event == "map_key":
                helper_list.append(float(value))
            if prefix == "asks.item.s" and previous_map_event == "map_key":
                helper_list.append(self.gateio_futures_multiply(symbol, float(value), price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  time.time(),  "bids" : bids, "asks" : asks}

        return d

    async def gateio_ws_spot_depth(self, data:str, market_state:dict,  connection_data:str, *args, **kwargs):
        bids = []
        asks = []
        timestamp = None

        for prefix, event, value in ijson.parse(data):
            if prefix == "result.t":
                timestamp = float(value)
                break

        previous_map_event = ""
        helper_list = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.b.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.b.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "result.a.item.item" and previous_map_event == "start_array":
                helper_list.append(float(value))
            if prefix == "result.a.item.item" and previous_map_event == "string":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  timestamp / 1000,  "bids" : bids, "asks" : asks}

        return d

    async def gateio_ws_perpetual_future_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            side : bids, asks
        """
        bids = []
        asks = []
        timestamp = None
        symbol = None

        price = market_state.get("price_future", self.backup_symbol_gateio, self.default_price_value)

        for prefix, event, value in ijson.parse(data):
            if prefix == "result.t":
                timestamp = float(value)
            if prefix == "result.s":
                symbol = value
            if timestamp != None and symbol != None:
                break

        previous_map_event = ""
        helper_list = []
        for prefix, event, value in ijson.parse(data):
            if prefix == "result.b.item.p" and previous_map_event == "map_key":
                helper_list.append(float(value))
            if prefix == "result.b.item.s" and previous_map_event == "map_key":
                helper_list.append(self.gateio_futures_multiply(symbol, float(value), price))
                bids.append(helper_list)
                helper_list = []
            if prefix == "result.a.item.p" and previous_map_event == "map_key":
                helper_list.append(float(value))
            if prefix == "result.a.item.s" and previous_map_event == "map_key":
                helper_list.append(self.gateio_futures_multiply(symbol, float(value), price))
                asks.append(helper_list)
                helper_list = []
            previous_map_event = event

        d = {"timestamp" :  timestamp/1000,  "bids" : bids, "asks" : asks}

        return d

    async def gateio_ws_spot_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            side : bids, asks
        """
        data = json.loads(data)
        data = data.get("result")
        trades = []
        liquidations = []
        timestamp = float(data.get("create_time_ms")) / 1000
        side = data.get("side")
        amount =  float(data.get("amount"))
        price = float(data.get("price"))
        symbol = data.get("currency_pair")
        trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "quantity" : amount})

        msid = f"{symbol}@spot@gateio"
        market_state.input_data("price_spot", msid, price)

        r = {"liquidations" : liquidations, "trades" : trades, "timestamp" : timestamp}
        return r

    async def gateio_ws_perpetual_future_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        """
            https://www.gate.io/docs/developers/futures/ws/en/#trades-notification
        """
        data = json.loads(data)
        inst_type = connection_data.get("instType") or connection_data.get("instTypes").split("_")[0]

        data = data.get("result")
        trades = []
        liquidations = []
        for trade in data:
            timestamp = float(trade.get("create_time_ms")) / 1000
            side = "sell" if trade.get("size") < 0 else "buy"
            amount =  abs(float(trade.get("size")))
            symbol = trade.get("contract")
            price = float(trade.get("price"))
            amount = self.gateio_futures_multiply(symbol, float(value), price)
            if "is_internal" in trade and trade.get("is_internal") is True:
                liquidations.append({"side" : side, "timestamp" : timestamp, "price" : price, "quantity" : amount})
            else:
                trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "quantity" : amount})
            
            sss = trade.get('contract')
            msid = f"{sss}@perpetual@gateio"
            market_state.input_data("price_future", msid, price)
        return {"liquidations" : liquidations, "trades" : trades, "timestamp" : timestamp}

class coinbase_on_message(on_message_helper):

    def __init__ (self):
        pass

    async def coinbase_api_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
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
                bids.append(helper_list)
                helper_list = []
            if prefix == "pricebook.bids.item.price":
                helper_list.append(float(value))
            if prefix == "pricebook.bids.item.size":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
        
        d = {"timestamp" :  time.time(), "bids" : bids, "asks" : asks}
        return d

    async def coinbase_ws_spot_depth(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        bids = []
        asks = []
        helper_list = []
        t = None

        for prefix, event, value in ijson.parse(data):
            if prefix == "events.item.updates.item.event_time":
                t = value
                break
        
        side = ""

        for prefix, event, value in ijson.parse(data):
            if prefix == "events.item.updates.item.price_level"  and side == "bid":
                helper_list.append(float(value))
            if prefix == "events.item.updates.item.new_quantity" and side == "bid":
                helper_list.append(float(value))
                bids.append(helper_list)
                helper_list = []
            if prefix == "events.item.updates.item.price_level" and side == "offer":
                helper_list.append(float(value))
            if prefix == "events.item.updates.item.new_quantity" and side == "offer":
                helper_list.append(float(value))
                asks.append(helper_list)
                helper_list = []
            if prefix == "events.item.updates.item.side":
                side = value
        
        receive_time = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
        receive_time = float(receive_time * 1000)

        d = {"timestamp" :  receive_time,  "bids" : bids, "asks" : asks}
        return d

    async def coinbase_ws_spot_trades(self, data:str, market_state:dict, connection_data:str, *args, **kwargs):
        data = json.loads(data)
        trades = []
        liquidations = []
        data = data.get("events")[0].get("trades")
        msid = f"{connection_data.get('exchange_symbol')}@spot@coinbase"
        for trade in data:
            receive_time = datetime.strptime(trade.get("time"), "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
            receive_time = float(receive_time * 1000)
            side = trade.get("side").lower()
            amount =  float(trade.get("size"))
            price = float(trade.get("price"))
            trades.append({"side" : side, "timestamp" : receive_time, "price" : price, "quantity" : amount})
            market_state.input_data("price_spot", msid, price)

        return {"liquidations" : liquidations, "trades" : trades, "timestamp" : receive_time}

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


