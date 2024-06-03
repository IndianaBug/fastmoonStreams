import numpy as np
import pandas as pd
import dask
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import time
import datetime
import json
import h5py
import asyncio
import uuid
import matplotlib.pyplot as plt
import math
import pandas as pd
import numpy as np
import socket
import multiprocessing as mp
import logging

pd.set_option('future.no_silent_downcasting', True)

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
        
        
        
class booksflow():
    """
        Important notes:
            If the book is above book_ceil_thresh from the current price, it will be omited.
            Aggregation explanation:  If the level_size is 20, books between [0-20) go to level 20, [20, 40) go to level 40, and so forth.
    """
    def __init__(self,
                 exchange : str,
                 symbol : str,
                 inst_type : str,
                 price_level_size : int,
                 api_on_message : callable,
                 ws_on_message : callable,
                 book_snap_interval : int = 1,
                 books_process_interval : int = 10,
                 book_ceil_thresh = 5,
                 mode = "production",
                 ):
        """
            insType : spot, future, perpetual
            level_size : the magnitude of the level to aggragate upon (measured in unites of the quote to base pair)
            book_ceil_thresh : % ceiling of price levels to ommit, default 5%
            number_of_paritions : number of partitions for dusk to work in paralel
            book_processing_timespan : Specifies the timespan for processing the books, canceled and reinforced.
            books_snapshot_timestan_ratio : needed for the interval of taking a snapshot
                                            books_snpshot_interval = (book_processing_timespan / books_snapshot_timestan_ratio)
                                            as books_snapshot_timestan_ratio must be < than book_processing_timespan
        """
        self.mode = mode

        self.connection_data = dict()
        self.market_state = dict()
        # Identification
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = inst_type
        self.api_on_message = api_on_message
        self.ws_on_message = ws_on_message
        self.level_size = float(price_level_size)
        self.book_ceil_thresh = int(book_ceil_thresh)
        self.book_snap_interval = int(book_snap_interval)
        self.books_process_interval = int(books_process_interval)
        self.books = OrderBook(self.book_ceil_thresh)
        self.df = pd.DataFrame()
        self.processed_df = None
        # Helpers
        self.last_receive_time = 0
        self.running = False

    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.level_size) * self.level_size
    
    def scale_current_timestamp(self):
        """ scales timestamp to a propepr interval """
        current_timestamp = int(time.time() % 60)
        scaled_timestamp = (self.books_process_interval * current_timestamp) / int(60 / self.books_process_interval)
        return int(scaled_timestamp)

    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_connection_data(self, connection_data):
       """ passes connectiondata dictionary"""
       self.connection_data = connection_data

    async def input_data_api(self, data:str):
        """ inputs books from api into dataframe"""
        try:
            processed_data = await self.api_on_message(data, self.market_state, self.connection_data)
            await self.books.update_data(processed_data)
        except:
            return

    async def input_data_ws(self, data:str):
        """ inputs books from ws into dataframe"""
        try:
            processed_data = await self.ws_on_message(data, self.market_state, self.connection_data)
            recieve_time = processed_data.get("receive_time")
            if self.last_receive_time < recieve_time:
                await self.books.update_data(processed_data)
                self.last_receive_time = recieve_time
            self.last_receive_time = recieve_time
        except:
            return

    def input_into_pandas_df(self):
        """ Inputs bids and asks into pandas dataframe """
        prices = np.array(list(map(float, self.books.bids.keys())) + list(map(float, self.books.asks.keys())), dtype=np.float64)
        amounts = np.array(list(map(float, self.books.bids.values())) + list(map(float, self.books.asks.values())), dtype=np.float64)
        levels = [self.find_level(price) for price in  prices]
        unique_levels, inverse_indices = np.unique(levels, return_inverse=True)
        group_sums = np.bincount(inverse_indices, weights=amounts)
        columns = [str(col) for col in unique_levels]
        timestamp = self.scale_current_timestamp()
        print(timestamp)
        if self.df.empty:
            self.df = pd.DataFrame(0, index=list(range(self.books_process_interval)), columns=columns, dtype='float64')
            self.df.loc[timestamp] = group_sums
            sorted_columns = sorted(map(float, self.df.columns))
            self.df = self.df[map(str, sorted_columns)]
        else:
            old_levels = np.array(self.df.columns, dtype=np.float64)
            new_levels = np.setdiff1d(np.array(columns, dtype=np.float64), old_levels)
            for l in new_levels:
                self.df[str(l)] = 0
                self.df[str(l)]= self.df[str(l)].astype("float64")
            sums = self.manipulate_arrays(old_levels, np.array(columns, dtype=np.float64), group_sums)
            self.df.loc[timestamp] = sums
            sorted_columns = sorted(map(float, self.df.columns))
            self.df = self.df[map(str, sorted_columns)]

    @staticmethod
    def manipulate_arrays(old_levels, new_levels, new_values):
        """ helper for snapshot creating, dynamically deals with new columns """
        new_isolated_levels = np.setdiff1d(new_levels, old_levels)
        sorted_new_values = np.array([])
        for i in range(len(old_levels)):
            index = np.where(new_levels == old_levels[i])[0]
            if len(index) != 0:
                sorted_new_values = np.append(sorted_new_values, new_values[index])
            else:
                sorted_new_values = np.append(sorted_new_values,0)
        for i in range(len(new_isolated_levels)):
            index = np.where(new_levels == new_isolated_levels[i])[0]
            if len(index) != 0:
                sorted_new_values = np.append(sorted_new_values, new_values[index])
            else:
                sorted_new_values = np.append(sorted_new_values,0)
        return sorted_new_values
    
    async def schedule_snapshot(self):
        """ creates task for input_into_pandas_df """
        await asyncio.sleep(1)
        while True:
            self.input_into_pandas_df()
            # print(self.df)
            await asyncio.sleep(self.book_snap_interval)


    async def schedule_processing_dataframe(self):
        """ Generates dataframe of processed books """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.books_process_interval)
                await self.books.trim_books()
                for col in self.df.columns:
                    self.df[col] = self.df[col].replace(0, pd.NA).ffill()
                    self.df[col] = self.df[col].replace(0, pd.NA).bfill()
                self.processed_df = self.df.copy()
                self.df = pd.DataFrame()
                if self.mode == "testing":
                    self.generate_data_for_plot(f"sample_data/{self.connection_data.get('id_ws')}.json")
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            

    def generate_data_for_plot(self, file_path):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        for index, row in self.processed_df.iterrows():
            if not all(row == 0):
                timestamp = self.df[index].index
                break
        plot_data = {
            'x': [float(x) for x in row.columns.tolist()],
            'y': row.values.tolist(),
            'xlabel': 'Level',
            'ylabel': 'Amount',
            'legend': [f'Books for every level at timestamp {timestamp}']
        }
        with open(file_path, 'w') as file:
            json.dump(plot_data, file)
            




