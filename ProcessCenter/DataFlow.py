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
from .StreamDataClasses import OrderBook, MarketTradesLiquidations, OpenInterest, OptionInstrumentsData, InstrumentsData

pd.set_option('future.no_silent_downcasting', True)


# Fix books stuff
# Different trades, different measures. Probably more than a single process method needed, fixit
        
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
        
        # Helper for testing
        self.folderpath = ""
        
    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.level_size) * self.level_size
    
    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_connection_data(self, connection_data):
       """ passes connectiondata dictionary"""
       self.connection_data = connection_data

    def pass_savefolder_path(self, folderpath):
       """ passes connectiondata dictionary"""
       self.folderpath = folderpath

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
        
        if self.mode == "testing":
            print(self.df)     

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
                
                if self.mode == "testing":
                    self.dump_df_to_csv("raw")

                for col in self.df.columns:
                    self.df[col] = self.df[col].replace(0, pd.NA).ffill()
                    self.df[col] = self.df[col].replace(0, pd.NA).bfill()
                self.dfp = self.df.copy()
                
                if self.mode == "testing":
                    self.dump_df_to_csv("processed")
                
                self.df = pd.DataFrame()
                
                if self.mode == "testing":
                    self.generate_data_for_plot()
                    
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            

    def generate_data_for_plot(self):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        name = self.connection_data.get("id_ws")
        filepath = f"{self.folderpath}/sample_data/plots/{name}.csv"
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
            with open(filepath, 'w') as file:
                json.dump(plot_data, file)
        except Exception as e:
            print(e)
            
    def dump_df_to_csv(self, dftype):
        """ processed, raw"""
        name = self.connection_data.get("id_ws")
        file_path = f"{self.folderpath}/sample_data/pandasdf/{dftype}/{name}.csv"
        if dftype == "raw":
            self.df.to_csv(file_path, index=False)
        if dftype == "processed":
            self.dfp.to_csv(file_path, index=False)
            
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
        self.dfpbuys = pd.DataFrame()
        self.dfpsells = pd.DataFrame()
        self.dfptotal = pd.DataFrame()
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
                # self.dfpbuys.to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/trades_buys.csv", index=False)
                # self.dfpsells.to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/trades_sells.csv", index=False)
                # self.dfptotal.to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/trades_total.csv", index=False)
                self.buys = self.Trades.buys
                self.sells = self.Trades.sells
                self.Trades.reset_trades()
                if self.mode == "testing":
                    self.generate_data_for_plot(f"sample_data/trades_{self.connection_data.get('id_ws')}.json")
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

class oiflow():
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
                 oi_process_interval : int = 10,
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
        self.oi_process_interval = oi_process_interval
        # helpers
        self.dfp = pd.DataFrame()
        self.ois = OpenInterest()
        self.mode = mode
        self.last_recieve_time = 0

    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.price_level_size) * self.price_level_size
    
    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_connection_data(self, connection_data):
       """ passes connectiondata dictionary"""
       self.connection_data = connection_data

    async def input_data(self, data:str):
        """ 
            inputs data into oi dictionary
            on message returns  {symbols : {"oi" : value,}, "timestamp" : "", "receive_time"}
        """
        try:
            oidata = await self.on_message(data, self.market_state, self.connection_data)
            timestamp = oidata.get("receive_time")
            if timestamp > self.last_recieve_time:
                for symbol in oidata:
                    oi = oidata.get(symbol).get("oi")
                    self.ois.add_entry(timestamp, symbol, oi)
            self.last_recieve_time = timestamp
        except Exception:
            return
        
    def make_dataframe(self):
        """ creates dataframe of OIs"""
        
        dfp = pd.DataFrame(0, index=list(range(0, self.oi_process_interval)))
        
        for data_point in self.ois.data:
            timestamp =  data_point.timestamp
            instrument =  data_point.instrument
            open_interest =  data_point.open_interest
            price = data_point.price
            previous_oi = self.ois.last_values.get(instrument)
            if previous_oi:
                index_time = int(timestamp % self.oi_process_interval)
                price_level = self.find_level(price)
                current_columns = (map(float, [x for x in dfp.columns.tolist()]))
                if price_level not in current_columns:
                    dfp[str(price_level)] = 0
                    dfp[str(price_level)] = dfp[str(price_level)].astype("float64")
                    dfp[index_time, str(price_level)] = open_interest - previous_oi
                else:
                    dfp[index_time, str(price_level)] = open_interest - previous_oi
                
            self.ois.last_values[instrument] = open_interest
    
        self.dfp = dfp
    
    
    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.oi_process_interval)
                self.make_dataframe()
                # self.dfp.to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/ois.csv", index=False)
                # self.dump_df_to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/ois.csv")
                self.ois.reset_data()
                if self.mode == "testing":
                    self.generate_data_for_plot(f"sample_data/ois_{self.connection_data.get('id_ws')}.json")
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")


    def generate_data_for_plot(self, file_path):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        # ax.bar(categories, values, color=['green' if v >= 0 else 'red' for v in values])
        try:
            plot_data = {
                'x': [float(x) for x in self.dfp.columns],
                'y': self.dfp.sum().tolist(),
                'color' : ['green' if v >= 0 else 'red' for v in self.dfp.sum().tolist()],
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'Ois increases over {self.oi_process_interval}, {self.exchange}, {self.symbol} '
            }

            with open(file_path, 'w') as file:
                json.dump(plot_data, file)
        except Exception as e:
            print(e)

