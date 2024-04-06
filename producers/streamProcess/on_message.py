from typing import Dict, Optional, Callable, Tuple, List, Union
from datetime import datetime
# from dateutil import parser
import time
import json
import numpy as np
from utilis_streamProcess import *

timestamp_keys = ["E", "T", "ts", "timestamp", "time", "t"]
func_args = ["data", "symbol", "btc_prices"]
from typing import Literal, Dict, Any
from typing import Dict, List, Tuple, Union, Literal
from typing import List, Dict, Union, Optional, Literal

# redo binance bybit okx options

class on_message_helper():

    """
        depth : {"bids" : [[price, amount]], "asks" : [[price, amount]], "timestamp" : '%Y-%m-%d %H:%M:%S'}
        trades_liquidations : {"liquidations" : {"side" : str, "amount" : float, "price" : float, "timestamp" : '%Y-%m-%d %H:%M:%S'}, 
                                "asks" : {"side" : str, "amount" : float, "price" : float, "timestamp" : '%Y-%m-%d %H:%M:%S'}, 
                                "timestamp" : '%Y-%m-%d %H:%M:%S'}
        oi_funding_optionoi_tta_ttp_gta_pos : {symbol : {"some indicator" : value}, ....}

    """
    depth: Dict[str, Union[List[List[float, float]], str]]
    trades_liquidations: Dict[str, Union[List[List[str, float, float, str]], str]]
    future_perp_oi_funding_pos_dict_oioption: Dict[str, Any]

    possible_function_args = ["data", "market_state"]

    @classmethod
    def convert_books(cls, data):
        return list(map(lambda x: [float(x[0]), float(x[1])], data))

    @classmethod
    def books_multiplier(cls, data, multiplier:callable, current_price):
        return list(map(lambda x: [float(x[0]), multiplier(float(x[1]), current_price)], data))

    @classmethod
    def process_timestamp(cls, data, timestamp_keys:list, divide_value=1):
        timestamp = data
        for key in timestamp_keys:
            timestamp = timestamp.get(key)
        return datetime.fromtimestamp(int(timestamp) / divide_value).strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def process_timestamp_no_timestamp(cls):
        return datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
  
