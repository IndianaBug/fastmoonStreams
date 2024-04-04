from typing import Dict, Optional, Callable, Tuple, List, Union
from datetime import datetime
# from dateutil import parser
import time
import json
import numpy as np
from on_message_helpers import *

timestamp_keys = ["E", "T"]

class on_message_helper():

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
            derivate_multiplier is a dictionary with lambdas that converts contracts amount into native ocin amounts
            keys must be of the same format as from binance api call

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }

            https://www.binance.com/en/support/faq/binance-coin-margined-futures-contract-specifications-a4470430e3164c13932be8967961aede

            Contract multiplier represents the value of a contract. For example, the contract multiplier for BTC COIN-margined contracts is 100 USD. 
            Meanwhile, altcoin contracts usually have a multiplier of 10 USD, although this may vary for specific symbols.

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }
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
    
    def binance_api_spot_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp_no_timestamp()
        books = self.convert_books(data.get(side))
        return books, timestamp

    def binance_api_linear_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        timestamp = self.process_timestamp(data, ["E"], 1000)
        books = self.convert_books(data.get(side))
        return books, timestamp

    def binance_api_inverse_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
            type_ : perpetual, future
        """
        symbol = data.get("pair")
        current_price = (float(data.get("bids")[0][0]) + float(data.get("asks")[0][0])) / 2
        timestamp = self.process_timestamp(data, ["T"], 1000)
        books = self.books_multiplier(data.get(side), self.derivate_multiplier.get(symbol), current_price)
        return books, timestamp

    def binance_ws_spot_linear_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
        """
        side = "a" if side=="asks" else "b"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        books = self.convert_books(data.get(side))
        return books, timestamp

    def binance_ws_inverse_depth(self, data:dict, side:str,) -> Tuple[list, str]:
        """
            side : bids, asks
            type_ : perpetual, future
        """
        side = "a" if side=="asks" else "b"
        symbol = data.get("ps")
        current_price = (float(data.get("b")[0][0]) + float(data.get("a")[0][0])) / 2
        timestamp = self.process_timestamp(data, ["E"], 1000)
        books = self.books_multiplier(data.get(side), self.derivate_multiplier.get(symbol), current_price)
        return books, timestamp
    
    def binance_ws_spot_linear_option_trades(self, data:dict) -> List[Union[str, float, float, str]]:
        """
            trades aggregate channel
            returns [side, price, amount, timestamp]
        """
        quantity = float(data.get("q"))
        price = float(data.get("p"))
        side = "buy" if data.get("m") is True else "sell"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return [[side, price, quantity, timestamp]]

    def binance_ws_inverse_trades(self, data:dict) -> List[Union[str, float, float, str]]:
        """
            returns [side, price, amount, timestamp]
        """
        price = float(data.get("p"))
        quantity = self.derivate_multiplier.get(data.get("s").split("_")[0])(float(data.get("q")), price)
        side = "buy" if data.get("m") is True else "sell"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return [[side, price, quantity, timestamp]]

    def binance_ws_linear_option_liquidations(self, data:dict) -> List[Union[str, float, float, str]]:
        """
            trades aggregate channel
            returns [side, price, amount, timestamp]
        """
        quantity = float(data.get("o").get("q"))
        price = float(data.get("o").get("p"))
        side = data.get("o").get("S").lower()
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return [[side, price, quantity, timestamp]]

    def binance_ws_inverse_liquidations(self, data:dict) -> List[Union[str, float, float, str]]:
        """
            returns [side, price, amount, timestamp]
        """
        price = float(data.get("o").get("p"))
        quantity = self.derivate_multiplier.get(data.get("o").get("ps"))(float(data.get("o").get("q")), price)
        side = data.get("o").get("S").lower()
        timestamp = self.process_timestamp(data, ["E"], 1000)
        return [[side, price, quantity, timestamp]]

    def binance_api_oifutureperp(self, data:dict, price:float=1000000) -> Dict[str, list]:
        """
            price : current price of bitcoin
            returns [side, price, amount, timestamp]
        """
        l = {}
        for di in data.values():
            if "code" in di:
                continue
            if "symbol" in di:
                symbol = di.get("symbol").split("_")[0]
                amount = self.derivate_multiplier.get(symbol)(float(di.get("openInterest")), price)
                timestamp = self.process_timestamp(di, ["time"], 1000)
                l[di.get("symbol")] = [amount, price, timestamp]
        return l

    def binance_api_oioption(self, data:dict, side:str, price:float=None) -> Tuple[np.array, np.array, np.array, float, str]:
        """
            side : P, C
            returns: strikes, countdowns, ois, price, timestamp
        """
        data = [d for l in data.values() for d in l if isinstance(d, dict)]
        strikes = np.array([float(op.get("symbol").split("-")[2]) for op in data if op.get("symbol").split("-")[-1] == side])
        countdowns = np.array([binance_option_timedelta(op.get("symbol").split("-")[1]) for op in data if op.get("symbol").split("-")[-1] == side])
        ois = np.array([float(op.get("sumOpenInterest")) for op in data if op.get("symbol").split("-")[-1] == side])
        timestamp = self.process_timestamp_no_timestamp()
        return strikes, countdowns, ois, price, timestamp
    
    def binance_api_posfutureperp(self, data:dict, price:float=1000000) -> Dict[str, list]:
        """
            price : current price of bitcoin
            returns [side, price, amount, timestamp]
        """
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

            https://www.binance.com/en/support/faq/binance-coin-margined-futures-contract-specifications-a4470430e3164c13932be8967961aede

            Contract multiplier represents the value of a contract. For example, the contract multiplier for BTC COIN-margined contracts is 100 USD. 
            Meanwhile, altcoin contracts usually have a multiplier of 10 USD, although this may vary for specific symbols.

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }
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





filepath = "C:/coding/SatoshiVault/producers/mockdb/binance/binance_api_perpetual_gta_btc.json" 

file = json.load(open(filepath))[0]

onn = binance_on_message()
print(onn.binance_api_posfutureperp(file, 70000))

# ! git clone https://github.com/badcoder-cloud/fastmoonStreams

# ! git clone https://github.com/badcoder-cloud/moonStreamProcess

# import os

# current_directory = os.chdir("/content/fastmoonStreams")


# filepath = "/content/fastmoonStreams/producers/mockdb/binance/binance_ws_perpetual_depth_btcusdperp.json" 

# file = json.load(open(filepath))[0]

# print(file)

