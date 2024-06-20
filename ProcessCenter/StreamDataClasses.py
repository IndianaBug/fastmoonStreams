from dataclasses import dataclass, field
import asyncio
import time
from typing import List, Dict, Optional, Tuple
import pandas as pd
import uuid
import rapidjson as json
from datetime import datetime


class OrderBook:

    def __init__(self, book_ceil_thresh):
        self.book_ceil_thresh = book_ceil_thresh
        self.timestamp = 0
        self.price = None
        self.bids = {}
        self.asks = {}

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
            return 9999999999999999999999999999999999
        
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

    async def add_entry(self, symbol, data_dict):
        """
            Args:
                timestamp (float): unix
                instrument (str): str 
                oi (float): float
                price (float): float
        """
        if symbol not in self.data:
            self.data[symbol] = []
        self.data[symbol].append(data_dict)

    def get_uniquetimestamps(self):
        """ getse unique instrumet"""
        unique_timestamps = set(dic.get("timestamp") for l in self.data.values() for dic in l)
        return list(unique_timestamps)

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
        return {"strikes": strikes, "days_left": countdowns, "ois": ois, "prices" : prices}
    
    def get_summary_by_option_type(self) -> Dict[str, Dict[str, List]]:

        summary = {
            "Call": {
                "strikes": [], "days_left": [], "ois": [], "prices" : []
                },
            "Put": {
                "strikes": [], "days_left": [], "ois": [], "prices" : [] 
                }
            }

        for instrument, data in self.data.items():

            option_category = "Call" if data.get("option_type") == 'C' else "Put"

            summary[option_category]["strikes"].append(data.get("strike"))

            summary[option_category]["days_left"].append(data.get("days_left"))

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
    


