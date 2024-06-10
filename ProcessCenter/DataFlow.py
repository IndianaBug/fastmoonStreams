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
from .StreamDataClasses import OrderBook, MarketTradesLiquidations, OpenInterest, OptionInstrumentsData, InstrumentsData, AggregationDataHolder
import copy

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
        self.df_books = pd.DataFrame()
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

    def pass_stream_data(self, connection_data):
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
        
        # if self.mode == "testing":
        #     print(self.df)     

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
                self.df_books = self.df.copy()
                
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
        filepath = f"{self.folderpath}\\sample_data\\plots\\books_{name}.json"
        try:
            for index, row in self.dfp.iterrows():
                if not all(row == 0):
                    break
            plot_data = {
                'x': [float(x) for x in row.index.tolist()],
                'y': row.values.tolist(),
                'price' : self.find_level(self.books.price),
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
        file_path = f"{self.folderpath}\\sample_data\\dfpandas\\{dftype}\\{dftype}_books_{name}.csv"
        if dftype == "raw":
            self.df.to_csv(file_path, index=False)
        if dftype == "processed":
            self.df_books.to_csv(file_path, index=False)
            
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
        self.stream_data = dict()
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
        self.df_trades_total = pd.DataFrame()
        self.df_trades_delta = pd.DataFrame()
        self.Trades = MarketTradesLiquidations()
        self.buys = dict()
        self.sells = dict()

        self.folderpath = ""
        self.mode = mode

    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.price_level_size) * self.price_level_size
    
    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_stream_data(self, stream_data):
       """ passes connectiondata dictionary"""
       self.stream_data = stream_data

    def pass_savefolder_path(self, folderpath):
       """ passes connectiondata dictionary"""
       self.folderpath = folderpath

    async def input_data(self, data, *args, **kwargs) :
        """ inputs data"""
        try:
            processed_data = await self.on_message(data, self.stream_data, self.market_state)
            await self.Trades.add_trades(processed_data)
        except:
            return
    
    def create_pandas_dataframe(self, type_):
        """
            Common method to process trades and update the DataFrame
            type_ : buys or sells
        """

        data_object = self.Trades.buys if type_ == "buys" else self.Trades.sells
        df = pd.DataFrame(index=list(range(0, self.trades_process_interval)))

        trades = [
            [int(t % self.trades_process_interval), str(self.find_level(trade["price"])), trade["quantity"]]
            for t in data_object for trade in data_object[t]
        ]

        df = pd.DataFrame(trades, columns=['timestamp', 'level', 'quantity'])
        grouped_df = df.groupby(['timestamp', 'level'])['quantity'].sum().reset_index()
        transposed_df = grouped_df.pivot(index='timestamp', columns='level', values='quantity').reset_index()
        transposed_df.columns.name = None
        transposed_df.columns = [str(col) if col != 'timestamp' else 'timestamp' for col in transposed_df.columns]
        transposed_df.set_index('timestamp', inplace=True)
        transposed_df = transposed_df.reindex(range(self.trades_process_interval), fill_value=0).reset_index()
        transposed_df = transposed_df.drop(columns=['timestamp'])
        return transposed_df
    
    @staticmethod
    def merge_suffixes(n):
        """
            The maximum amount of datasets to aggregate is the len(alphabet). 
            Modify this function to get more aggregation possibilities
        """
        alphabet = 'xyzabcdefghijklmnopqrstuvw'
        suffixes = [f'{alphabet[i]}' for i in range(n)]
        return suffixes

    def merge_columns_by_suffix(self, df, obj):
        """ 
            Helper function to merge columns by suffix
            obj : 'sum' or 'delta'
        """
        base_columns = set(col.split('_', 1)[1] for col in df.columns)
        merged_columns = {}

        for base in base_columns:
            matching_columns = [col for col in df.columns if col.endswith(f'_{base}')]
            if obj == 'sum':
                merged_columns[base] = df[matching_columns].sum(axis=1)
            elif obj == 'delta':
                merged_columns[base] = df[matching_columns[0]].fillna(0)
                for col in matching_columns[1:]:
                    merged_columns[base] -= df[col].fillna(0)
            else:
                raise ValueError("The 'obj' parameter must be either 'sum' or 'delta'")
        merged_df = pd.DataFrame(merged_columns)
        return merged_df
    
    def merge_dataframes(self, dataframes : List[pd.DataFrame], obj) -> pd.DataFrame:
        """ 
            Merges multiple books into one dataframe
            books : List[pd.DataFrame] -- list of books to merge
        """
        concatenated_df = pd.concat(dataframes, axis=1, keys=self.merge_suffixes(len(dataframes)))
        concatenated_df.columns = [f'{suffix}_{col}' for suffix, col in concatenated_df.columns]
        concatenated_df = self.merge_columns_by_suffix(concatenated_df, obj)
        sorted_columns = sorted(map(float, [c for c in concatenated_df]))
        concatenated_df = concatenated_df[map(str, sorted_columns)]
        return concatenated_df

    def make_dataframes(self):
        """ generates processed dataframes of trades """
        self.dfbuys = self.create_pandas_dataframe("buys")
        self.dfsells = self.create_pandas_dataframe("sells")
        self.df_trades_total = self.merge_dataframes([self.dfbuys, self.dfsells], "sum")
        self.df_trades_delta = self.merge_dataframes([self.dfbuys, self.dfsells], "delta")


    def dump_df_to_csv(self, dftype):
        """ processed, raw"""
        name = self.stream_data.get("id_ws")
        file_path = f"{self.folderpath}\\sample_data\\dfpandas\\processed\\{dftype}_trades_{self.inst_type}_{name}.csv"
        if dftype == "buys":
            self.dfbuys.to_csv(file_path, index=False)
        if dftype == "sells":
            self.dfsells.to_csv(file_path, index=False)
        if dftype == "total":
            self.df_trades_total.to_csv(file_path, index=False)
        if dftype == "delta":
            self.df_trades_delta.to_csv(file_path, index=False)


    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.trades_process_interval)
                self.make_dataframes()
                if self.mode == "testing":
                    self.dump_df_to_csv("buys")
                    self.dump_df_to_csv("sells")
                    self.dump_df_to_csv("total")
                    self.dump_df_to_csv("delta")

                self.buys = copy.copy(self.Trades.buys)
                self.sells = copy.copy(self.Trades.sells)

                await self.Trades.reset_trades()
                if self.mode == "testing":
                    self.generate_data_for_plot()
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")


    def generate_data_for_plot(self):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:

            name = self.stream_data.get("id_ws")

            for type_, df in {"buys" : self.dfbuys, "sells" : self.dfsells, "total" : self.df_trades_total, "delta" : self.df_trades_delta}.items():

                filepath = f"{self.folderpath}\\sample_data\\plots\\trades_{type_}_{self.inst_type}_{name}.json"

                plot_data = {
                    'x': [float(x) for x in df.columns],
                    'y': df.sum().tolist(),
                    'xlabel': 'Level',
                    'ylabel': 'Amount',
                    'legend': f'Trades sum/delta over {self.trades_process_interval}, {self.exchange}, {type_}, {self.symbol} '
                }

                with open(filepath, 'w') as file:
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
        self.stream_data = dict()
        self.market_state = dict()
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = inst_type
        self.on_message = on_message
        self.price_level_size = float(price_level_size)
        self.oi_process_interval = oi_process_interval
        # helpers
        self.df_ois_delta = pd.DataFrame()
        self.OIS = OpenInterest()
        self.mode = mode
        self.folderpath = ""
        self.last_recieve_time =  {}

        self.ois = {}
        self.oi_changes = {}
        self.data = []

    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.price_level_size) * self.price_level_size
    
    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_stream_data(self, stream_data):
       """ passes connectiondata dictionary"""
       self.stream_data = stream_data

    def pass_savefolder_path(self, folderpath):
       """ passes connectiondata dictionary"""
       self.folderpath = folderpath

    async def input_data(self, data:str):
        """ 
            inputs data into oi dictionary
            on message returns  {symbols : {"oi" : value,}, "timestamp" : "", "receive_time"}
        """
        try:
            oidata = await self.on_message(data, self.market_state, self.stream_data)
            symbol = next(iter(oidata))
            timestamp = oidata.get("timestamp")
            if timestamp > self.last_recieve_time.get(symbol, 0):
                for symbol in oidata:
                    oi = oidata.get(symbol).get("oi")
                    price = oidata.get(symbol).get("price")
                    await self.OIS.add_entry(timestamp, symbol, oi, price)
                    self.last_recieve_time[symbol] = timestamp
        except:
            return

    @staticmethod
    def merge_suffixes(n):
        """
            The maximum amount of datasets to aggregate is the len(alphabet). 
            Modify this function to get more aggregation possibilities
        """
        alphabet = 'xyzabcdefghijklmnopqrstuvw'
        suffixes = [f'_{alphabet[i]}' for i in range(n)]
        return suffixes
    
    def merge_columns_by_suffix(self, df):
        base_columns = set(col.split('_', 1)[1] for col in df.columns)
        merged_columns = {}
        for base in base_columns:
            matching_columns = [col for col in df.columns if col.endswith(f'_{base}')]
            merged_columns[base] = df[matching_columns].sum(axis=1)
        merged_df = pd.DataFrame(merged_columns)
        return merged_df
    
    def merge_dataframes(self, dataframes : List[pd.DataFrame]) -> pd.DataFrame:
        """ 
            Merges multiple books into one dataframe
            books : List[pd.DataFrame] -- list of books to merge
        """
        concatenated_df = pd.concat(dataframes, axis=1, keys=self.merge_suffixes(len(dataframes)))
        concatenated_df.columns = [f'{suffix}_{col}' for suffix, col in concatenated_df.columns]
        concatenated_df = self.merge_columns_by_suffix(concatenated_df)
        sorted_columns = sorted(map(float, [c for c in concatenated_df]))
        concatenated_df = concatenated_df[map(str, sorted_columns)]
        return concatenated_df
    
        
    def make_dataframe(self):
        """ creates dataframe of OIs"""

        processed_oi_by_instrument = {instrument : [] for instrument in self.OIS.data}
                
        for instrument in self.OIS.data:
            for entry in self.OIS.data.get(instrument):
                open_interest = entry.get("open_interest")
                price = entry.get("price")
                timestamp = entry.get("timestamp")
                oi_difference = open_interest - self.ois.get(instrument, open_interest)
                if oi_difference != 0:
                    if timestamp not in self.oi_changes:
                        self.oi_changes[timestamp] = []
                    self.oi_changes[timestamp].append({"oi" : oi_difference,  "price" : price})

                processed_oi_data = [
                    int(timestamp % self.oi_process_interval), 
                    str(self.find_level(price)), 
                    oi_difference
                    ]
                self.ois[instrument] = open_interest
                processed_oi_by_instrument[instrument].append(processed_oi_data)
        
        dataframes = []
        for instrument in processed_oi_by_instrument:
            df = pd.DataFrame(processed_oi_by_instrument.get(instrument), columns=['timestamp', 'level', 'quantity'])
            grouped_df = df.groupby(['timestamp', 'level'])['quantity'].sum().reset_index()
            transposed_df = grouped_df.pivot(index='timestamp', columns='level', values='quantity').reset_index()
            transposed_df.columns.name = None
            transposed_df.columns = [str(col) if col != 'timestamp' else 'timestamp' for col in transposed_df.columns]
            transposed_df.set_index('timestamp', inplace=True)
            transposed_df = transposed_df.reindex(range(self.oi_process_interval), fill_value=0).reset_index()
            transposed_df = transposed_df.drop(columns=['timestamp'])    
            dataframes.append(transposed_df)
        
        if len(dataframes) > 1:
            self.df_ois_delta = self.merge_dataframes(dataframes)
        else:
            self.df_ois_delta = dataframes[0]


    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.oi_process_interval)
                self.make_dataframe()
                if self.mode == "testing":
                    name = self.stream_data.get("id_ws") if "id_ws" in self.stream_data else self.stream_data.get("id_api")
                    self.dfp.to_csv(f"{self.folderpath}\\sample_data\\dfpandas\\processed\\ois_{name}.csv", index=False)

                self.data = copy.copy(self.increases)
                self.increases = []
                await self.ois.reset_data()
                if self.mode == "testing":
                    self.generate_data_for_plot()
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
        
    def generate_data_for_plot(self):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:

            name = self.stream_data.get("id_ws") if "id_ws" in self.stream_data else self.stream_data.get("id_api")

            filepath = f"{self.folderpath}\\sample_data\\plots\\ois_{name}.json"

            plot_data = {
                'x': [float(x) for x in self.dfp.columns],
                'y': self.dfp.sum().tolist(),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'Trades sum over {self.oi_process_interval}, {self.exchange}, {self.symbol} '
            }

            with open(filepath, 'w') as file:
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
        self.stream_data = dict()
        self.market_state = dict()
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = inst_type
        self.on_message = on_message
        self.price_level_size = float(price_level_size)
        self.liquidations_process_interval = liquidations_process_interval
        # helpers
        self.dflongs = pd.DataFrame()
        self.dfshorts = pd.DataFrame()
        self.df_liquidations_total = pd.DataFrame()
        self.df_liquidations_delta = pd.DataFrame()
        self.Liquidations = MarketTradesLiquidations()
        self.shorts = dict()
        self.longs = dict()

        self.folderpath = ""
        self.mode = mode

    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.price_level_size) * self.price_level_size

    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_stream_data(self, stream_data):
       """ passes connectiondata dictionary"""
       self.stream_data = stream_data

    def pass_savefolder_path(self, folderpath):
       """ passes connectiondata dictionary"""
       self.folderpath = folderpath

    def input_data(self, data, *args, **kwargs) :
        """ inputs data"""
        try:
            processed_data = self.on_message(data, self.stream_data, self.market_state)
            self.Liquidations.add_liquidations(processed_data)
        except:
            return
        

    
    @staticmethod
    def merge_suffixes(n):
        """
            The maximum amount of datasets to aggregate is the len(alphabet). 
            Modify this function to get more aggregation possibilities
        """
        alphabet = 'xyzabcdefghijklmnopqrstuvw'
        suffixes = [f'{alphabet[i]}' for i in range(n)]
        return suffixes

    def merge_columns_by_suffix(self, df, obj):
        """ 
            Helper function to merge columns by suffix
            obj : 'sum' or 'delta'
        """
        base_columns = set(col.split('_', 1)[1] for col in df.columns)
        merged_columns = {}

        for base in base_columns:
            matching_columns = [col for col in df.columns if col.endswith(f'_{base}')]
            if obj == 'sum':
                merged_columns[base] = df[matching_columns].sum(axis=1)
            elif obj == 'delta':
                merged_columns[base] = df[matching_columns[0]].fillna(0)
                for col in matching_columns[1:]:
                    merged_columns[base] -= df[col].fillna(0)
            else:
                raise ValueError("The 'obj' parameter must be either 'sum' or 'delta'")
        merged_df = pd.DataFrame(merged_columns)
        return merged_df
    
    def merge_dataframes(self, dataframes : List[pd.DataFrame], obj) -> pd.DataFrame:
        """ 
            Merges multiple books into one dataframe
            books : List[pd.DataFrame] -- list of books to merge
        """
        concatenated_df = pd.concat(dataframes, axis=1, keys=self.merge_suffixes(len(dataframes)))
        concatenated_df.columns = [f'{suffix}_{col}' for suffix, col in concatenated_df.columns]
        concatenated_df = self.merge_columns_by_suffix(concatenated_df, obj)
        sorted_columns = sorted(map(float, [c for c in concatenated_df]))
        concatenated_df = concatenated_df[map(str, sorted_columns)]
        return concatenated_df

    
    def create_pandas_dataframe(self, type_):
        """
            Common method to process liquidations and update the DataFrame
            type_ : longs or shorts
        """
        data_object = self.Liquidations.longs if type_ == "longs" else self.Liquidations.shorts
        df = pd.DataFrame(index=list(range(0, self.liquidations_process_interval)))

        trades = [
            [int(t % self.liquidations_process_interval), str(self.find_level(trade["price"])), trade["quantity"]]
            for t in data_object for trade in data_object[t]
        ]

        df = pd.DataFrame(trades, columns=['timestamp', 'level', 'quantity'])
        grouped_df = df.groupby(['timestamp', 'level'])['quantity'].sum().reset_index()
        transposed_df = grouped_df.pivot(index='timestamp', columns='level', values='quantity').reset_index()
        transposed_df.columns.name = None
        transposed_df.columns = [str(col) if col != 'timestamp' else 'timestamp' for col in transposed_df.columns]
        transposed_df.set_index('timestamp', inplace=True)
        transposed_df = transposed_df.reindex(range(self.liquidations_process_interval), fill_value=0).reset_index()
        transposed_df = transposed_df.drop(columns=['timestamp'])
    
        return transposed_df


    def make_dataframes(self):
        """ generates processed dataframes of trades """
        self.dflongs = self.create_pandas_dataframe("longs")
        self.dfshorts = self.create_pandas_dataframe("shorts")
        self.df_liquidations_total = self.merge_dataframes([self.dflongs, self.dfshorts], "sum")
        self.df_liquidations_delta = self.merge_dataframes([self.dflongs, self.dfshorts], "delta")

    def dump_df_to_csv(self, dftype):
        """ processed, raw"""
        name = self.stream_data.get("id_ws")
        file_path = f"{self.folderpath}\\sample_data\\dfpandas\\processed\\{dftype}_liquidations_{name}.csv"
        if dftype == "longs":
            self.dflongs.to_csv(file_path, index=False)
        if dftype == "shorts":
            self.dfshorts.to_csv(file_path, index=False)
        if dftype == "total":
            self.df_liquidations_total.to_csv(file_path, index=False)

    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.liquidations_process_interval)
                self.make_dataframes()
                if self.mode == "testing":
                    self.dump_df_to_csv("longs")
                    self.dump_df_to_csv("shorts")
                    self.dump_df_to_csv("total")
                    self.dump_df_to_csv("delta")

                self.longs = copy.copy(self.Liquidations.buys)
                self.shorts = copy.copy(self.Liquidations.sells)
                await self.Liquidations.reset_liquidations()
                if self.mode == "testing":
                    self.generate_data_for_plot()
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")


    def generate_data_for_plot(self):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:

            name = self.stream_data.get("id_ws") if self.stream_data.get("id_ws") else self.stream_data.get("id_api")

            for type_, df in {"longs" : self.dflongs, "shorts" : self.dfshorts, "total" : self.df_liquidations_total, "delta" : self.df_liquidations_delta}.items():

                filepath = f"{self.folderpath}\\sample_data\\plots\\liquidations_{type_}_{name}.json"

                plot_data = {
                    'x': [float(x) for x in df.columns],
                    'y': df.sum().tolist(),
                    'xlabel': 'Level',
                    'ylabel': 'Amount',
                    'legend':f'Liquidations ({type_}) over {self.liquidations_process_interval}.s on {self.exchange}, {self.inst_type} ({self.symbol})'
                }

                with open(filepath, 'w') as file:
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
        self.stream_data = dict()
        self.market_state = dict()
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = "option"
        self.on_message = on_message
        self.pranges = pranges
        self.expiry_windows = expiry_windows
        self.option_process_interval = option_process_interval
        self.odata = OptionInstrumentsData()
        self.dfc = pd.DataFrame()
        self.dfp = pd.DataFrame()
        self.mode = mode
        self.index_price_symbol = index_price_symbol
        
    async def input_data(self, data:str):
        try:
        
            processed_data = await self.on_message(data, self.market_state, self.stream_data)
            await self.odata.add_data_bulk(processed_data)
            
        except Exception as e:
            return

    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_stream_data(self, stream_data):
       """ passes connectiondata dictionary"""
       self.stream_data = stream_data

    def pass_savefolder_path(self, folderpath):
       """ passes connectiondata dictionary"""
       self.folderpath = folderpath

    @staticmethod
    def weighted_avg(df, value_column, weight_column):
        return np.average(df[value_column], weights=df[weight_column])

    def process_option_data(self, data:dict):
        """ processes option data"""

        df = pd.DataFrame(data)
        grouped_df = df.groupby(['countdowns', 'strikes']).apply(
            lambda x: pd.Series({
                'weighted_avg_price': self.weighted_avg(x, 'prices', 'ois'),
                'total_open_interest': x['ois'].sum()
            })
                ).reset_index()
        return grouped_df
       
    def create_dataframes(self):
        """ creates puts and calls dataframes """
        call_data, put_data = self.odata.get_summary_by_option_type()
        self.dfp = self.process_option_data(put_data)
        self.dfc = self.process_option_data(call_data)
    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.option_process_interval)
                self.create_dataframes()
                if self.mode == "testing":
                    self.dump_df_to_csv()

        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")

    def dump_df_to_csv(self):
        """ helper function to dump dataframes to csv """
        id_ = self.stream_data.get("id_ws") if "id_ws" in self.stream_data else self.stream_data.get("id_api")
        
        for type_, dff in zip(["Puts", "Calls"], [self.dfp, self.dfc]):
            file_path = f"{self.folderpath}\\sample_data\\dfpandas\\processed\\oioption_{type_}_{id_}.csv"
            dff.to_csv(file_path, index=False)

