from dataclasses import dataclass, field
import asyncio
import time
from typing import List, Dict, Optional, Tuple
import pandas as pd
import uuid
import rapidjson as json

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

    def update_from_dict(self, data_dict):
        """Updates with new data based on condition."""
        for symbol, symbol_data in data_dict.items():
            if symbol not in self._data:
                self.create_symbol_dict(symbol)
            self._data[symbol].update(symbol_data)
            self._data[symbol]['update_time'] = time.time()
    
    async def remove_dead_instruments(self, check_interval):
        while True:
            current_time = time.time()
            symbols_to_remove = [symbol for symbol, data in self._data.items() if current_time - data.get('update_time', 0) > self.expiration_timeout]
            for symbol in symbols_to_remove:
                del self._data[symbol]
            await asyncio.sleep(self.symbol_remove_timeout) 
    
    def retrive_data_by_objective(self, objectives:list=[], inst_types:list=[], exchanges:list=[]):
        """ Retrives data by objective. If instrument type is passed in a list, these will be ignored"""
        data = {obj : {} for obj in objectives}
        for instrument in self._data:
            isnt_type = instrument.split("@")[1]
            if isnt_type in inst_types:
                for obj in objectives:
                    data[obj][instrument] = self.retrive_data(instrument, obj)
        return data

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
        self.timestamp = 0
        self.price = None
        self.bids : dict = field(default_factory=dict)
        self.asks : dict = field(default_factory=dict)

    async def update_bid(self, price: float, amount: float):
        """ updates bid"""
        if amount > 0:
            self.bids[price] = amount
        elif amount == 0 and price in self.bids:
            del self.bids[price]

    async def update_ask(self, price: float, amount: float):
        """ updates ask """
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

    #@jit(nopython=True)
    async def trim_books(self):
        """ trims books if needed"""
        for level in self.bids.copy().keys():
            if abs(self.compute_percentage_variation(float(level), self.price)) > self.book_ceil_thresh:
                del self.bids[level]
        for level in self.asks.copy().keys():
            if abs(self.compute_percentage_variation(float(level), self.price)) > self.book_ceil_thresh:
                del self.asks[level]

    @staticmethod
    def compute_percentage_variation(new_value, old_value):
        """ Computes percentage variation"""
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
    
    async def add_sell(self, timestamp: float, price: float, quantity: float):
        """ adds a sell trade"""
        if quantity > 0 and self.last_timestamp < timestamp:
            if timestamp not in self.sells:
                self.sells[timestamp] = []
            self.sells[timestamp].append({"price" : price, "quantity" : quantity})
            self.price = price
        self.last_timestamp = timestamp

    async def add_buy(self, timestamp: float, price: float, quantity: float):
        """ adds a buys trade"""
        if quantity > 0 and self.last_timestamp < timestamp:
            if timestamp not in self.buys:
                self.buys[timestamp] = []
            self.buys[timestamp].append({"price" : price, "quantity" : quantity})
            self.price = price
        self.last_timestamp = timestamp


    async def add_short(self, timestamp: float, price: float, quantity: float):
        """ adds a sell trade"""
        if quantity > 0 and self.last_ltimestamp < timestamp:
            if timestamp not in self.shorts:
                self.shorts[timestamp] = []
            self.shorts[timestamp].append({"price" : price, "quantity" : quantity})
        self.last_ltimestamp = timestamp

    async def add_long(self, timestamp: float, price: float, quantity: float):
        """ adds a buys trade"""
        if quantity > 0 and self.last_ltimestamp < timestamp:
            if timestamp not in self.longs:
                self.longs[timestamp] = []
            self.longs[timestamp].append({"price" : price, "quantity" : quantity})
        self.last_ltimestamp = timestamp
    
    async def reset_trades(self):
        """ resets trades data """
        self.buys.clear()
        self.sells.clear()
        self.last_timestamp = 0

    async def reset_liquidations(self):
        """ resets liquidations data """
        self.longs.clear()
        self.shorts.clear()
        self.last_ltimestamp = 0
        
@dataclass
class OpenInterest:
    """ Data holder of processed Open interest values by future/perpetual instrument, ready to be processed or merged"""
    
    data : dict = field(default_factory=dict)
    last_values : dict = field(default_factory=dict)

    async def add_entry(self, timestamp: float, instrument: str, open_interest: float, price : float):
        """
            Args:
                timestamp (float): unix
                instrument (str): str
                open_interest (float): float
                price (float): float
        """
        entry = {"timestamp": timestamp, "open_interest": open_interest, "price" : price}

        if instrument not in self.data:
            self.data[instrument] = []
        self.data[instrument].append(entry)
        self.last_values[instrument] = open_interest
        # await asyncio.sleep(0.3) # for testing
 

    async def get_last_value(self, instrument: str) -> Optional[int]:
        """ gets last values """
        return self.last_values.get(instrument)

    async def get_unique_instruments(self):
        """ getse unique instrumet"""
        return  list(self.data.keys())

    async def reset_data(self):
        """ resets data """
        self.data = dict()

    def __str__(self):
        """ __str__"""
        return '\n'.join(str(entry) for entry in self.data)
    