# @dataclass
# class Trades:

#     timestamp: Optional[float] = field(default_factory=lambda: time.time())
#     buys: Dict[float, List[List[float, float]]] = field(default_factory=dict)
#     sells: Dict[float, List[List[float, float]]] = field(default_factory=dict)

#     async def add_sell(self, timestamp: float, price: float, quantity: float):
#         if quantity > 0:
#             if timestamp not in self.sells:
#                 self.sells[timestamp] = []
#             self.sells[timestamp].append([price, quantity])

#     async def add_buy(self, timestamp: float, price: float, quantity: float):
#         if quantity > 0:
#             if timestamp not in self.buys:
#                 self.buys[timestamp] = []
#             self.buys[timestamp].append([price, quantity])

#     async def drop_data(self):
#         buys = self.buys.clear()
#         sells = self.sells.clear()
#         self.buys.clear()
#         self.sells.clear()
#         return buys, sells

#     async def drop_buys(self):
#         buys = self.buys.clear()
#         self.buys.clear()
#         return buys

#     async def drop_sells(self):
#         sells = self.sells.clear()
#         self.sells.clear()
#         return sells


# class tradesflow():
#     """
#         Important notes:
#             Aggregation explanation:  If the level_size is 20, books between [0-20) go to level 20, [20, 40) go to level 40, and so forth.
#     """