class binance_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            https://www.binance.com/en/support/faq/binance-coin-margined-futures-contract-specifications-a4470430e3164c13932be8967961aede

            https://www.binance.com/en/support/faq/binance-options-contract-specifications-cdee5d43b70d4d2386980d41786a8533

            Be cautios with option, as units vary for XRP and DOGE
        """
        if derivate_multiplier == None:
            self.derivate_multiplier = {
                "BTCUSD" : lambda amount, price : amount * 100 / price,  # the same for perp and any expiry future
                "BTCUSDT" : lambda amount, price : amount,
                "BTCDOMUSDT" : lambda amount, price : amount,
                "BTCUSDC" : lambda amount, price : amount,
            }
        else:
            self.derivate_multiplier = derivate_multiplier
    
    def binance_api_spot_depth(self, data:dict, *args, **kwargs) -> 'on_message_helper.depth':
        d = {}
        for side in ["bids", "asks"]:
            books = self.convert_books(data.get(side))
            d[side] = books
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    def binance_api_linearperpetual_linearfuture_depth(self, data:dict, *args, **kwargs) -> 'on_message_helper.depth':
        d = {}
        for side in ["bids", "asks"]:
            books = self.convert_books(data.get(side))
            d[side] = books
        d["timestamp"] = self.process_timestamp(data, ["E"], 1000)
        return d

    def binance_api_inverseperpetual_inversefuture_depth(self, data:dict,  *args, **kwargs) -> 'on_message_helper.depth':
        symbol = data.get("pair")
        current_price = (float(data.get("bids")[0][0]) + float(data.get("asks")[0][0])) / 2
        d = {}
        for side in ["bids", "asks"]:
            books = self.books_multiplier(data.get(side), self.derivate_multiplier.get(symbol), current_price)
            d[side] = books
        d["timestamp"] = self.process_timestamp(data, ["T"], 1000)
        return d

    def binance_ws_spot_linearperpetual_linearfuture_depth(self, data:dict,  *args, **kwargs) -> 'on_message_helper.depth':
        d = {}
        d["timestamp"] = self.process_timestamp(data, ["E"], 1000)
        for side in ["a", "b"]:
            books = self.convert_books(data.get(side))
            d["bids" if side=="b" else "asks"] = books
        return d

    def binance_ws_inverseperpetual_inversefuture_depth(self, data:dict, *args, **kwargs) -> 'on_message_helper.depth':
        d = {}
        current_price = (float(data.get("b")[0][0]) + float(data.get("a")[0][0])) / 2
        symbol = data.get("ps")
        d["timestamp"] = self.process_timestamp(data, ["E"], 1000)
        for side in ["a", "b"]:
            d["bids" if side=="b" else "asks"] = self.books_multiplier(data.get(side), self.derivate_multiplier.get(symbol), current_price)
        return d
    
    def binance_ws_spot_linearperpetual_linearfuture_option_trades(self, data:dict, *args, **kwargs) -> 'on_message_helper.trades_liquidations':
        quantity = float(data.get("q"))
        price = float(data.get("p"))
        side = "buy" if data.get("m") is True else "sell"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return {"trades" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "liquidations" : []}

    def binance_ws_inverseperpetual_inversefuture_trades(self, data:dict, *args, **kwargs) -> 'on_message_helper.trades_liquidations':
        price = float(data.get("p"))
        quantity = self.derivate_multiplier.get(data.get("s").split("_")[0])(float(data.get("q")), price)
        side = "buy" if data.get("m") is True else "sell"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return {"trades" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "liquidations" : []}

    def binance_ws_linearperpetual_linearfuture_option_liquidations(self, data:dict, *args, **kwargs) -> 'on_message_helper.trades_liquidations':
        quantity = float(data.get("o").get("q"))
        price = float(data.get("o").get("p"))
        side = data.get("o").get("S").lower()
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return {"liquidations" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "trades" : []}

    def binance_ws_inverseperpetual_inversefuture_liquidations(self, data:dict, *args, **kwargs) -> 'on_message_helper.trades_liquidations':
        price = float(data.get("o").get("p"))
        quantity = self.derivate_multiplier.get(data.get("o").get("ps"))(float(data.get("o").get("q")), price)
        side = data.get("o").get("S").lower()
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return {"liquidations" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}], "trades" : []}

    def binance_api_oifutureperp(self, data:dict, market_state:dict, *args, **kwargs) -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        l = {}
        for di in data.values():
            if "code" in di:
                continue
            if "symbol" in di:
                symbol = di.get("symbol").split("_")[0]
                ss = di.get("symbol")
                instType = "future" if di.get("symbol").split("_")[1].isdigit() else "perpetual"
                price = market_state.get(f"{symbol}@{instType}@binance").get("price")
                amount = self.derivate_multiplier.get(symbol)(float(di.get("openInterest")), price)
                l[f"{ss}@{instType}@binance"] = {"oi" : amount}
        l["timestamp"] = self.process_timestamp_no_timestamp()
        return l

    def binance_api_oioption_oi_option(self, data:dict, market_state:dict, *args, **kwargs) -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':
        """
            https://www.binance.com/en/support/faq/binance-options-contract-specifications-cdee5d43b70d4d2386980d41786a8533
        """
        data = [d for l in data.values() for d in l if isinstance(d, dict)]
        ddd = {}
        for instData in data:
            symbol_list = instData.get("symbol").split("-")
            symbol = symbol_list[0]
            oi = float(instData.get("sumOpenInterest"))
            strike = float(symbol_list[2])
            days_left = binance_option_timedelta(symbol_list[1])
            side = symbol_list[-1]
            index_price = market_state.get(f"{symbol}USDT@spot@binance")
            ddd[f"{instData.get('name')}@option@binance"] = {"symbol" : instData.get("name"),
                                                      "side" :  side, "index_price" : index_price, 
                                                      "strike" : strike, "underlying_price" : index_price, "oi" : oi, "days_left" : days_left}
        return ddd
        
    
    def binance_api_posfutureperp(self, data:dict, *args, **kwargs) -> 'on_message_helper.oi_funding_optionoi_tta_ttp_gta_pos':

        d = {"timestamp" : self.process_timestamp_no_timestamp()}
        tta = [d for key, l in data.items() for d in l if isinstance(d, dict) if "tta" in key]
        ttp = [d for key, l in data.items() for d in l if isinstance(d, dict) if "ttp" in key]
        gta = [d for key, l in data.items() for d in l if isinstance(d, dict) if "gta" in key]
        for pst in ["tta", "ttp", "gta"]:
            d[pst] = {inst.get("symbol") if "symbol" in inst else inst.get("pair")  : {
                "longs":float(inst.get("longAccount")) if "longAccount" in inst else inst.get("longPosition"),
                "shorts":float(inst.get("shortAccount")) if "shortAccount" in inst else inst.get("longPosition"),
                "ratio":float(inst.get("longShortRatio")) if "longShortRatio" in inst else inst.get("longShortRatio"),
                } for inst in eval(pst)}
        return d
    
    def binance_api_fundfutureperp(self, data:dict, price:float=1000000) -> Dict[str, float]:
        """
            price : current price of bitcoin
            returns [side, price, amount, timestamp]
        """
        d = {"timestamp" : self.process_timestamp_no_timestamp()}
        data = {x[0].get("symbol"):float(x[0].get("fundingRate")) for x in data.values() if isinstance(x[0], dict)}
        d.update(data)
        return d

class bybit_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            derivate_multiplier is a dictionary with lambdas that converts contracts amount into native ocin amounts
            keys must be of the same format as from binance api call

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }

            https://www.bybit.com/en/announcement-info/transact-parameters

            some are 1BTC some are 1USD, depends on the instrument

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }
        """
        if derivate_multiplier == None:
            self.derivate_multiplier = {
                "BTCUSD" : lambda amount, price : amount / price,  # the same for perp and any expiry future
                "BTCUSDT" : lambda amount, price : amount,
                "BTCPERP" : lambda amount, price : amount,
                "BTCUSDM24" : lambda amount, price : amount / price,
                "BTCUSDU24" : lambda amount, price : amount / price,
                "BTC" : lambda amount, price : amount,   # expiry futures

            }
        else:
            self.derivate_multiplier = derivate_multiplier

    def bybit_api_fundperp(self, data:dict) -> list:
        """
            [[side, price, size, timestamp]]
        """
        d = {}
        for instrument in data:
            response = data.get(instrument)
            if isinstance(response, dict): 
              if response.get("result").get("list") != []:
                  d[instrument] = float(response.get("result").get("list")[0].get("fundingRate"))
              else:
                continue
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d


    def bybit_api_oifutureperp(self, data:dict, price) -> list:
        """
            [[side, price, size, timestamp]]
        """
        d = {}
        for instrument in data:
            response = data.get(instrument)
            if isinstance(response, dict): 
              if response.get("result").get("list") != []:
                  symbol = response.get("result").get("list")[0].get("symbol")
                  d[symbol] = self.derivate_multiplier.get(symbol)(float(response.get("result").get("list")[0].get("openInterest")), price)
              else:
                continue
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

      
    def bybit_api_posfutureperp(self, data:dict) -> list:
        """
            [[side, price, size, timestamp]]
        """
        d = {}
        for instrument in data:
            response = data.get(instrument)
            if isinstance(response, dict): 
              if response.get("result").get("list") != []:
                  symbol = response.get("result").get("list")[0].get("symbol")
                  d[symbol] = {
                      "buyRatio" : float(response.get("result").get("list")[0].get("buyRatio")),
                      "sellRatio" : float(response.get("result").get("list")[0].get("sellRatio"))
                  }
              else:
                continue
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d


    def bybit_api_spot_linear_perpetual_future_option_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        side = "a" if side == "asks" else "b"
        timestamp = self.process_timestamp(data, ["result", "ts"], 1000)
        books = self.convert_books(data.get("result").get(side))
        return books, timestamp

    def bybit_api_inverse_perpetual_future_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        side = "a" if side == "asks" else "b"
        symbol = data.get("result").get("s")
        current_price = (float(data.get("result").get("b")[0][0]) + float(data.get("result").get("a")[0][0])) / 2
        timestamp = self.process_timestamp(data, ["result", "ts"], 1000)
        books = self.books_multiplier(data.get("result").get(side), self.derivate_multiplier.get(symbol), current_price)
        return books, timestamp

    def bybit_ws_spot_linear_perpetual_future_option_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        side = "a" if side == "asks" else "b"
        timestamp = self.process_timestamp(data, ["ts"], 1000)
        books = self.convert_books(data.get("data").get(side))
        return books, timestamp

    def bybit_ws_inverse_perpetual_future_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        side = "a" if side == "asks" else "b"
        symbol = data.get("data").get("s")
        current_price = (float(data.get("data").get("b")[0][0]) + float(data.get("data").get("a")[0][0])) / 2
        timestamp = self.process_timestamp(data, ["ts"], 1000)
        books = self.books_multiplier(data.get("data").get(side), self.derivate_multiplier.get(symbol), current_price)
        return books, timestamp


    def bybit_ws_linear_spot_perpetual_future_option_trades(self, data:dict) -> list:
        """
            [[side, price, size, timestamp]]
        """
        l = []
        for trade in data.get("data"):
            timestamp = self.process_timestamp(trade, ["T"], 1000)
            side = trade.get("S").lower()
            price = float(trade.get("p"))
            size = float(trade.get("v"))
            l.append([side, price, size, timestamp])
        return l

    def bybit_ws_inverse_perpetual_future_trades(self, data:dict) -> list:
        """
            [[side, price, size, timestamp]]
        """
        l = []
        for trade in data.get("data"):
            symbol = trade.get("s")
            timestamp = self.process_timestamp(trade, ["T"], 1000)
            side = trade.get("S").lower()
            price = float(trade.get("p"))
            size = self.derivate_multiplier.get(symbol)(float(trade.get("v")), price)
            l.append([side, price, size, timestamp]) 
        return l


    def bybit_ws_linear_spot_perpetual_future_option_liquidations(self, data:dict) -> list:
        """
            [[side, price, size, timestamp]]
        """
        l = []
        trade = data.get("data")
        timestamp = self.process_timestamp(data, ["ts"], 1000)
        side = trade.get("side").lower()
        price = float(trade.get("price"))
        size = float(trade.get("size"))
        l.append([side, price, size, timestamp])
        return l

    def bybit_ws_inverse_perpetual_future_liquidations(self, data:dict) -> list:
        """
            [[side, price, size, timestamp]]
        """
        l = []
        trade = data.get("data")
        timestamp = self.process_timestamp(data, ["ts"], 1000)
        side = trade.get("side").lower()
        price = float(trade.get("price"))
        symbol = trade.get("symbol")
        size = self.derivate_multiplier.get(symbol)(float(trade.get("size")), price)
        l.append([side, price, size, timestamp])
        return l


    def bybit_api_option_oi(self, data : json, side : str, price=None) -> Tuple[np.array, np.array, np.array, float, str]:
        """
            side : P, C
            returns: strikes, countdowns, ois, price, timestamp
        """
        timestamp = self.process_timestamp_no_timestamp()
        strikes = np.array([float(d.get("symbol").split("-")[-2]) for d in data.get("result").get("list") if d.get("symbol").split("-")[-1] == side])
        ois = np.array([float(d.get("openInterest")) for d in data.get("result").get("list") if d.get("symbol").split("-")[-1] == side])
        countdowns = np.array([calculate_option_time_to_expire_bybit(d.get("symbol").split("-")[1]) for d in data.get("result").get("list") if d.get("symbol").split("-")[-1] == side])
        return strikes, countdowns, ois, price, timestamp