class liqflow():
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
                 liquidations_process_interval : int = 10,
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
        self.liquidations_process_interval = liquidations_process_interval
        # helpers
        self.dfpbuys = pd.DataFrame()
        self.dfpsells = pd.DataFrame()
        self.dfptotal = pd.DataFrame()
        self.Liquidations = MarketTradesLiquidations()
        self.shorts = dict()
        self.longs = dict()
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
            self.Liquidations.add_liquidations(processed_data)
        except:
            return
    
    def create_pandas_dataframe(self, type_):
        """
            Common method to process trades and update the DataFrame
            type_ : buys or sells
        """
        data_object = self.Liquidations.buys if type_ == "buys" else self.Liquidations.sells
        df = pd.DataFrame(0, index=list(range(0, self.liquidations_process_interval)))
        for timestamp in data_object:
            for trade in data_object.get("timestamp"):
                price = trade.get("price")
                quantity = trade.get("quantity")
                index_timestamp = int(timestamp % self.liquidations_process_interval)
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
        self.dfpbuys = self.create_pandas_dataframe("buys")
        self.dfpsells = self.create_pandas_dataframe("sells")
        # Merge dfs
        merged_df = pd.merge(self.dfpbuys.copy(), self.dfpsells.copy(), left_index=True, right_index=True, how='outer', suffixes=('_buys', '_sells')).fillna(0)
        common_columns_dic = {column.split("_")[0] : [] for column in merged_df.columns.tolist()}
        for column in merged_df.columns.tolist():
            common_columns_dic[column.split("_")[0]].append(column)
        self.dftotal = pd.DataFrame(0, index=list(range(0, self.liquidations_process_interval)), dtype='float64')
        for common_columns in common_columns_dic.keys():
            for index, column in enumerate(common_columns_dic[common_columns]):
                if index == 0 :
                    self.dfptotal[common_columns] = merged_df[column]
                else:
                    self.dfptotal[common_columns] = self.dfptotal[common_columns] + merged_df[column]


    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.liquidations_process_interval)
                self.make_dataframes()
                # self.dfpbuys.to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/liquidations_longs.csv", index=False)
                # self.dfpsells.to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/liquidations_shorts.csv", index=False)
                # self.dfptotal.to_csv("/workspaces/fastmoonStreams/sample_data/pandasdf/liquidations_total.csv", index=False)
                self.shorts = self.Liquidations.shorts
                self.longs = self.Liquidations.longs
                self.Liquidations.reset_liquidations()
                if self.mode == "testing":
                    self.generate_data_for_plot(f"sample_data/liquidations_{self.connection_data.get('id_ws')}.json")
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")


    def generate_data_for_plot(self, file_path):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            for type_, df in {"sells" : self.dfpbuys, "buys" : self.dfpsells, "total" : self.dfptotal}.items():

                plot_data = {
                    'x': [float(x) for x in df.columns],
                    'y': df.sum().tolist(),
                    'xlabel': 'Level',
                    'ylabel': 'Amount',
                    'legend': f'Liquidations sum over {self.liquidations_process_interval}, {self.exchange}, {self.symbol} '
                }

                splitted_file_path = file_path.split(".")
                splitted_file_path[0] = splitted_file_path+"_"+type_
                file_path = ".".join(splitted_file_path)

                with open(file_path, 'w') as file:
                    json.dump(plot_data, file)
        except Exception as e:
            print(e)