#     def __init__(self,
#                  exchange :str,
#                  symbol : str,
#                  inst_type : str,
#                  exchange_symbol:str,
#                  level_size : int,
#                  api_on_message : callable,
#                  ws_on_message : callable,
#                  trades_processing_timespan : int,
#                  trades_snapshot_interval : int,
#                  npartitions=5
#                  ):
#         """
#             insType : spot, future, perpetual
#             level_size : the magnitude of the level to aggragate upon (measured in unites of the quote to base pair)
#             lookup : function to extract details from the response
#         """
#         self.connection_data = dict()
#         self.market_state = dict()
#         self.dask_client = dask_Client()
#         # Identification
#         self.exchange = exchange
#         self.symbol = symbol
#         self.exchange_symbol = exchange_symbol
#         self.inst_type = inst_type
#         self.api_on_message = api_on_message
#         self.ws_on_message = ws_on_message
#         self.level_size = float(level_size)
#         self.trades_processing_timespan = trades_processing_timespan
#         self.npartitions = npartitions
#         self.processed_df = None
#         self.price = 0
#         self.running = False
#         self.processed_df_buys = dask.from_pandas(pd.DataFrame())
#         self.processed_df_sells = dask.from_pandas(pd.DataFrame())
#         self.current_second = time.time()
#         self.previous_second = time.time()
#         self.counter = 0
#         self.df_buys = dask.from_pandas(
#             pd.DataFrame(0, index=list(range(0, self.trades_processing_timespan, 1)), columns=np.array(['price']), dtype='float64'),
#             npartitions=self.npartitions
#         )
#         self.df_sells = dask.from_pandas(
#             pd.DataFrame(0, index=list(range(0, self.trades_processing_timespan, 1)), columns=np.array(['price']), dtype='float64'),
#             npartitions=self.npartitions
#         )
#         self.Trades = Trades()
#         self.buys = dict()
#         self.sells = dict()

#     def pass_market_state(self, market_state):
#        self.market_state = market_state

#     def pass_dask_client(self, dask_client):
#        self.dask_client = dask_client

#     def pass_connection_data(self, connection_data):
#        self.connection_data = connection_data

#     def find_level(self, price):
#         """ helper for snapshot creation"""
#         return np.ceil(price / self.level_size) * self.level_size

#     def input_trades(self, data, message_type:str, *args, **kwargs) :
#         method = self.ws_on_message if message_type == "ws" else self.api_on_message
#         try:
#             data_trades = self.method(data)
#             for trade in data_trades.get("trades")
#                 side = trade.get("side")
#                 price = trade.get("price")
#                 quantity = trade.get("quantity")
#                 timestamp = trade.get("timestamp")
#                 if side == "sell":
#                     self.Trades.add_sell(timestamp, price, quantity):
#                 elif side == "buy":
#                     self.Trades.add_buy(timestamp, price, quantity):
#         except:
#             return

#     def process_trades(self, trades_dict : dict, df : dask.DataFrame):
#         """Common method to process trades and update the DataFrame"""
#         for timestamp in trades_dict:
#             for trades in trades_dict.get(timestamp):
#                 for trade in trades:
#                     self.current_second = datetime.datetime.strptime(self.OrderBook.timestamp, '%Y-%m-%d %H:%M:%S').second
#                     self.counter = int(self.trades_processing_timespan / 60 * self.current_second)
#                     price = trade[0]
#                     amount = trade[1]
#                     df.loc[self.counter, 'price'] = price
#                     level = self.find_level(price, self.level_size)
#                     current_columns = (map(float, [x for x in df.columns.tolist() if x != "price"]))
#                     if level not in current_columns:
#                         df[str(level)] = 0
#                         df[str(level)] = df[str(level)].astype("float64")
#                         df.loc[self.counter, str(level)] += amount
#                     else:
#                         df.loc[self.counter, str(level)] += amount

#     async def generate_processed_dataframe(self):
#         """ generates snapshot of trades with dask dataframe """
#         self.process_trades(self.Trades.buys, self.df_buys)
#         self.process_trades(self.Trades.sells, self.df_sells)
#         self.processed_df_buys = self.df_buys.copy()
#         self.processed_df_sells = self.df_sells.copy()
#         self.processed_df_buys.fillna(0, inplace = True)
#         self.processed_df_sells.fillna(0, inplace = True)

#         # Merge buys and sells
#         merged_df = pd.merge(self.processed_df_sells.copy(), self.processed_df_sells.copy(), left_index=True, right_index=True, how='outer', suffixes=('_buys', '_sells')).fillna(0)
#         for column in merged_df.columns.tolist():
#             common_columns_dic[column.split("_")[0]].append(column)

#         self.processed_df_total = dask.from_pandas(
#             pd.DataFrame(0, index=list(range(0, self.trades_processing_timespan, 1)), columns=np.array(['price']), dtype='float64'),
#             npartitions=self.npartitions
#         )
#         for common_columns in common_columns_dic.keys():
#             for index, column in enumerate(common_columns_dic[common_columns]):
#                 if index == 0 and "price" not in column:
#                     self.processed_df_total[common_columns] = merged_df[column]
#                 if "price" not in column and index != 0:
#                     self.processed_df_total[common_columns] = self.processed_df_total[common_columns] + merged_df[column]
#         self.processed_df_total.insert(0, 'price', self.snapshot_buys['price'])