class okx_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            derivate_multiplier is a dictionary with lambdas that converts contracts amount into native ocin amounts
            keys must be of the same format as from binance api call

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }

            https://www.okx.com/trade-market/info/futures

            some are 1BTC some are 1USD, depends on the instrument

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }
        """
        if derivate_multiplier == None:
            self.derivate_multiplier = {
                "BTC-USDT" : lambda amount, price : amount * 0.01,  # any swap or future
                "BTC-USDC" : lambda amount, price : amount * 0.0001,  # any swap or future
                "BTC-USD" : lambda amount, price : amount / price * 100,

            }
        else:
            self.derivate_multiplier = derivate_multiplier

    def okx_api_fundperp(self, data:dict, *args, **kwargs) -> List[Union[str, float, float, str]]:
        """
        """
        d = {}
        for marginType in data:
            if isinstance(data.get(marginType), dict):
              for d_per_instrument in data.get(marginType).get("data"):
                symbol = d_per_instrument.get("instId")
                d[symbol] = float(d_per_instrument.get("fundingRate"))
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    def okx_api_gta(self, data:dict, *args, **kwargs) -> List[Union[str, float, float, str]]:
        """
        """
        d = {"BTC" : float(data.get("data")[0][1])}
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    def okx_api_oifutureperp(self, data:dict, *args, **kwargs) -> List[Union[str, float, float, str]]:
        """
        """
        d = {}
        for marginType in data:
            if isinstance(data.get(marginType), dict):
                for d_per_instrument in data.get(marginType).get("data"):
                    if isinstance(d_per_instrument, dict):
                        symbol = d_per_instrument.get("instId")
                        d[symbol] = float(d_per_instrument.get("oiCcy"))
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    def okx_api_option_oi(self, data : dict, side : str, price:float,  *args, **kwargs) -> Tuple[np.array, np.array, np.array, float, str]:
        """
            side : P, C
            returns : strikes, countdowns, ois, price, timestamp
        """
        strikes = np.array([float(x["instId"].split('-')[-2]) for x in data["data"] if x["instId"].split('-')[-1] == side])
        countdowns = np.array([calculate_option_time_to_expire_okx(x["instId"].split('-')[2]) for x in data["data"] if x["instId"].split('-')[-1] == side])
        ois = np.array([float(x["oiCcy"]) for x in data["data"] if x["instId"].split('-')[-1] == side])
        timestamp = self.process_timestamp_no_timestamp()
        return strikes, countdowns, ois, price, timestamp

    def okx_api_ws_spot_option_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data.get("data")[0], ["ts"], 1000)
        books = self.convert_books(data.get("data")[0].get(side))
        return books, timestamp

    def okx_api_ws_linear_inverse_perpetual_future_depth(self, data:dict, side:str, symbol:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
            symbol : the symbol with the exact format fetched from okx api info BUT the instType 
        """
        timestamp = self.process_timestamp(data.get("data")[0], ["ts"], 1000)
        books = self.books_multiplier(data.get("data")[0].get(side), self.derivate_multiplier.get("-".join(symbol.split("-")[:2])), 1000)
        return books, timestamp

    def okx_ws_option_trades(self, data:dict, *args, **kwargs) -> List[Union[str, float, float, str]]:
        """
        """
        l = []
        for trade in data.get("data"):
            side = trade.get('side')
            price =float(trade.get('idxPx'))
            timestamp = self.process_timestamp(trade, ["ts"], 1000)
            amount = float(trade.get('fillVol'))
            l.append([side, price, amount, timestamp])
        return l
    
    def okx_ws_spot_trades(self, data, *args, **kwargs)-> List[Union[str, float, float, str]]:
        l = []
        for trade in data.get("data"):
            side = trade.get('side')
            price =float(trade.get('px'))
            timestamp = self.process_timestamp(trade, ["ts"], 1000)
            amount = float(trade.get('sz'))
            l.append([side, price, amount, timestamp])      
        return l    
    
    def okx_ws_linear_inverse_perpetual_future_trades(self, data, *args, **kwargs)-> List[Union[str, float, float, str]]:
        l = []
        for trade in data.get("data"):
            multiplier_symbol = "-".join(trade.get('instId').split("-")[0:2])
            side = trade.get('side')
            price =float(trade.get('px'))
            timestamp = self.process_timestamp(trade, ["ts"], 1000)
            amount = self.derivate_multiplier.get(multiplier_symbol)(float(trade.get('sz')), price)
            l.append([side, price, amount, timestamp])      
        return l      

    def okx_ws_future_perpetual_option_liquidations(self, data, *args, **kwargs)-> List[Union[str, float, float, str]]:
        l = []
        for liquidation in data.get("data"):
            instType = liquidation.get("instType")
            instId = liquidation.get("instId")
            multiplier_symbol = liquidation.get('instFamily')
            if "BTC" in instId:
                for l2 in liquidation.get("details"):
                    side = l2.get('side')
                    price =float(l2.get('bkPx'))
                    timestamp = self.process_timestamp(l2, ["ts"], 1000)
                    if instType != "OPTION":
                        amount = self.derivate_multiplier.get(multiplier_symbol)(float(l2.get("sz")), price)
                    if instType == "OPTION":
                        amount = float(l2.get("sz"))
                    l.append([side, price, amount, timestamp])     
        return l    

