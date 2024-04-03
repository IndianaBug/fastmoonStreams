from typing import Dict, Optional, Callable, Tuple, List
import datetime
from dateutil import parser
import time
import json

class on_message_helper():

  @classmethod
  def convert_lists_to_floats(cls, data):
      """
      Convert a list of lists to a list of lists of floats.

      Args:
          data (list of lists): The input data consisting of lists.

      Returns:
          list of lists of floats: The converted data.
      """
      return list(map(lambda x: [float(x[0]), float(x[1])], data))

  @classmethod
  def process_timestamp(cls, data, timestamp_keys:list, divide_value=1):
      """
      Extracts and formats timestamp from data dictionary.

      Args:
          data (dict): The input dictionary.
          timestamp_key (str): The key specifying the timestamp in the data dictionary.
          divide_value (float or None, optional): Value to divide the timestamp by. Defaults to None.

      Returns:
          str: The formatted timestamp.
      """
      timestamp = data
      for key in timestamp_keys:
          timestamp = timestamp.get(key)
      return datetime.datetime.fromtimestamp(int(timestamp) / divide_value).strftime('%Y-%m-%d %H:%M:%S')

  @classmethod
  def process_timestamp_no_timestamp(cls):
      """
      """
      return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
  


class binance_on_message(on_message_helper):

    def __init__ (self, unit_conversation:Optional[Dict[str, Callable]] = None):
        """
            unit_conversation is a dictionary that converts amounts from native units into btc units

            https://www.binance.com/en/support/faq/binance-coin-margined-futures-contract-specifications-a4470430e3164c13932be8967961aede

            Contract multiplier represents the value of a contract. For example, the contract multiplier for BTC COIN-margined contracts is 100 USD. 
            Meanwhile, altcoin contracts usually have a multiplier of 10 USD, although this may vary for specific symbols.

            Example : 
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : calculation,
                "WONDERFULSHIT_PERP" : lambda amount, price : your calculation,
            }

            Note: symbol must be of the same format as from binance API
        """
        if unit_conversation != None:
            self.unit_conversation = {
                "BTCUSD_PERP" : lambda amount, price : amount * 100 / price,
            }
        else:
            self.unit_conversation = unit_conversation
    
    def binance_api_spot_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
            Must return a list of float and timestamp in string format
            [
                [float(price), float(amount)],
                .....
            ]
            returns: [[price, amount]...], timestamp
        """
        timestamp = self.process_timestamp_no_timestamp()
        books = self.convert_lists_to_floats(data.get(side))
        return books, timestamp

    def binance_api_perpetual_future_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
            Must return a list of float and timestamp in string format
            [
                [float(price), float(amount)],
                .....
            ]
            returns: [[price, amount]...], timestamp
        """
        timestamp = self.process_timestamp(data, ["T"], 1000)
        books = self.convert_lists_to_floats(data.get(side))
        return books, timestamp

    def binance_ws_spot_LinearPerpetual_LinearFuture_future_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
            Must return a list of float and timestamp in string format
            [
                [float(price), float(amount)],
                .....
            ]
            returns: [[price, amount]...], timestamp
        """
        symbol = data.get("s")
        side = "a" if side=="asks" else "b"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        books = self.convert_lists_to_floats(data.get(side))
        return books, timestamp

    def binance_ws_InversePerpetual_InverseFuture_future_depth(self, data:dict, side:str) -> Tuple[list, str]:
        """
            side : bids, asks
            Must return a list of float and timestamp in string format
            [
                [float(price), float(amount)],
                .....
            ]
            returns: [[price, amount]...], timestamp
        """
        side = "a" if side=="asks" else "b"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        books = self.convert_lists_to_floats(data.get(side))
        return books, timestamp

    def binance_ws_spot_perpetual_future_trades(self, data : dict) -> List[str, float, float, str]:
        """
          [side, price, amount, timestamp]
        """
        side = "a" if side=="asks" else "b"
        timestamp = self.process_timestamp(data, ["E"], 1000)
        books = self.convert_lists_to_floats(data.get(side))
        return books, timestamp


# timestamp_keys = ["E", "T"]

# ! git clone https://github.com/badcoder-cloud/fastmoonStreams

# ! git clone https://github.com/badcoder-cloud/moonStreamProcess

# import os

# current_directory = os.chdir("/content/fastmoonStreams")


# filepath = "/content/fastmoonStreams/producers/mockdb/binance/binance_ws_perpetual_depth_btcusdperp.json" 

# file = json.load(open(filepath))[0]

# print(file)