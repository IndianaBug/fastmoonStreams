from dataclasses import dataclass, field
import asyncio
import time
from numba import jit

@dataclass
class MarketState:
    """ 
      Holds market data for instruments
      
      Every instrument should be named like this symbol@instType@exchange
    """
    _data : dict = field(default_factory=dict)
    
    expiration_timeout = 600
    symbol_remove_timeout = 600

    def retrive_data(self, symbol, objective, default_return=None):
        """Gets value for key in symbol's data."""
        return self._data.get(symbol, {}).get(objective, default_return)

    def retrive_symbol_data(self, symbol, default_return=None):
        """Gets value for key in symbol's data."""
        return self._data.get(symbol, default_return)

    def create_symbol_dict(self, symbol):
        """Sets value for key in symbol's data (creates dict if needed)."""
        self._data[symbol] = {}

    @jit(nopython=True)
    def update_from_dict(self, data_dict):
        """Updates with new data based on condition."""
        for symbol, symbol_data in data_dict.items():
            if symbol not in self._data:
                self.create_symbol_dict(symbol)
            self._data[symbol].update(symbol_data)
            self._data[symbol]['update_time'] = time.time()
    
    @jit(nopython=True)
    async def remove_dead_instruments(self, check_interval):
        while True:
            current_time = time.time()
            symbols_to_remove = [symbol for symbol, data in self._data.items() if current_time - data.get('update_time', 0) > self.expiration_timeout]
            for symbol in symbols_to_remove:
                del self._data[symbol]
            await asyncio.sleep(self.symbol_remove_timeout) 
    
    @jit(nopython=True)
    def retrive_data_by_objective(self, objectives:list=[], inst_types:list=[], exchanges:list=[]):
        """ Retrives data by objective. If instrument type is passed in a list, these will be ignored"""
        data = {obj : {} for obj in objectives}
        for instrument in self._data:
            isnt_type = instrument.split("@")[1]
            if isnt_type in inst_types:
                for obj in objectives:
                    data[obj][instrument] = self.retrive_data(instrument, obj)
        return data

    @jit(nopython=True)
    def retrive_data_by_exchange(self, exchanges:list=[], objectives:list=[]):
        """ Retrives data by objective. If instrument type is passed in a list, these will be ignored"""
        data = {exchange : {obj : {} for obj in objectives} for exchange in exchanges}
        for instrument in self._data:
            exchange = instrument.split("@")[-1]
            if exchange in exchanges:
                for obj in objectives:
                    data[exchange][obj][instrument] = self._data.get(instrument).get(obj)
        return data

@dataclass
class OrderBook:

    def __init__(self, book_ceil_thresh):
      self.book_ceil_thresh = book_ceil_thresh
      self.timestamp = dict()
      self.price = None
      self.bids = dict()
      self.asks = dict()

    async def update_bid(self, price: float, amount: float):
        if amount > 0:
            self.bids[price] = amount
        elif amount == 0 and price in self.bids:
            del self.bids[price]

    async def update_ask(self, price: float, amount: float):
        if amount > 0:
            self.asks[price] = amount
        elif amount == 0 and price in self.asks:
            del self.asks[price]

    async def update_data(self, data):
        """ updates all asks and bids at once """

        self.timestamp = data.get("timestamp")
        
        for bid_data in data.get("bids", []):
            await self.update_bid(bid_data[0], bid_data[1])

        for ask_data in data.get("asks", []):
            await self.update_ask(ask_data[0], ask_data[1])
        
        self.price = (max(self.bids.keys()) + min(self.asks.keys())) / 2

    async def trim_books(self):
      for level in self.bids.copy().keys():
          if abs(self.compute_percentage_variation(float(level), self.price)) > self.book_ceil_thresh:
              del self.bids[level]
      for level in self.asks.copy().keys():
          if abs(self.compute_percentage_variation(float(level), self.price)) > self.book_ceil_thresh:
              del self.asks[level]

    @staticmethod
    def compute_percentage_variation(new_value, old_value):
        try:
            percentage_difference = abs((new_value - old_value) / old_value) * 100
            return percentage_difference
        except:
            return 9999999999
        

@dataclass
class MarketTradesLiquidations:

    """
        inputs data from this dictionary:
            {"trades" : [{"side" : side, "price" : price, "quantity" : quantity, "timestamp" : timestamp}, ...], "liquidations" : [...], "receive_time" : receive_time}
    """

    buys : dict = field(default_factory=dict)
    sells : dict = field(default_factory=dict)
    longs : dict = field(default_factory=dict)
    shorts : dict = field(default_factory=dict)
    last_timestamp = 0
    last_ltimestamp = 0
    price = 0

    @jit(nopython=True)
    async def add_trades(self, data):
        """ adds trades in bulk"""
        for trade in data.get("trades"):
            side = trade.get("side")
            price = trade.get("price")
            quantity = trade.get("quantity")
            timestamp = trade.get("timestamp")
            if side == "buy":
                await self.add_buy(timestamp, price, quantity)
            elif side == "sell":
                await self.add_sell(timestamp, price, quantity)

    @jit(nopython=True)
    async def add_liquidations(self, data):
        """ adds liquidations in bulk"""
        for trade in data.get("liquidations"):
            side = trade.get("side")
            price = trade.get("price")
            quantity = trade.get("quantity")
            timestamp = trade.get("timestamp")
            if side == "buy":
                await self.add_short(timestamp, price, quantity)
            elif side == "sell":
                await self.add_long(timestamp, price, quantity)
    
    @jit(nopython=True)
    async def add_sell(self, timestamp: float, price: float, quantity: float):
        """ adds a sell trade"""
        if quantity > 0 and self.last_timestamp < timestamp:
            if timestamp not in self.sells:
                self.sells[timestamp] = []
            self.sells[timestamp].append({"price" : price, "quantity" : quantity})
            self.price = price
        self.last_timestamp = timestamp

    @jit(nopython=True)
    async def add_buy(self, timestamp: float, price: float, quantity: float):
        """ adds a buys trade"""
        if quantity > 0 and self.last_timestamp < timestamp:
            if timestamp not in self.buys:
                self.buys[timestamp] = []
            self.buys[timestamp].append({"price" : price, "quantity" : quantity})
            self.price = price
        self.last_timestamp = timestamp


    @jit(nopython=True)
    async def add_short(self, timestamp: float, price: float, quantity: float):
        """ adds a sell trade"""
        if quantity > 0 and self.last_ltimestamp < timestamp:
            if timestamp not in self.shorts:
                self.shorts[timestamp] = []
            self.shorts[timestamp].append({"price" : price, "quantity" : quantity})
        self.last_ltimestamp = timestamp

    @jit(nopython=True)
    async def add_long(self, timestamp: float, price: float, quantity: float):
        """ adds a buys trade"""
        if quantity > 0 and self.last_ltimestamp < timestamp:
            if timestamp not in self.longs:
                self.longs[timestamp] = []
            self.longs[timestamp].append({"price" : price, "quantity" : quantity})
        self.last_ltimestamp = timestamp
    
    @jit(nopython=True)
    async def reset_trades(self):
        """ resets trades data """
        self.buys.clear()
        self.sells.clear()
        self.last_timestamp = 0

    @jit(nopython=True)
    async def reset_liquidations(self):
        """ resets liquidations data """
        self.longs.clear()
        self.shorts.clear()
        self.last_ltimestamp = 0