class deribit_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier:Optional[Dict[str, Callable]] = None):
        """
            derivate_multiplier is a dictionary with lambdas that converts contracts amount into native ocin amounts
            keys must be of the same format as from binance api call

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }

            https://www.deribit.com/kb/deribit-linear-perpetual

            https://static.deribit.com/files/USDCContractSpecsandmargins.pdf

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }
        """
        if derivate_multiplier == None:
            self.derivate_multiplier = {
                 "BTC" : lambda amount, price=1, objective="",*args, **kwargs: amount  / price / 10 if objective == "oifuture" else amount  / price * 10,    # bullshit deribit api for oi
                "BTC_USDC" : lambda amount, *args, **kwargs : amount * 0.001,  # any swap or future
                "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.001,

            }
        else:
            self.derivate_multiplier = derivate_multiplier

    def deribit_api_option_oi(self, data:dict, *args, **kwargs)-> dict:
        d = {}
        for side in ["C", "P"]:
            strikes = np.array([float(x["instrument_name"].split('-')[-2]) for x in data["result"] if x["instrument_name"].split('-')[-1] == side])
            countdowns = np.array([calculate_option_time_to_expire_deribit(x["instrument_name"].split('-')[1]) for x in data["result"] if x["instrument_name"].split('-')[-1] == side])
            ois = np.array([float(x["open_interest"]) for x in data["result"] if x["instrument_name"].split('-')[-1] == side])
            underlying_prices = np.array([float(x["underlying_price"]) for x in data["result"] if x["instrument_name"].split('-')[-1] == side])
            instruments = np.array([x["instrument_name"] for x in data["result"] if x["instrument_name"].split('-')[-1] == side])
            d[side] = [{"symbol" : ss, "strike" : s, "countdown" : c, "oi" : o, "underlying_price" : u} for ss, s, c, o, u in zip(instruments, strikes, countdowns, ois, underlying_prices)]
        timestamp = self.process_timestamp_no_timestamp()
        d["timestamp"] = timestamp
        d["price"] = data.get("result")[0].get("estimated_delivery_price")
        d["index_prices"] = {ins["underlying_index"] : ins["underlying_price"] for ins in data.get("result")}
        return d

    def deribit_api_perpetual_future_oi_funding(self, data:dict, *args, **kwargs)-> dict:
        d = {"oi" : {}, "funding" : {}}
        for inst_data in data.get("result"):
            price = inst_data.get("mid_price")
            symbol = inst_data.get("instrument_name")
            symbol_multiplier = symbol.split("-")[0]
            oi = self.derivate_multiplier.get(symbol_multiplier)(float(inst_data.get("open_interest")), price, "oifuture")
            d["oi"][symbol] = oi
            if "funding_8h" in inst_data:
                funding = float(inst_data.get("funding_8h"))
                d["funding"][symbol] = funding
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    def deribit_ws_future_perpetual_linear_inverse_option_trades_tradesagg_liquidations(self, data:dict, *args, **kwargs)-> List[List[Union[str, float, float ,str]]]:
        """
            Actually returns 2 lists. One is about trades and another about liquidations
        """
        trades_list = []
        liquidations_list = []
        for trade in data.get("params").get("data"):
            symbol = trade.get("instrument_name").split("-")[0]
            side = trade.get("direction")
            price = float(trade.get("price"))
            amount = self.derivate_multiplier.get(symbol)(float(trade.get("amount")), price)
            timestamp = self.process_timestamp(trade, ["timestamp"], 1000)
            trades_list.append([side, amount, price, timestamp])

            # https://docs.deribit.com/#trades-kind-currency-interval -- contains liquidations

            if "liquidation" in trade:
                liquidations_list.append([side, amount, price, timestamp])
        return trades_list, liquidations_list

    def deribit_ws_future_perpetual_linear_inverse_get_price(self, data:dict, *args, **kwargs)-> List[List[Union[str, float, float ,str]]]:
        l = []
        prices = {}
        for trade in data.get("params").get("data"):
            symbol = trade.get("instrument_name").split("-")[0]
            side = trade.get("direction")
            price = float(trade.get("price"))
            amount = self.derivate_multiplier.get(symbol)(float(trade.get("amount")), price)
            timestamp = self.process_timestamp(trade, ["timestamp"], 1000)
            l.append([side, amount, price, timestamp])
            if "liquidation" not in trade:
                prices[trade.get("instrument_name")] = price
        return prices

    def deribit_api_perpetual_future_depth(self, data:dict, side:str, *args, **kwargs)-> Tuple[list, str]:
        """
            side : bids, asks
        """
        price = data.get("result").get("last_price")
        msymbol = data.get("result").get("instrument_name").split("-")[0]
        timestamp = self.process_timestamp(data.get("result"), ["timestamp"], 1000)
        books = self.books_multiplier(data.get("result").get(side), self.derivate_multiplier.get(msymbol), price)
        return books, timestamp

    def deribit_ws_perpetual_future_depth(self, data:dict, side:str, *args, **kwargs)-> Tuple[list, str]:
        """
            side : bids, asks
        """
        data = data.get("params")
        price = (data.get("data").get("asks")[0][0] + data.get("data").get("bids")[0][0]) / 2
        msymbol = data.get("data").get("instrument_name").split("-")[0]
        timestamp = self.process_timestamp(data.get("data"), ["timestamp"], 1000)
        books = self.books_multiplier(data.get("data").get(side), self.derivate_multiplier.get(msymbol), price)
        return books, timestamp