#         self.df_buys = dask.from_pandas(
#             pd.DataFrame(0, index=list(range(0, self.trades_processing_timespan, 1)), columns=np.array(['price']), dtype='float64'),
#             npartitions=self.npartitions
#         )
#         self.df_sells = dask.from_pandas(
#             pd.DataFrame(0, index=list(range(0, self.trades_processing_timespan, 1)), columns=np.array(['price']), dtype='float64'),
#             npartitions=self.npartitions
#         )
#         buys, sells = self.Trades.drop_data()
#         self.buys = buys
#         self.sells = sells

#     async def schedule_data_processing(self, testing_mode=False, file_path=None):
#         """ schedules tasks for """
#         self.running = True
#         while self.running:
#             task_id = uuid.uuid4()
#             future = self.dask_client.submit(self.generate_processed_dataframe, task_id)
#             await asyncio.wrap_future(future)
#             buys, sells = self.Trades.drop_data()
#             self.buys = buys
#             self.sells = sells
#             asyncio.sleep(self.trades_processing_timespan)
#             if testing_mode:
#               self.generate_data_for_plot(file_path)

#     def generate_data_for_plot(self, file_path):
#         """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
#         pandas_series = self.buys.iloc[:, 1:].sum()
#         for index, row in self.df.iterrows():
#             if not all(row == 0):
#                 timestamp = self.df[index].index
#                 break
#         pandas_series = row.compute()

#         plot_data = {
#             'x': [float(x) for x in pandas_series.columns.tolist()],
#             'y': pandas_series.values.tolist(),
#             'xlabel': 'Level',
#             'ylabel': 'Amount',
#             'legend': [f'Trades for every level at timestamp {timestamp}']
#         }

#         with open(file_path, 'w') as file:
#             json.dump(plot_data, file)




#     def process_trades(self, side, price, amount, timestamp):

#         self.current_second = int(datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').second)



#         if self.previous_second > self.current_second:


#             self.snapshot_buys = self.buys.copy()
#             self.snapshot_buys.fillna(0, inplace = True)
#             self.snapshot_sells = self.sells.copy()
#             self.snapshot_sells.fillna(0, inplace = True)

#             self.snapshot_buys['price'] = self.snapshot_buys['price'].replace(0, pd.NA).ffill()
#             self.snapshot_buys['price'] = self.snapshot_buys['price'].replace(0, pd.NA).bfill()
#             self.snapshot_sells['price'] = self.snapshot_sells['price'].replace(0, pd.NA).ffill()
#             self.snapshot_sells['price'] = self.snapshot_sells['price'].replace(0, pd.NA).bfill()

#             merged_df = pd.merge(self.snapshot_buys.copy(), self.snapshot_sells.copy(), left_index=True, right_index=True, how='outer', suffixes=('_buys', '_sells')).fillna(0)

#             common_columns_dic = {column.split("_")[0] : [] for column in merged_df.columns.tolist()}
#             for column in merged_df.columns.tolist():
#                 common_columns_dic[column.split("_")[0]].append(column)

#             self.snapshot_total = pd.DataFrame()
#             for common_columns in common_columns_dic.keys():
#                 for index, column in enumerate(common_columns_dic[common_columns]):
#                     if index == 0 and "price" not in column:
#                         self.snapshot_total[common_columns] = merged_df[column]
#                     if "price" not in column and index != 0:
#                         self.snapshot_total[common_columns] = self.snapshot_total[common_columns] + merged_df[column]
#             self.snapshot_total.insert(0, 'price', self.snapshot_buys['price'])





# class DaskClientSupport():
#     logger = logging.getLogger("Example")  # just a reference
#     def find_free_port(self, start=8787, end=8800):
#         for port in range(start, end):
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 try:
#                     s.bind(('', port))
#                     return port
#                 except OSError:
#                     self.logger.error("Dask error, free port: %s", OSError, exc_info=True)
#                     continue
#         raise RuntimeError(f"No free ports available in range {start}-{end}")

#     def start_dask_client(self):
#         for attempt in range(5):
#             try:
#                 # Check for an available port
#                 free_port = self.find_free_port()
#                 print(f"Using port: {free_port}")

#                 # Initialize the Dask Client with the available port
#                 client = Client(n_workers=1, threads_per_worker=1, port=free_port)
#                 return client
#             except RuntimeError as e:
#                 self.logger.error("Dask error, RuntimeError, reconnecting: %s", e, exc_info=True)
#                 print(f"Attempt {attempt + 1}: {str(e)}")
#             except Exception as e:
#                 self.logger.error("Dask error, Unexpected error: %s", e, exc_info=True)
#                 print(f"Attempt {attempt + 1}: Unexpected error: {str(e)}")
#         raise RuntimeError("Failed to start Dask Client after several attempts")