@dataclass
class OptionInstrumentsData:
    
    data : dict = field(default_factory=dict) # a dictionary of Instrument: List[OpenInterestEntry]

    async def add_data_bulk(self, bulk_data):

        for instrument, data in bulk_data.items():

            if isinstance(data, dict):
                days_left = data.get("days_left")
                oi = data.get("oi")

                if days_left >= 0 and oi > 0:
                    oidata = {
                        "instrument" : data.get("symbol"),
                        "strike" : data.get("strike"),
                        "days_left" : data.get("days_left"),
                        "oi" : data.get("oi"),
                        "price" : data.get("price"),
                        "option_type" : data.get("symbol")[-1],
                    }
                    self.data[instrument] = oidata

                if instrument in self.data and oi <= 0:
                    del self.data[instrument]


    def reset_data(self):
        self.data = {}

    def get_summary(self) -> Dict[str, List]:
        strikes = [instrument.get("strike") for instrument in self.data.values()]
        countdowns = [instrument.get("days_left") for instrument in self.data.values()]
        ois = [instrument.get("oi") for instrument in self.data.values()]
        prices = [instrument.get("price") for instrument in self.data.values()]
        return {"strikes": strikes, "countdowns": countdowns, "ois": ois, "prices" : prices}
    
    def get_summary_by_option_type(self) -> Dict[str, Dict[str, List]]:

        summary = {
            "Call": {
                "strikes": [], "countdowns": [], "ois": [], "prices" : []
                },
            "Put": {
                "strikes": [], "countdowns": [], "ois": [], "prices" : [] 
                }
            }

        for instrument, data in self.data.items():

            option_category = "Call" if data.get("option_type") == 'C' else "Put"

            summary[option_category]["strikes"].append(data.get("strike"))

            summary[option_category]["countdowns"].append(data.get("days_left"))

            summary[option_category]["ois"].append(data.get("oi"))

            summary[option_category]["prices"].append(data.get("price"))

        return summary.get("Call"), summary.get("Put")

    def __str__(self):
        return '\n'.join(f"{key}: {vars(instrument)}" for key, instrument in self.data.items())
    
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
    
def default_map_dictionary() -> Dict[str, Dict]:
    return {
        "books" : {
            "spot" : dict(),
            "future" : dict(),
        },
        "canceled_books" : {
            "spot" : dict(),
            "future" : dict(),
        },
        "reinforced_books" : {
            "spot" : dict(),
            "future" : dict(),
        },
        "trades" : {
            "spot" : dict(),
            "future" : dict(),
            "option" : dict(),
        },
        "oi_deltas" : {
            "future" : dict(),
            "option" : dict(),
        },
        "liquidations" : {
            "future" : dict(),
        }
    }