class ooiflow():

    """ 
        example:
            pranges = np.array([0.0, 1.0, 2.0, 5.0, 10.0])  : percentage ranges of strikes from current price
            expiry_windows = np.array([0.0, 1.0, 3.0, 7.0])  : expiration window ranges
            index_price_symbol --- "BTCUSDT@spot@binance"
    """

    def __init__(self,
                 exchange : str,
                 symbol : str,
                 pranges : np.array,
                 index_price_symbol : str,  
                 expiry_windows : np.array,
                 on_message : callable,
                 option_process_interval : int = 10,
                 mode = "production",
                 *args,
                 **kwargs,
                 ):
        """ Cool init method"""
        self.connection_data = dict()
        self.market_state = dict()
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = "option"
        self.on_message = on_message
        self.pranges = pranges
        self.expiry_windows = expiry_windows
        self.option_process_interval = option_process_interval
        self.odata = OptionInstrumentsData()
        self.dfpc = dict()
        self.dfpp = dict()
        self.mode = mode
        self.index_price_symbol = index_price_symbol
        
    def input_data(self, data:str):
        try:
            processed_data = self.on_message(data, self.connection_data, self.market_state)
            self.odata.add_instruments_bulk(processed_data)
        except Exception:
            return

    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_connection_data(self, connection_data):
       """ passes connectiondata dictionary"""
       self.connection_data = connection_data
       
    def create_dataframes(self):
        """ creates puts and calls dataframes """
        timestamp = time.time()
        data = self.odata.get_summary_by_option_type()
        for side in data:
            options_data = data.get(side)
            df = pd.DataFrame(options_data).groupby(['countdown', 'strikes']).sum().reset_index()
            df = df[(df != 0).all(axis=1)]
            dictDataFrame = self.build_option_dataframes(self.expiry_windows, self.pranges)
            helper = self.oiflowOption_dictionary_helper(dictDataFrame, options_data.get("countdowns"))
            fullPranges = self.oiflowOption_getranges(self.pranges)
            current_price = self.market_state.get(self.index_price_symbol).get("price", 100000000000000)
            for dfid in helper.keys():
                empty_df = pd.DataFrame()
                for countdown in helper[dfid]:
                    d = df[df['countdown'] == countdown ].drop(columns=['countdown'])
                    d['pcd'] = df['strikes'].apply(lambda x : self.getpcd(current_price, x))
                    d['range'] = d['pcd'].apply(lambda x: self.oiflowOption_choose_range(fullPranges, x))
                    d = d.groupby(['range']).sum().reset_index().drop(columns=["strikes", "pcd"]).set_index('range')
                    missing_values = np.setdiff1d(fullPranges, d.index.values)
                    new_rows = pd.DataFrame({'oi': 0}, index=missing_values)
                    combined_df = pd.concat([d, new_rows])
                    combined_df = combined_df.transpose() 
                    combined_df['timestamp'] = pd.to_datetime(timestamp)
                    combined_df.set_index('timestamp', inplace=True)
                    combined_df = combined_df.sort_index(axis=1)
                    empty_df = pd.concat([empty_df, combined_df], ignore_index=True)
                empty_df  = empty_df.sum(axis=0).values.T
                try:
                    dictDataFrame[dfid].loc[pd.to_datetime(timestamp)] = empty_df
                except:
                    pass
            if side == "Call":
                self.dfpc = dictDataFrame.copy()
            if side == "Put": 
                self.dfpp = dictDataFrame.copy()   
                
    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.option_process_interval)
                self.create_dataframes()
                if self.mode == "testing":
                    self.generate_data_for_plot(f"sample_data/oioption_{self.connection_data.get('id_ws')}.json")
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")


    def generate_data_for_plot(self, file_path):
        """ generates data for plots of options at a random timestamp to verify any discrepancies, good for testing """
        try:
            for type_, dict_ in zip(["Puts", "Calls"], [self.dfpp, self.dfpc]):
                for expiration in dict_:
                    df = dict_.get(expiration).transpose()
                    df = pd.Series(df.values.transpose()[0], index=df.index.values)
                    plot_data = {
                        'x': df.index,
                        'y': df.values,
                        'xlabel': 'Level',
                        'ylabel': 'Amount',
                        'legend': f'Options oi data over {self.option_process_interval}, {self.exchange}, {self.symbol}, {type_}, {expiration} '
                    }
                    splitted_file_path = file_path.split(".")
                    splitted_file_path[0] = splitted_file_path+"_"+type_+expiration
                    file_path = ".".join(splitted_file_path)
                    with open(file_path, 'w') as file:
                        json.dump(plot_data, file)
        except Exception as e:
            print(e)
                
            
    def build_option_dataframes(self, expiration_ranges, ppr):
        columns = self.oiflowOption_getcolumns(ppr)
        df_dic = {}
        for i, exp_range in enumerate(expiration_ranges):
            if i in [0, len(expiration_ranges)-1]:
                df_dic[f'{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
                df_dic[f'{int(exp_range)}']['timestamp'] = pd.to_datetime([])
                df_dic[f'{int(exp_range)}'].set_index('timestamp', inplace=True)
            if i in [len(expiration_ranges)-1]:
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
            else:
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
        df_dic.pop(f"{int(np.max(expiration_ranges))}_{int(np.min(expiration_ranges))}")
        return df_dic
    
    @staticmethod
    def oiflowOption_getcolumns(price_percentage_ranges: np.array):
        price_percentage_ranges = np.unique(np.sort(np.concatenate((price_percentage_ranges, -price_percentage_ranges)), axis=0))
        price_percentage_ranges[price_percentage_ranges == -0] = 0
        price_percentage_ranges[price_percentage_ranges == price_percentage_ranges[0]] = 0
        price_percentage_ranges = np.unique(price_percentage_ranges)
        columns = np.concatenate((np.array(['timestamp']), price_percentage_ranges), axis=0)
        return columns
    
    @staticmethod
    def oiflowOption_getranges(price_percentage_ranges: np.array):
        price_percentage_ranges = np.unique(np.sort(np.concatenate((price_percentage_ranges, -price_percentage_ranges)), axis=0))
        price_percentage_ranges[price_percentage_ranges == -0] = 0
        price_percentage_ranges[price_percentage_ranges == price_percentage_ranges[0]] = 0
        price_percentage_ranges = np.unique(price_percentage_ranges)
        return price_percentage_ranges

    @staticmethod
    def oiflowOption_dictionary_helper(dfs, countdowns):
        countdown_ranges = list(dfs.keys())
        countdowns = np.unique(countdowns)
        countdown_ranges_flt = sorted(list(set(([float(item) for sublist in [x.split('_') for x in countdown_ranges] for item in sublist]))))
        mx = max(countdown_ranges_flt)
        mn = min(countdown_ranges_flt)
        l = {key: [] for key in countdown_ranges}
        for index, cf in enumerate(countdown_ranges_flt):
            for v in countdowns.tolist():
                if cf == mn and v <= cf:
                    l[str(int(cf))].append(v)
                if cf != mn and v <= cf and v > countdown_ranges_flt[index-1]:
                    l[f"{str(int(countdown_ranges_flt[index-1]))}_{str(int(cf))}"].append(v)
                if cf == mx and v > cf:
                    l[str(int(cf))].append(v)
            return l
    
    @staticmethod
    def getpcd(center, value):
        if center == 0 and value > center:
            return float(100)
        if value == 0 and value < center:
            return float(9999999999)
        else:
            diff = value - center
            average = (center + value) / 2
            percentage_diff = (diff / average) * 100
            return percentage_diff
        
        
    @staticmethod
    def oiflowOption_choose_range(ppr, value):
        for index, r in enumerate(ppr):
            if index == 0 and value < r:
                return ppr[0]
            if index == len(ppr)-1 and value > r:
                return ppr[-1]
            if value < r and value >= ppr[index-1]:
                return r

class pfflow():
    """ Can be used to process fundings and position data"""
    def __init__ (self,
                 exchange : str,
                 symbol : str,
                 on_message : callable,
                 mode = "production",
                 ):
        self.connection_data = dict()
        self.market_state = dict()
        self.exchange = exchange
        self.symbol = symbol
        self.on_message = on_message
        self.data = InstrumentsData()
        self.mode = mode
        
    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_connection_data(self, connection_data):
       """ passes connectiondata dictionary"""
       self.connection_data = connection_data
       
    def input_data(self, data:str):
        processed_data = self.on_message(data, self.connection_data, self.market_state)
        for symbol in processed_data:
            self.InstrumentsData.update_position(symbol, processed_data.get("symbol"))
            
    def retrive_data_by_instrument(self, instrument):
        self.InstrumentsData.get_position(instrument)

    def retrive_data(self):
        self.data.get_all_positions()