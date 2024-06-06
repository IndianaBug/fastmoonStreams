from dataclasses import dataclass, field
import asyncio
import time
from numba import jit
from typing import List, Dict, Optional

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
        
@dataclass
class OpenInterestEntry:
    timestamp: float
    instrument: str
    open_interest: float
    price : float
    
@dataclass
class OpenInterest:
    data: List[OpenInterestEntry] = field(default_factory=list)
    last_values: Dict[str, int] = field(default_factory=dict)

    def add_entry(self, timestamp: float, instrument: str, open_interest: float, price : float):
        entry = OpenInterestEntry(timestamp, instrument, open_interest, price)
        self.data.append(entry)
        self.last_values[instrument] = open_interest

    def get_entries_by_instrument(self, instrument: str) -> List[OpenInterestEntry]:
        return [entry for entry in self.data if entry.instrument == instrument]

    def get_entries_by_timestamp(self, timestamp: float) -> List[OpenInterestEntry]:
        return [entry for entry in self.data if entry.timestamp == timestamp]

    def get_last_value(self, instrument: str) -> Optional[int]:
        return self.last_values.get(instrument)

    def calculate_change(self, instrument: str, new_open_interest: int) -> Optional[int]:
        last_value = self.get_last_value(instrument)
        if last_value is not None:
            return new_open_interest - last_value
        return None

    def reset_data(self):
        self.data = []

    def __str__(self):
        return '\n'.join(str(entry) for entry in self.data)
    
@dataclass
class OptionInstrument:
    symbol: str
    strike: float
    days_left: int
    oi: float
    option_type: str  # 'C' for Call, 'P' for Put

@dataclass
class OptionInstrumentsData:
    instruments: Dict[str, OptionInstrument] = field(default_factory=dict)

    def add_instrument(self, key: str, instrument: OptionInstrument):
        self.instruments[key] = instrument

    def add_instruments_bulk(self, bulk_data: Dict[str, Dict]):
        for key, data in bulk_data.items():
            days_left = data["days_left"]
            if days_left >= 0:
                instrument = OptionInstrument(
                    symbol=data["symbol"],
                    strike=data["strike"],
                    days_left=days_left,
                    oi=data["oi"],
                    option_type=data["symbol"][-1]  # Extracting option type from the symbol
                )
            self.add_instrument(key, instrument)

    def get_instrument(self, key: str) -> OptionInstrument:
        return self.instruments.get(key)

    def remove_instrument(self, key: str):
        if key in self.instruments:
            del self.instruments[key]

    def reset_data(self):
        self.instruments = {}

    def get_summary(self) -> Dict[str, List]:
        strikes = [instrument.strike for instrument in self.instruments.values()]
        countdowns = [instrument.days_left for instrument in self.instruments.values()]
        oi = [instrument.oi for instrument in self.instruments.values()]
        return {"strikes": strikes, "countdowns": countdowns, "oi": oi}
    
    def get_summary_by_option_type(self) -> Dict[str, Dict[str, List]]:
        summary = {"Call": {"strikes": [], "countdowns": [], "oi": []},
                   "Put": {"strikes": [], "countdowns": [], "oi": []}}

        for instrument in self.instruments.values():
            option_category = "Call" if instrument.option_type == 'C' else "Put"
            summary[option_category]["strikes"].append(instrument.strike)
            summary[option_category]["countdowns"].append(instrument.days_left)
            summary[option_category]["oi"].append(instrument.oi)

        return summary

    def __str__(self):
        return '\n'.join(f"{key}: {vars(instrument)}" for key, instrument in self.instruments.items())
    
@dataclass
class PositionData:

    symbol: str
    
    gta_long_ratio: Optional[float] = None
    gta_short_ratio: Optional[float] = None
    gta_ratio: Optional[float] = None
    gta_size_ratio: Optional[float] = None

    tta_long_ratio: Optional[float] = None
    tta_short_ratio: Optional[float] = None
    tta_ratio: Optional[float] = None
    tta_size_ratio: Optional[float] = None

    ttp_long_ratio: Optional[float] = None
    ttp_short_ratio: Optional[float] = None
    ttp_ratio: Optional[float] = None
    ttp_size_ratio: Optional[float] = None
    
    funding: Optional[float] = None

    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: '{key}' is not a valid attribute of {self.__class__.__name__}")

@dataclass
class InstrumentsData:
    
    # update_data = {"tta_ratio": 1.6, "funding": 0.02}
    # instruments_data.update_position("ETHUSDT", update_data)
    
    instruments: Dict[str, PositionData] = field(default_factory=dict)
    
    def add_position(self, symbol: str, **kwargs):
        self.instruments[symbol] = PositionData(symbol=symbol, **kwargs)

    def update_position(self, symbol: str, data: dict):
        if symbol not in self.instruments:
            self.instruments[symbol] = PositionData(symbol=symbol)
        self.instruments[symbol].update_from_dict(data)

    def get_position(self, symbol: str) -> Optional[PositionData]:
        return self.instruments.get(symbol)

    def get_all_positions(self) -> Dict[str, PositionData]:
        return self.instruments

    def reset_data(self):
        self.instruments = {}

    def __str__(self):
        return '\n'.join(f"{symbol}: {vars(data)}" for symbol, data in self.instruments.items())