class bitget_on_message(on_message_helper):

    def __init__ (self):
        """
            Contract multipliers not needed (I couldnt find the documentation for htem)
        """
        pass

    def bitget_api_spot_linear_inverse_perpetual_future_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data.get("data"), ["ts"], 1000)
        books = self.convert_books(data.get("data").get(side))
        return books, timestamp

    def bitget_ws_spot_linear_inverse_perpetual_future_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data.get("data")[0], ["ts"], 1000)
        books = self.convert_books(data.get("data")[0].get(side))
        return books, timestamp

    def bitget_ws_inverse_perpetual_future_spot_trades(self, data:dict, *args, **kwargs) -> list:
        """
            [[side, price, size, timestamp]]
        """
        l = []
        for trade in data.get("data"):
            timestamp = self.process_timestamp(trade, ["ts"], 1000)
            side = trade.get("side").lower()
            price = float(trade.get("price"))
            size = float(trade.get("size"))
            l.append([side, price, size, timestamp]) 
        return l

    def bitget_api_oi_perpetual_oifutureperp(self, data:dict, *args, **kwargs) -> list:
        """
            [[side, price, size, timestamp]]
        """
        d = {}
        for instrument_data in data:
            if isinstance(data.get(instrument_data), dict):
                d[data.get(instrument_data).get("data").get("openInterestList")[0].get("symbol")] = float(data.get(instrument_data).get("data").get("openInterestList")[0].get("size"))
        timestamp = self.process_timestamp_no_timestamp()
        d["timestamp"] = timestamp
        return d

    def bitget_api_funding_perpetual_fundperp(self, data:dict, *args, **kwargs) -> list:
        """
            [[side, price, size, timestamp]]
        """
        d = {}
        for instrument_data in data:
            if isinstance(data.get(instrument_data), dict) and data.get(instrument_data).get("data") != []:
                d[data.get(instrument_data).get("data")[0].get("symbol")] = float(data.get(instrument_data).get("data")[0].get("fundingRate"))
        timestamp = self.process_timestamp_no_timestamp()
        d["timestamp"] = timestamp
        return d

