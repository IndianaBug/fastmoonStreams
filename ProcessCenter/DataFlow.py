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
from .StreamDataClasses import OrderBook, MarketTradesLiquidations

pd.set_option('future.no_silent_downcasting', True)
        
        
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
        self.dfp = pd.DataFrame()
        # Helpers
        self.last_receive_time = 0
        self.running = False

    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.level_size) * self.level_size
    
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
        
    def dump_df_to_csv(self, location, type_):
        if type_ == 1:
            self.df.to_csv(location, index=False)
        if type_ == 2:
            self.dfp.to_csv(location, index=False)


    async def input_into_pandas_df(self):
        """ Inputs bids and asks into pandas dataframe """
        
        await self.books.trim_books()
        
        prices = np.array(list(map(float, self.books.bids.keys())) + list(map(float, self.books.asks.keys())), dtype=np.float64)
        
        amounts = np.array(list(map(float, self.books.bids.values())) + list(map(float, self.books.asks.values())), dtype=np.float64)
        
        levels = [self.find_level(price) for price in  prices]
        
        unique_levels, inverse_indices = np.unique(levels, return_inverse=True)
        group_sums = np.bincount(inverse_indices, weights=amounts)
        columns = [str(col) for col in unique_levels]
        timestamp = int(time.time() % self.books_process_interval)
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
                
        # self.dump_df_to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/books_unprocessed.csv", 1)
        

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
            await self.input_into_pandas_df()
            # print(self.df)
            await asyncio.sleep(self.book_snap_interval)


    async def schedule_processing_dataframe(self):
        """ Generates dataframe of processed books """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.books_process_interval)
                
                # self.dump_df_to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/books.csv", 1)

                for col in self.df.columns:
                    self.df[col] = self.df[col].replace(0, pd.NA).ffill()
                    self.df[col] = self.df[col].replace(0, pd.NA).bfill()
                self.dfp = self.df.copy()
                
                # self.dump_df_to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/books_processed.csv", 2)
                
                self.df = pd.DataFrame()
                
                if self.mode == "testing":
                    self.generate_data_for_plot(f"sample_data/books_{self.connection_data.get('id_ws')}.json")
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            

    def generate_data_for_plot(self, file_path):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            for index, row in self.dfp.iterrows():
                if not all(row == 0):
                    break
            plot_data = {
                'x': [float(x) for x in row.index.tolist()],
                'y': row.values.tolist(),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'Books for every level at timestamp {index}, {self.exchange}, {self.symbol}'
            }
            with open(file_path, 'w') as file:
                json.dump(plot_data, file)
        except Exception as e:
            print(e)
            


class tradesflow():
    """
        Important notes:
            Aggregation explanation:  If the level_size is 20, books between [0-20) go to level 20, [20, 40) go to level 40, and so forth.
    """

    def __init__(self,
                 exchange : str,
                 symbol : str,
                 inst_type : str,
                 price_level_size : int,
                 on_message : callable,
                 trades_process_interval : int = 10,
                 mode = "production",
                 ):
        """
            insType : spot, future, perpetual
            price_level_size : the magnitude of the level to aggragate upon (measured in unites of the quote to base pair)
            on_message : function to extract details from the response
        """
        self.connection_data = dict()
        self.market_state = dict()
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = inst_type
        self.on_message = on_message
        self.price_level_size = float(price_level_size)
        self.trades_process_interval = trades_process_interval
        # helpers
        self.dfbuys = pd.DataFrame()
        self.dfsells = pd.DataFrame()
        self.dftotal = pd.DataFrame()
        self.Trades = MarketTradesLiquidations()
        self.buys = dict()
        self.sells = dict()

        self.mode = mode

    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.price_level_size) * self.price_level_size
    
    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_connection_data(self, connection_data):
       """ passes connectiondata dictionary"""
       self.connection_data = connection_data

    def input_data(self, data, *args, **kwargs) :
        """ inputs data"""
        try:
            processed_data = self.on_message(data, self.connection_data, self.market_state)
            self.Trades.add_trades(processed_data)
        except:
            return
    
    def create_pandas_dataframe(self, type_):
        """
            Common method to process trades and update the DataFrame
            type_ : buys or sells
        """
        data_object = self.Trades.buys if type_ == "buys" else self.Trades.sells
        df = pd.DataFrame(0, index=list(range(0, self.trades_process_interval)))
        for timestamp in data_object:
            for trade in data_object.get("timestamp"):
                price = trade.get("price")
                quantity = trade.get("quantity")
                index_timestamp = int(timestamp % self.trades_process_interval)
                level = self.find_level(price)
                current_columns = (map(float, [x for x in df.columns.tolist()]))
                if level not in current_columns:
                    df[str(level)] = 0
                    df[str(level)] = df[str(level)].astype("float64")
                    df.loc[index_timestamp, str(level)] += quantity
                else:
                    df.loc[index_timestamp, str(level)] += quantity
        return df.fillna(0, inplace = True)

    def make_dataframes(self):
        """ generates processed dataframes of trades """
        self.dfbuys = self.create_pandas_dataframe("buys")
        self.dfsells = self.create_pandas_dataframe("sells")
        # Merge dfs
        merged_df = pd.merge(self.dfbuys.copy(), self.dfsells.copy(), left_index=True, right_index=True, how='outer', suffixes=('_buys', '_sells')).fillna(0)
        common_columns_dic = {column.split("_")[0] : [] for column in merged_df.columns.tolist()}
        for column in merged_df.columns.tolist():
            common_columns_dic[column.split("_")[0]].append(column)
        self.dftotal = pd.DataFrame(0, index=list(range(0, self.trades_process_interval)), dtype='float64')
        for common_columns in common_columns_dic.keys():
            for index, column in enumerate(common_columns_dic[common_columns]):
                if index == 0 :
                    self.dftotal[common_columns] = merged_df[column]
                else:
                    self.dftotal[common_columns] = self.dftotal[common_columns] + merged_df[column]


    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.trades_process_interval)
                self.make_dataframes()
                # self.dump_df_to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/trades_buys.csv", 1)
                # self.dump_df_to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/trades_sells.csv", 1)
                # self.dump_df_to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/trades_total.csv", 1)
                self.buys = self.Trades.buys
                self.sells = self.Trades.sells
                self.Trades.reset_trades()
                if self.mode == "testing":
                    self.generate_data_for_plot(f"sample_data/books_{self.connection_data.get('id_ws')}.json")
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")


    def generate_data_for_plot(self, file_path):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            for type_, df in {"sells" : self.dfbuys, "buys" : self.dfsells, "total" : self.dftotal}.items():

                plot_data = {
                    'x': [float(x) for x in df.columns],
                    'y': df.sum().tolist(),
                    'xlabel': 'Level',
                    'ylabel': 'Amount',
                    'legend': f'Trades sum over {self.trades_process_interval}, {self.exchange}, {self.symbol} '
                }

                splitted_file_path = file_path.split(".")
                splitted_file_path[0] = splitted_file_path+"_"+type_
                file_path = ".".join(splitted_file_path)

                with open(file_path, 'w') as file:
                    json.dump(plot_data, file)
        except Exception as e:
            print(e)



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