class pfflow():
    """ Can be used to process fundings and position data"""
    def __init__ (self,
                 exchange : str,
                 symbol : str,
                 on_message : callable,
                 mode = "production",
                 ):
        self.stream_data = dict()
        self.market_state = dict()
        self.exchange = exchange
        self.symbol = symbol
        self.on_message = on_message
        self.data_holder = InstrumentsData()
        self.mode = mode
        self.folderpath = ""
        
    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_stream_data(self, stream_data):
       """ passes connectiondata dictionary"""
       self.stream_data = stream_data

    def pass_savefolder_path(self, folderpath):
       """ passes connectiondata dictionary"""
       self.folderpath = folderpath
       
    async def input_data(self, data:str):

        try:
            processed_data = await self.on_message(data,  self.market_state, self.stream_data)
            for symbol in processed_data:
                if symbol not in ["receive_time", "timestamp"]:
                    data = processed_data.get(symbol)
                    self.data_holder.update_position(symbol, data)
        except Exception as e:
            pass
            
    def retrive_data_by_instrument(self, instrument):
        self.data_holder.get_position(instrument)

    def retrive_data(self):
        self.data_holder.get_all_positions()

class MarketDataFusion:
    """ Mergers for pandas dataframes """
    def __init__(
            self, 
            options_price_ranges: np.array = np.array([0.0, 1.0, 2.0, 5.0, 10.0]), 
            options_index_price_symbols:dict = {"binance" : "BTCUSDT@spot@binance"}, 
            options_expiry_windows: np.array = np.array([0.0, 1.0, 3.0, 7.0]),
            books_spot_aggregation_interval = 60,
            books_future_aggregation_interval = 60,
            trades_spot_aggregation_interval = 60,
            trades_future_aggregation_interval = 60,
            trades_option_aggregation_interval = 60,
            oidelta_future_aggregation_interval = 60,
            liquidations_future_aggregation_interval = 60,
            oi_options_aggregation_interval = 60,
            canceled_books_spot_aggregation_interval = 60,
            canceled_books_future_aggregation_interval = 60,
            mode = "production"
            ):
        """ 
            options_price_ranges : np.array -- aggregates option open_interest data based on price 
            options_index_price_symbols : dict -- if there is an index price for an option, this dict contains the symbol of the index
            options_expiry_windows : np.array  -- aggregates option open_interest data based on expiry
        """
        self.options_price_ranges = options_price_ranges
        self.options_index_price_symbols : dict = options_index_price_symbols
        self.options_expiry_windows : np.array = options_expiry_windows

        self.market_state = dict()

        # Aggregation

        self.aggregation_intervals = {
            "books_spot": books_spot_aggregation_interval,
            "books_future": books_future_aggregation_interval,
            "trades_spot": trades_spot_aggregation_interval,
            "trades_future": trades_future_aggregation_interval,
            "trades_option": trades_option_aggregation_interval,
            "oi_delta_future": oidelta_future_aggregation_interval,
            "liquidations_future": liquidations_future_aggregation_interval,
            "oi_options": oi_options_aggregation_interval,
            "canceled_books_spot": canceled_books_spot_aggregation_interval,
            "canceled_books_future": canceled_books_future_aggregation_interval"
        }
        self.mode = mode

        #dataholders
        self.data_holder = AggregationDataHolder()

    def pass_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def pass_data_holder(self, data_holder):
       """ passes marketstate dictionary"""
       self.data_holder = data_holder

    @staticmethod
    def is_valid_dataframe(df):
        return df is not None and isinstance(df, pd.DataFrame)
    
    @staticmethod
    def merge_suffixes(n):
        """
            The maximum amount of datasets to aggregate is the len(alphabet). 
            Modify this function to get more aggregation possibilities
        """
        alphabet = 'xyzabcdefghijklmnopqrstuvw'
        suffixes = [f'{alphabet[i]}' for i in range(n)]
        return suffixes
    
    def merge_columns_by_suffix(self, df, obj):
        """ 
            Helper function to merge columns by suffix
            obj : 'sum' or 'delta'
        """
        base_columns = set(col.split('_', 1)[1] for col in df.columns)
        merged_columns = {}

        for base in base_columns:
            matching_columns = [col for col in df.columns if col.endswith(f'_{base}')]
            if obj == 'sum':
                merged_columns[base] = df[matching_columns].sum(axis=1)
            elif obj == 'delta':
                merged_columns[base] = df[matching_columns[0]].fillna(0)
                for col in matching_columns[1:]:
                    merged_columns[base] -= df[col].fillna(0)
            else:
                raise ValueError("The 'obj' parameter must be either 'sum' or 'delta'")
        merged_df = pd.DataFrame(merged_columns)
        return merged_df
    
    def merge_dataframes(self, dataframes : List[pd.DataFrame], obj) -> pd.DataFrame:
        """ 
            Merges multiple books into one dataframe
            books : List[pd.DataFrame] -- list of books to merge
        """
        dataframes = [df for df in dataframes if self.is_valid_dataframe(df)]
        concatenated_df = pd.concat(dataframes, axis=1, keys=self.merge_suffixes(len(dataframes)))
        concatenated_df.columns = [f'{suffix}_{col}' for suffix, col in concatenated_df.columns]
        concatenated_df = self.merge_columns_by_suffix(concatenated_df, obj)
        sorted_columns = sorted(map(float, [c for c in concatenated_df]))
        concatenated_df = concatenated_df[map(str, sorted_columns)]
        return concatenated_df

    @staticmethod
    def merge_multiple_dictionaries(dicts : List[dict]) -> dict:
        """ Helper function to merge dictionaries of trades """
        merged_dict = {}
        all_keys = set()
        for d in dicts:
            all_keys.update(d.keys())
        for key in all_keys:
            merged_dict[key] = []
            for d in dicts:
                merged_dict[key].extend(d.get(key, []))
        return merged_dict
    

    async def schedule_books_aggregation(self, aggregation_type:str):
        """ 
            Schedules aggregation of books over certain instrument type 
            aggregation_type : self.aggregation_intervals.keys()
        """
        try:
            interval = self.aggregation_intervals.get(aggregation_type)
            await asyncio.sleep(1)
            while True:

                await asyncio.sleep(interval)

                if aggregation_type not in  ["canceled_books_spot", "canceled_books_future"]:
                    list_of_dataframes = list(self.data_holder.dataframes_to_merge.get(aggregation_type))
                    self.data_holder.merged_dataframes[aggregation_type] = self.merge_dataframes(list_of_dataframes, "sum")
                else:
                    inst_type = aggregation_type.split("_")[-1]
                    books = self.data_holder.merged_dataframes.get(f"books_{inst_type}")
                    trades = self.data_holder.merged_dataframes.get(f"trades_{inst_type}")
                    list_of_dataframes = list(books, trades)
                    self.data_holder.merged_dataframes[aggregation_type] = self.merge_dataframes(list_of_dataframes, "delta")




                    self.books_spot = self.merge_dataframes(marged_data_holder.get("books"))
                    , dict(zip(concatenated_df.columns.tolist(), concatenated_df.iloc[-1].values))

        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")    
    
    async def schedule_aggregation(self, marged_data_holder:List[pd.DataFrame], inst_type:str, objective : str):
        """ 
            Schedules aggregation of a certain objective over certain instrument type 
        """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.books_aggregation_interval)
                df_books, books_dict = self.merge_dataframes(marged_data_holder.get("books"))

        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")

        return dict(zip(self.books.columns.tolist(), self.books.iloc[-1].values))

# Global data 

{

}


# Spot books MAP
# Perp books MAO
# Spot Canceled books MAP
# Spot Reinforced books MAP
# Perp Canceled books MAP
# Perp Reinforced books MAO

# Spot Trades ALL
# Perp/Future/Option Trades ALL
# Spot Trades MAP
# Perp/Future/Option Trades MAP

# Perp Liquidations ALL
# Perp Liquidations MAP

# OI change MAP
# VIOV MAP

# Option OI per instrument