class bingx_on_message(on_message_helper):

    def __init__ (self):
        """
            Contract multipliers not needed (I couldnt find the documentation for htem)
        """
        pass

    def bingx_api_perpetual_linear_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        side = "bidsCoin" if side == "bids" else "asksCoin"
        timestamp = self.process_timestamp(data.get("data"), ["T"], 1000)
        books = self.convert_books(data.get("data").get(side))
        return books, timestamp

    def bingx_ws_spot_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp_no_timestamp()
        books = self.convert_books(data.get("data").get(side))
        return books, timestamp

    def bingx_api_perpetual_oi(self, data:dict, price:str, *args, **kwargs) -> dict:
        timestamp = self.process_timestamp(data.get("data"), ["time"], 1000)
        openInterest = float(data.get("data").get("openInterest"))
        s = str(data.get("data").get("symbol"))
        return {"timestamp" : timestamp, s : openInterest / price}

    def bingx_api_perpetual_funding(self, data:dict, *args, **kwargs) -> dict:
        timestamp = self.process_timestamp_no_timestamp()
        funding = float(data.get("data").get("lastFundingRate"))
        s = str(data.get("data").get("symbol"))
        return {"timestamp" : timestamp, s : funding}

    def bingx_ws_trades_perpetual(self, data:dict, *args, **kwargs) -> list:
        """
            [[side, price, size, timestamp]]
        """
        l = []
        for trade in data.get("data"):
            timestamp = self.process_timestamp(trade, ["T"], 1000)
            side = "buy" if trade.get("m") is True else "sell"
            price = float(trade.get("p"))
            size = float(trade.get("q"))
            l.append([side, price, size, timestamp]) 
        return l

    def bingx_ws_trades_spot(self, data:dict, *args, **kwargs) -> list:
        """
            [[side, price, size, timestamp]]
        """
        l = []
        trade = data.get("data")
        timestamp = self.process_timestamp(trade, ["T"], 1000)
        side = "buy" if trade.get("m") is True else "sell"
        price = float(trade.get("p"))
        size = float(trade.get("q"))
        l.append([side, price, size, timestamp]) 
        return l

class htx_on_message(on_message_helper):

    def __init__ (self):
        """
            Contract multipliers not needed (I couldnt find the documentation for htem)
        """
        pass

    def htx_api_perpetual_oi(self, data:dict, *args, **kwargs) -> dict:
        d = {}
        for marginType in data:
            if isinstance(data.get(marginType), dict): 
                data_per_marginType = data.get(marginType).get("data")
                for data_instrument in data_per_marginType:
                    symbol = data_instrument.get("contract_code")
                    oi = float(data_instrument.get("amount"))
                    d[symbol] = oi
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d


    def htx_api_perpetual_pos_posfutureperp(self, data:dict, *args, **kwargs) -> dict:
        d = {}
        for instrument in data:
            if isinstance(data.get(instrument), dict):
                pos_data = data.get(instrument).get("data").get("list")[0]
                long_ratio = float(pos_data.get("buy_ratio"))
                short_ratio = float(pos_data.get("sell_ratio"))
                d[instrument] = {"long_ratio" : long_ratio, "short_ratio" : short_ratio}
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

    def htx_api_perpetual_funding_fundperp(self, data:dict, *args, **kwargs) -> dict:
        d = {}
        for marginCoin in data:
            if isinstance(data.get(marginCoin), dict):
                instData = data.get(marginCoin).get("data")[0]
                funding = float(instData.get("funding_rate"))
                contract_code = instData.get("contract_code")
                d[contract_code] = funding
        d["timestamp"] = self.process_timestamp_no_timestamp()
        return d

class kucoin_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier=None):
        """
            https://www.kucoin.com/pt/futures/contract/detail/XBTUSDTM
        """
        if derivate_multiplier == None:
            self.derivate_multiplier = {
                "XBTUSDTM" : lambda amount, *args, **kwargs : amount * 0.001,  
            }
        else:
            self.derivate_multiplier = derivate_multiplier

    def kucoin_ws_spot_trades(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        timestamp = self.process_timestamp(data.get("data"), ["time"], 10**9)
        price = float(data.get("data").get("price"))
        side = data.get("data").get("side")
        amount = float(data.get("data").get("size"))
        return [[side, amount, price, timestamp]]

    def kucoin_ws_perpetual_trades(self, data:dict, price, *args, **kwargs) -> Tuple[list, str]:
        timestamp = self.process_timestamp(data.get("data"), ["ts"], 10**9)
        price = float(data.get("data").get("price"))
        side = data.get("data").get("side")
        symbol = data.get("data").get("symbol")
        amount = self.derivate_multiplier.get(symbol)(float(data.get("data").get("size")), price)
        return [[side, amount, price, timestamp]]
    
    def kucoin_api_perpetual_oi_funding(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        data = data.get("data")
        symbol = data.get("symbol")
        multiplier = float(data.get("multiplier"))
        timestamp = self.process_timestamp_no_timestamp()
        oi = float(data.get("openInterest")) * multiplier
        funding = float(data.get("fundingFeeRate"))
        return {"symbol" : symbol, "oi" : oi, "timestamp" : timestamp, "funding" : funding}

    def kucoin_api_spot_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data.get("data"), ["time"], 1)
        books = self.convert_books(data.get("data").get(side))
        return books, timestamp

    def kucoin_api_perpetual_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data.get("data"), ["ts"], 10**9)
        symbol = data.get("data").get("symbol")
        price = (float(data.get("data").get("bids")[0][0]) + float(data.get("data").get("asks")[0][0])) / 2
        books = self.books_multiplier(data.get("data").get(side), self.derivate_multiplier.get(symbol), price)
        return books, timestamp

    def kucoin_ws_spot_depth(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data.get("data"), ["time"], 1000)
        books = [[x[0], x[1]] for x in self.convert_books(data.get("data").get("changes").get(side))]
        return books, timestamp

    def kucoin_ws_perpetual_depth(self, data:dict, side:str, price, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data, ["data", "timestamp"], 10**3)
        side = "buy" if side == "bids" else "sell"
        change = data.get("data").get("change").split(",")
        symbol = data.get("topic").split(":")[-1]
        books = [float(change[0]), self.derivate_multiplier.get(symbol)(float(change[-1]), price)] if side == change[1] else [[]]
        return books, timestamp