class MarketState:
    """
    This class holds all market data, sanitized data, and data needed for processing.

    Attributes:
        staging_data:
            * timestamp: Current UNIX timestamp
            * by_instrument: 
                Data of prices, volume, open interest, funding rate, liquidations, and some exchange positions data
                for every instrument type (e.g., spot, future, perpetual, etc.)
            * global: 
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
    def __init__(self, streams_data, cdepth_spot=True, cdepth_future=True, rdepth_spot=True, rdepth_future=True, dead_instruments_timeout=600):
        """ dead_instruments_timeout : timeinterval for removing expired futures"""
        self.streams_data = streams_data
        self.dead_instruments_timeout = dead_instruments_timeout
        self.staging_data = self.create_marketstate_datastructure(self.streams_data, cdepth_spot, cdepth_future, rdepth_spot, rdepth_future)
        self.raw_data = self.create_raw_datastructure()

    def create_marketstate_datastructure(self, streams_data, cdepth_spot, cdepth_future, rdepth_spot, rdepth_future, *args, **kwargs,):
        """ 
            Creates datastructed based on selected streams
        """
        global_data_structure = {}
        byinsttument_structure = {}
        aggregated_maps_structure = {}
        ticks = {}
        oi_option = False
        metrics_to_insttype = [(s.get("objective"), s.get("instTypes") or s.get("instType")) for s in streams_data]
        
        if {("trades", "spot")}.issubset(metrics_to_insttype):
            global_data_structure["price_spot"] = 0
            global_data_structure["buys_spot"] = 0
            global_data_structure["sells_spot"] = 0
            
            byinsttument_structure["price_spot"] = {}
            aggregated_maps_structure["buys_spot"] = {}
            aggregated_maps_structure["sells_spot"] = {}
            
            ticks["trades_spot"] = {}
            
        if {("trades", "perpetual")}.issubset(metrics_to_insttype) or {("trades", "future")}.issubset(metrics_to_insttype):
            global_data_structure["price_future"] = 0
            global_data_structure["buys_future"] = 0
            global_data_structure["sells_future"] = 0
            byinsttument_structure["price_future"] = {}
            aggregated_maps_structure["buys_future"] = {}
            aggregated_maps_structure["sells_future"] = {}
            
            ticks["trades_future"] = {}
            
        if {("trades", "option")}.issubset(metrics_to_insttype) or {("trades", "optionTrades")}.issubset(metrics_to_insttype):
            global_data_structure["buys_option"] = 0
            global_data_structure["sells_option"] = 0
            aggregated_maps_structure["buys_option"] = {}
            aggregated_maps_structure["sells_option"] = {}
            ticks["trades_option"] = {}
        if {("oi", "perpetual")}.issubset(metrics_to_insttype) or {("oi", "future")}.issubset(metrics_to_insttype):
            global_data_structure["oi_future"] = 0
            byinsttument_structure["oi_future"] = {}
            aggregated_maps_structure["oi_deltas"] = {}
            ticks["oi_deltas"] = {}
        if {("oi", "option")}.issubset(metrics_to_insttype) or {("oi", "oioption")}.issubset(metrics_to_insttype):
            global_data_structure["oi_option"] = 0
            oi_option = True
        if "liquidations" in [x.get("objective") for x in streams_data]:
            global_data_structure["longs"] = 0
            global_data_structure["shorts"] = 0
            aggregated_maps_structure["longs"] = {}
            aggregated_maps_structure["shorts"] = {}
        if "trades" in [x.get("objective") for x in streams_data] and {"deribit", "gateio"}.issubset([x.get("exchnage") for x in streams_data]):
            insttypes = [x.get("instType").split("_")[0] or x.get("instTypes").split("_")[0] for x in streams_data]
            if {"perpetual", "future"}.issubset(insttypes):
                global_data_structure["longs"] = 0
                global_data_structure["shorts"] = 0
                aggregated_maps_structure["longs"] = {}
                aggregated_maps_structure["shorts"] = {}
        if "funding" in [x.get("objective") for x in streams_data]:
            global_data_structure["funding"] = 0
            byinsttument_structure["funding"] = {}
        if "oifunding" in [x.get("objective") for x in streams_data]:
            global_data_structure["oi_future"] = 0
            global_data_structure["funding"] = 0
            byinsttument_structure["funding"] = {}
            aggregated_maps_structure["oi_deltas"] = {}
            ticks["oi_deltas"] = {}
            
        if {("depth", "spot")}.issubset(metrics_to_insttype):
            aggregated_maps_structure["depth_spot"] = {}
            if cdepth_spot:
                aggregated_maps_structure["cdepth_spot"] = {}
            if rdepth_spot:
                aggregated_maps_structure["rdepth_spot"] = {}

        if {("depth", "perpetual")}.issubset(metrics_to_insttype):
            aggregated_maps_structure["depth_future"] = {}
            if cdepth_future:
                aggregated_maps_structure["cdepth_future"] = {}
            if rdepth_future:
                aggregated_maps_structure["rdepth_future"] = {}
        
        if {("gta", "perpetual")}.issubset(metrics_to_insttype) or {("tta", "perpetual")}.issubset(metrics_to_insttype):
            byinsttument_structure["ttp_long_ratio"] = {}
            byinsttument_structure["ttp_short_ratio"] = {}
            byinsttument_structure["ttp_ratio"] = {}
            byinsttument_structure["tta_long_ratio"] = {}
            byinsttument_structure["tta_short_ratio"] = {}
            byinsttument_structure["tta_ratio"] = {}
            byinsttument_structure["gta_long_ratio"] = {}
            byinsttument_structure["gta_short_ratio"] = {}
            byinsttument_structure["gta_ratio"] = {}
            byinsttument_structure["tta_size_ratio"] = {}
            byinsttument_structure["ttp_size_ratio"] = {}
            byinsttument_structure["gta_size_ratio"] = {}

        d = {
            "global" : global_data_structure,
            "by_instrument" : byinsttument_structure,
            "maps" : aggregated_maps_structure,
            "ticks" : ticks
        }
        
        if oi_option:
            d["oi_options"] = {}
        return d
    
    def create_raw_datastructure(self):
        """ creates datastructure that will be merged"""
        d = {
                "dataframes_to_merge": {
                    "depth" : {
                        "spot" : {}, 
                        "future" : {}
                        },
                    "trades" : {
                        "spot" :  {"buys" : {}, "sells" : {}, "total" : {}, "delta" : {}}, 
                        "future" : {"buys" : {}, "sells" : {}, "total" : {}, "delta" : {}}, 
                        "option" :  {"buys" : {}, "sells" : {}, "total" : {}, "delta" : {}}
                                },
                    "oi_deltas" : {},
                    "oi_options" : {"calls" : {}, "puts" : {}},
                    "liquidations" : {"longs" : {}, "shorts" : {}}
                },
                "ticks_data_to_merge": {
                    "trades" : {"spot" : {}, "future" : {}, "option" : {}},
                    "oi_deltas" : {},
                },
                "merged_dataframes": {
                    "depth" : {"spot" : pd.DataFrame(), "future" : pd.DataFrame()},
                    "trades" : {
                        "spot" :  {"buys" : pd.DataFrame(), "sells" : pd.DataFrame(), "total" : pd.DataFrame()}, 
                        "future" : {"buys" : pd.DataFrame(), "sells" : pd.DataFrame(), "total" : pd.DataFrame()}, 
                        "option" :  {"buys" : pd.DataFrame(), "sells" : pd.DataFrame(), "total" : pd.DataFrame()}
                                },
                    "oi_deltas" : pd.DataFrame(),
                    "oi_options" : {"puts" : pd.DataFrame() , "calls":pd.DataFrame()},
                    "liquidations" : {"longs" : pd.DataFrame(), "shorts" : pd.DataFrame()},
                    "cdepth" : {"spot" : pd.DataFrame(), "future" : pd.DataFrame()},
                    "rdepth" : {"spot" : pd.DataFrame(), "future" : pd.DataFrame()},
                },
            }
        return d
    
    def input_merged_dataframe(self, metric, inst_type=None, metric_subtype=None,  df=None):
        """ inputs merged dataframe """
        if metric_subtype:
            self.raw_data["merged_dataframes"][metric][inst_type][metric_subtype] = df
        elif not metric_subtype:
            self.raw_data["merged_dataframes"][metric][inst_type] = df
            
    def input_data(self, metric : str, symbol : str, quantity : float):
        """ inputs data by metric """
        self.staging_data["by_instrument"][metric][symbol] = quantity

    def get_data(self, metric : str, symbol : str, default_value=None):
        """ inputs data by metric """
        return self.staging_data.get("by_instrument", {}).get(metric, {}).get(symbol, default_value)
    
        
    def merge_dataframes(self, dataframes:list):
        pass
    
    def merge_ticks(self, ticks:list):
        pass
    
    def remove_dead_byinstrument_instruments(self):
        """ removes expired future instruments of by_insturment datastruvcture """
        for instrument in self.staging_data.get("by_instrument").get("oi_future").copy():
            if self.is_contract_expired(instrument):
                del self.staging_data["by_instrument"]["oi_future"][instrument]

    def remove_dead_dataframes_to_merge(self):
        """ removes expired future instruments from df to merge datastructure"""
        for instrument in self.raw_data.get("dataframes_to_merge").get("oi_delta").copy():
            if self.is_contract_expired(instrument):
                del self.raw_data["dataframes_to_merge"]["oi_delta"][instrument]

    def remove_dead_ticks_to_merge(self):
        """ removes expired future instruments from ticks datastructure"""
        for instrument in self.raw_data.get("ticks_data_to_merge").get("oi_delta").copy():
            if self.is_contract_expired(instrument):
                del self.raw_data["ticks_data_to_merge"]["oi_delta"][instrument]
                
    async def create_task_remove_expired_instruments(self):
        """ Asyncronious task for removing dead instruments """
        while True:
            self.remove_dead_byinstrument_instruments()
            await asyncio.sleep(self.dead_instruments_timeout)

    @staticmethod
    def is_contract_expired(contract_str):
        """ hellper for removing expired contracts """
        contract_str = contract_str.split("@")[0]
        normalized_str = contract_str.replace('"', '').replace('_', '-').split("-")[-1]
        if len(normalized_str) == 8 and normalized_str.isdigit():
            date = datetime.strptime(normalized_str, '%Y%m%d')
        elif len(normalized_str) == 6 and normalized_str.isdigit():
            date = datetime.strptime(normalized_str, '%y%m%d')
        else:
            date = datetime.strptime(normalized_str, '%d%b%y')
        today_date = datetime.now().date()
        return date.date() <= today_date

    def generate_unique_id(self) -> str:
        """Generates a unique identifier using UUID4."""
        return str(uuid.uuid4())

    def calculate_global_metrics(self,):
        """ calculates global metrics"""
        for metric in self.staging_data.get("by_instrument"):
            if True:
                pass
        
    def retrive_staging_data(self):
        """ Retrives data is json format to insert into database"""
        return self.staging_data
    