class MarketState:
    """
    This class holds all market data, sanitized data, and data needed for processing.

    Attributes:
        staging_data:
            * timestamp: Current UNIX timestamp
            * instrument_data: 
                Data of prices, volume, open interest, funding rate, liquidations, and some exchange positions data
                for every instrument type (e.g., spot, future, perpetual, etc.)
            * global_data: 
                Data of prices, volume, open interest, funding rate, and liquidations.
                It is the aggregate of all instrument data by instrument type such as spot, future, etc.
                Price and funding are weighted, everything elese is group-summed
            * maps:
                Order books, trades, and open interest deltas (ticks), canceled books, and reinforced books.
                This is aggregated data over all instrument types originating from different exchanges.
                Also, aggregation must happend over a certain price range
            * ticks: 
                Trades, liquidations, and open interest deltas over a certain period of time.
                This is aggregated data over all instrument types originating from different exchanges. Instead of the snapshot being 
                taken at the end of each period, it encapsulates every market action made over a certain period of time.

        raw_data:
            * dataframes_to_merge:
                A dictionary of dataframes that will be merged together, grouped by instrument type.
            * merged_dataframes:
                These will be used to extract canceled and reinforced books as well as to create maps.
            * ticks_data_to_merge:
                All ticks of trades, open interest deltas, and liquidations grouped by instrument types.
                Ticks contain all market actions over a certain period of time.
                Will be needed to input into ticks.
            
            Each raw_data will contain a timestamp for a corresponding data object in order to ensure the old data wasnt merged.
            If there is old data, the software will notify
    """
    def __init__(self, streams_data):
        self.streams_data = streams_data
        self.staging_data = {
                "timestamp": 0,
                "global": {
                    "price_spot" : 0,
                    "price_perpetual" : 0,
                    "price_future" : 0,
                    "price_derivate" : 0,
                    
                    "buys_spot": 0,
                    "buys_perpetual" : 0,
                    "buys_option" : 0,
                    "sells_spot" : 0,
                    "sells_perpetual" : 0,
                    "sells_option" : 0,
                    "oi_perpetual" : 0,
                    "oi_option" : 0,
                    "oi_future" : 0,
                    "longs": 0,
                    "shorts": 0,
                    "funding_rate": 0,
                },
                "by_instrument": {
                    "price_spot": {},
                    "price_perpetual" : {},
                    "price_future" : {},
                    "oi_perpetual" : {},
                    "oi_option" : {},
                    "oi_future" : {},
                    "funding_rate": {},
                    "ttp_long_ratio": {},
                    "ttp_short_ratio": {},
                    "ttp_ratio": {},
                    "tta_long_ratio": {},
                    "tta_short_ratio": {},
                    "tta_ratio": {},
                    "gta_long_ratio": {},
                    "gta_short_ratio": {},
                    "gta_ratio": {},
                    "tta_size_ratio": {},
                },
                "aggregated_maps": {
                    "books_spot": {},
                    "books_perpetual" : {},
                    "buys_spot": {},
                    "buys_perpetual": {},
                    "buys_option": {},
                    "sells_spot": {},
                    "sells_perpetual": {},
                    "sells_option": {},
                    "longs": {},
                    "shorts": {},
                    "canceled_books_spot": {},
                    "canceled_books_perpetual": {},
                    "reinforced_books_spot": {},
                    "reinforced_books_perpetual": {},
                    "oi_deltas_future" : {},
                },
                "ticks": {
                    "trades_spot": {},
                    "trades_perpetual": {},
                    "trades_option": {},
                    "liquidations": {},
                    "oi_deltas_future": {},
                },
                "oi_option" : {}
            }
        self.raw_data = {
            "dataframes_to_merge": {
                "books" : {"spot" : {}, "perpetual" : {}},
                "trades" : {
                    "spot" :  {"buys" : {}, "sells" : {}, "total" : {}, "delta" : {}}, 
                    "perpetual" : {"buys" : {}, "sells" : {}, "total" : {}, "delta" : {}}, 
                    "option" :  {"buys" : {}, "sells" : {}, "total" : {}, "delta" : {}}
                            },
                "oi_deltas" : {},
                "oi_option" : {},
                "liquidations" : {}
            },
            "ticks_data_to_merge": {
                "trades" : {"spot" : {}, "perpetual" : {}, "option" : {}},
                "oit_deltas" : {},
                "liquidations" : {},  
            },
            "merged_dataframes": {
                "books" : {"spot" : pd.DataFrame(), "perpetual" : pd.DataFrame()},
                "trades" : {
                    "spot" :  {"buys" : pd.DataFrame(), "sells" : pd.DataFrame(), "total" : pd.DataFrame(), "delta" : pd.DataFrame()}, 
                    "perpetual" : {"buys" : pd.DataFrame(), "sells" : pd.DataFrame(), "total" : pd.DataFrame(), "delta" : pd.DataFrame()}, 
                    "option" :  {"buys" : pd.DataFrame(), "sells" : pd.DataFrame(), "total" : pd.DataFrame(), "delta" : pd.DataFrame()}
                            },
                "oi_deltas" : pd.DataFrame(),
                "oi_option" : pd.DataFrame(),
                "liquidations" : pd.DataFrame(),
                "canceled_books" : {"spot" : pd.DataFrame(), "perpetual" : pd.DataFrame()},
                "reinforced_books" : {"spot" : pd.DataFrame(), "perpetual" : pd.DataFrame()},
            },
        }
        
    def input_data(self, metric : str, symbol : str, quantity : float):
        """ inputs data by metric """
        self.staging_data["by_instrument"][metric].update({symbol : quantity})
    
    def remove_unnecessary_keys(self):
        pass
        
        
        # Remove Staging Data based on streams data!

        # Insert into Staging Data
        # Global Data
        # 




    def generate_unique_id(self) -> str:
        """Generates a unique identifier using UUID4."""
        return str(uuid.uuid4())
    
    def retrive_all_data(self, drop):
        """ Retrives data is json format to insert into database"""
        return {
            "id" : self.generate_unique_id(),
            "timestamp" : time.time(),
            "global_data" : self.global_data,
            "instrument_data" : self.instrument_data,
            "maps" : self.maps,
            "tick_data" : self.tick_data
        }
    