class mexc_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier=None):
        """
            https://www.mexc.com/support/articles/17827791509072
        """
        if derivate_multiplier == None:
            self.derivate_multiplier = {
                "BTC-USDT" : lambda amount, *args, **kwargs : amount * 0.0001,  
                "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.0001, # some unstandart symbols in API, maybe not needed just in case
            }
        else:
            self.derivate_multiplier = derivate_multiplier

    def mexc_ws_spot_trades(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        trades = data.get("d").get("deals")
        ttt = []
        lll = []
        for trade in trades:
            price = float(trade.get("p"))
            side = "buy" if int(trade.get("S")) == 1 else "sell"
            amount = float(trade.get("v"))
            timestamp = self.process_timestamp(trade, ["t"], 10**3)
            ttt.append([side, amount, price, timestamp])
        return {"trades" : trades, "liquidations" : lll}

    def mexc_ws_perpetual_trades(self, data:dict, price, *args, **kwargs) -> Tuple[list, str]:
        symbol = data.get("symbol") 
        trade = data.get("data")
        trades = []
        liquidations = []
        price = float(trade.get("p"))
        side = "buy" if int(trade.get("T")) == 1 else "sell"
        amount = self.derivate_multiplier.get(symbol)(float(trade.get("v")), price)
        timestamp = self.process_timestamp(trade, ["t"], 10**3)
        trades.append([side, amount, price, timestamp])
        return {"trades" : trades, "liquidations" : []}

    def mexc_api_perpetual_oi_funding_oifunding(self, data:dict, side:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        symbol = data.get("data").get("symbol")
        oi = self.derivate_multiplier.get(symbol)(float(data.get("data").get("holdVol")))
        timestamp = self.process_timestamp_no_timestamp()
        funding = float(data.get("data").get("fundingRate"))
        return [{"symbol" : symbol, "oi" : oi, "funding" : funding, "timestamp" : timestamp}]

    def mexc_api_perpetual_depth(self, data:dict, side:str, symbol:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        current_price = (data.get("data").get("bids")[0][0] + data.get("data").get("asks")[0][0]) / 2
        timestamp = self.process_timestamp(data.get("data"), ["timestamp"], 1000)
        books = self.books_multiplier(data.get("data").get(side), self.derivate_multiplier.get(symbol), current_price)
        return books, timestamp

    def mexc_api_spot_depth(self, data:dict, side:str, symbol:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data.get("data"), ["timestamp"], 1000)
        books = self.convert_books(data.get("data").get(side))
        return books, timestamp

class gateio_on_message(on_message_helper):

    def __init__ (self, derivate_multiplier=None):
        """
            Options multiplier was fetched via api

            https://www.gate.io/help/futures/perpetual/22147/Calculation-of-Position-Value
        """
        if derivate_multiplier == None:
            self.derivate_multiplier = {
                "option" : {
                    "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.01, 
                },
                "perpetual_future" : {
                    "BTC_USDT" : lambda amount, *args, **kwargs : amount * 0.0001, 
                    "BTC_USD" : lambda amount, *args, **kwargs : amount * 0.0001, 
                },
            }
        else:
            self.derivate_multiplier = derivate_multiplier

    def gateio_api_option_oi_oioption(self, data:dict, btc_price_data:dict, *args, **kwargs) -> Tuple[list, str]:
        """
            btc_price_data : dictionary with all prices of bitcoin instruments from every exchange
        """
        data = data.get("list")
        ddd = {}
        for instData in data:
            name_data = instData.get("name").split("-")
            symbol = name_data[0]
            oi = self.derivate_multiplier.get("option").get(symbol)(instData.get("position_size"))
            strike = float(name_data[2])
            days_left = calculate_option_time_to_expire_gateio(name_data[1])
            side = name_data[-1]
            index_price = btc_price_data.get(f"{symbol}@gateio")
            ddd[f"{instData.get('name')}@gateio"] = {"symbol" : instData.get("name"), "side" : side, "index_price" : index_price, "strike" : strike, "underlying_price" : index_price, "oi" : oi, "days_left" : days_left}
        return ddd
    
    def gateio_api_perpetual_future_oi_tta(self, data:dict, *args, **kwargs):
        """
            https://www.gate.io/docs/developers/apiv4/en/#futures-stats
        """
        ddd = {}
        for instrument in data:
            if isinstance(data.get(instrument)[0], dict):
                instrument_data = data.get(instrument)[0]
                if len(instrument.split("_")) == 2:
                    price = instrument_data.get("mark_price")
                    oi = instrument_data.get("open_interest_usd") / price
                    lsr_taker = instrument_data.get("lsr_taker") # Long/short taker size ratio
                    lsr_account = instrument_data.get("lsr_account")   # Long/short account number ratio
                    top_lsr_account = instrument_data.get("top_lsr_account") # Top trader long/short account ratio
                    top_lsr_size = instrument_data.get("top_lsr_size")   #  	Top trader long/short position ratio
                    symbol = instrument
                    ddd[f"{symbol}@gateio"]  = {"ttp" : top_lsr_size , "tta" : top_lsr_account, "gta_NUMBER" : lsr_account, "gta_SIZE_RATIO" : lsr_taker, "oi" : oi, "price" : price}
                if len(instrument.split("_")) == 3:
                    symbol = instrument_data.get("contract")
                    price = float(instrument_data.get("mark_price"))
                    oi = self.derivate_multiplier.get("_".join(symbol.split("_")[:-1]))(float(instrument_data.get("total_size")))
                    ddd[f"{symbol}@gateio"] = {"price" : price, "oi" : oi}
        return ddd
    
    def gateio_api_perpetual_funding(self, data:dict, *args, **kwargs):
        ddd = {}
        for instrument in data:
            if isinstance(data.get(instrument)[0], dict):
                instrument_data = data.get(instrument)[0]
                ddd[f"{instrument}@gateio"]  = {"funding" : float(instrument_data.get("r"))}
        return ddd

    def gateio_api_spot_depth(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        d = {}
        d["timestamp"] = self.process_timestamp(data, ["update"], 1000)
        for side in ["bids", "asks"]:
            d[side] = self.convert_books(data.get(side))
        return d

    def gateio_api_perpetual_future_depth(self, data:dict, symbol:str, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        d = {}
        d["timestamp"] = self.process_timestamp(data, ["update"])
        symbol = symbol.split("@")[0]
        current_price = (float(data.get("bids")[0].get("p")) + float(data.get("asks")[0].get("p"))) / 2
        for side in ["bids", "asks"]:
            d[side] = self.books_multiplier([[x.get("p"), x.get("s")] for x in data.get(side)], self.derivate_multiplier.get("perpetual_future").get(symbol), current_price)
        return d

    def gateio_ws_spot_depth(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        data = data.get("result")
        d = {}
        d["timestamp"] = self.process_timestamp(data, ["t"], 1000)
        for side in ["a", "b"]:
            sss = "asks" if side == "a" else "bids" 
            d[sss] = self.convert_books(data.get(side))
        return d

    def gateio_ws_perpetual_future_depth(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        d = {}
        data = data.get("result")
        d["timestamp"] = self.process_timestamp(data, ["t"], 1000)
        symbol = data.get("s")
        current_price = (float(data.get("a")[0].get("p")) + float(data.get("b")[0].get("p"))) / 2
        for side in ["a", "b"]:
            sss = "asks" if side == "a" else "bids" 
            d[sss] = self.books_multiplier([[x.get("p"), x.get("s")] for x in data.get(side)], self.derivate_multiplier.get("perpetual_future").get(symbol), current_price)
        return d

    def gateio_ws_spot_trades(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        data = data.get("result")
        trades = []
        liquidations = []
        timestamp = self.process_timestamp(data, ["create_time"])
        side = data.get("side")
        amount =  float(data.get("amount"))
        price = float(data.get("price"))
        trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "amount" : amount})
        return {"liquidations" : liquidations, "trades" : trades}

    def gateio_ws_perpetual_future_trades(self, data:dict, *args, **kwargs) -> Tuple[list, str]:
        """
            https://www.gate.io/docs/developers/futures/ws/en/#trades-notification
        """
        data = data.get("result")
        trades = []
        liquidations = []
        for trade in data:
            timestamp = self.process_timestamp(trade, ["create_time"])
            side = "sell" if trade.get("size") < 0 else "buy"
            amount =  abs(float(trade.get("size")))
            price = float(trade.get("price"))
            if "is_internal" in trade and trade.get("is_internal") is True:
                liquidations.append({"side" : side, "timestamp" : timestamp, "price" : price, "amount" : amount})
            else:
                trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "amount" : amount})
        return {"liquidations" : liquidations, "trades" : trades}

class coinbase_on_message(on_message_helper):

    def __init__ (self):
        pass

    def coinbase_api_spot_depth(self, data:dict, *args, **kwargs):
        data = data.get("pricebook")
        d = {}
        d["timestamp"] = datetime.strptime(data.get("time"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        for side in ["bids", "asks"]:
            d[side] = self.convert_books([[x.get("price"), x.get("size")] for x in data.get(side)])
        return d

    def coinbase_ws_spot_depth(self, data:dict, *args, **kwargs):
        timestamp = datetime.strptime(data.get("timestamp").split(".")[0], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        data = data.get("events")[0].get("updates")
        bids = []
        asks = []
        for book in data:
            if book.get("side") == "bid":
                bids.append([float(book.get("price_level")), float(book.get("new_quantity"))])
            if book.get("side") == "offer":
                bids.append([float(book.get("price_level")), float(book.get("new_quantity"))])
        return {"bids" : bids, "asks" : asks, "timestamp" : timestamp}

    def coinbase_ws_spot_trades(self, data:dict, *args, **kwargs):
        trades = []
        liquidations = []
        data = data.get("events")[0].get("trades")
        for trade in data:
            timestamp = datetime.strptime(trade.get("time"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
            side = trade.get("side").lower()
            amount =  float(trade.get("size"))
            price = float(trade.get("price"))
            trades.append({"side" : side, "timestamp" : timestamp, "price" : price, "amount" : amount})
        return {"liquidations" : liquidations, "trades" : trades}



filepath = "C:/coding/SatoshiVault/producers/mockdb/coinbase/coinbase_ws_spot_depth_btcusd.json" 
# filepath = "C:/coding/SatoshiVault/producers/mockdb/deribit/deribit_api_future_oifunding_btc.json" 


file = json.load(open(filepath))[0]

onn = coinbase_on_message()
print(onn.coinbase_ws_spot_depth(file, "BTC_USDT@gateio"))

# ! git clone https://github.com/badcoder-cloud/fastmoonStreams

# ! git clone https://github.com/badcoder-cloud/moonStreamProcess

# import os

# current_directory = os.chdir("/content/fastmoonStreams")


# filepath = "/content/fastmoonStreams/producers/mockdb/binance/binance_ws_perpetual_depth_btcusdperp.json" 

# file = json.load(open(filepath))[0]

# print(file)

