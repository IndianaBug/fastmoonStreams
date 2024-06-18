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
from .StreamDataClasses import OrderBook, MarketTradesLiquidations, OpenInterest, OptionInstrumentsData, MarketState
import copy
from functools import partial
from collections import defaultdict

pd.set_option('future.no_silent_downcasting', True)

class CommonFlowFunctionalities():
    
    level_size = 20
    stream_data = {}
    inst_type = ""
    
    def find_level(self, price):
        """ locates the bucket to which the price belongs"""
        return np.ceil(price / self.level_size) * self.level_size
    
    def reference_market_state(self, market_state):
       """ passes marketstate dictionary"""
       self.market_state = market_state

    def reference_stream_data(self, stream_data):
       """ passes connectiondata dictionary"""
       self.stream_data = stream_data

    def reference_saving_directory(self, folderpath):
       """ passes connectiondata dictionary"""
       self.folderpath = folderpath
       
    def get_id(self):
        return self.stream_data.get("id_ws") if self.stream_data.get("id_ws") else self.stream_data.get("id_api")
    
    def get_inst_type(self):
        inst_type =  "future" if self.inst_type in ["perpetual", "future"] else self.inst_type
        return inst_type.split("_")[0]

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
        if len(dataframes) > 1:
            concatenated_df = pd.concat(dataframes, axis=1, keys=self.merge_suffixes(len(dataframes)))
            concatenated_df.columns = [f'{suffix}_{col}' for suffix, col in concatenated_df.columns]
            concatenated_df = self.merge_columns_by_suffix(concatenated_df, obj)
            sorted_columns = sorted(map(float, [c for c in concatenated_df]))
            concatenated_df = concatenated_df[map(str, sorted_columns)]
            return concatenated_df
        elif len(dataframes) == 1:
            return dataframes[0]
        else:
            return pd.DataFrame()
    
    @staticmethod
    def split_dataframe_by_weighted_price_ranges(df: pd.DataFrame, price_ranges: List[int]) -> List[pd.DataFrame]:
        """
            Splits a DataFrame into multiple DataFrames based on percentage ranges specified,
            relative to each row's 'weighted_avg_price' in the 'strikes' column.

            :param df: DataFrame to split, which includes 'strikes' and 'weighted_avg_price' columns.
            :param price_ranges: List of percentage ranges up to which the data is split.
            :return: List of DataFrames, each corresponding to the specified ranges.
        """
        split_dfs = {}
        range_limits = price_ranges + [float('inf')] 
        previous_upper = 0
        for upper in range_limits:
            # Create a mask that checks if the strike is within the current range for each row's weighted_avg_price
            mask = df.apply(lambda row: previous_upper <= 100 * (row['strikes'] / row['weighted_avg_price'] - 1) < upper, axis=1)
            split_dfs[upper] = df[mask]
            previous_upper = upper
        return split_dfs

    @staticmethod
    def split_dataframe_by_expiration_ranges(df: pd.DataFrame, expiration_ranges: List[int]) -> Dict[str, float]:
        """
        Splits a DataFrame by expiration ranges specified in 'days_left' and returns a dictionary
        where each key is an expiration range and each value is the total open interest for that range.

        :param df: DataFrame to split, which includes 'days_left' and 'sum_ois' columns.
        :param expiration_ranges: List of expiration ranges in days.
        :return: Dictionary with expiration ranges as keys and total open interest as values.
        """
        ois_totals = {}
        range_limits = expiration_ranges + [float('inf')]  
        previous_upper = 0
        for upper in range_limits:
            mask = (df['days_left'] >= previous_upper) & (df['days_left'] < upper)
            total_ois = df.loc[mask, 'sum_ois'].sum()
            if upper == float('inf'):
                range_label = f"{previous_upper}+ days"
            else:
                range_label = f"{previous_upper}-{upper} days"
            ois_totals[range_label] = total_ois
            previous_upper = upper
        return ois_totals
    
    @staticmethod
    def process_options_dataframe(self, dataframes, price_ranges, expiration_ranges):
        """ abstraction of split_dataframe_by_weighted_price_ranges and split_dataframe_by_expiration_ranges  """
        ois_dictionary = {}
        dfs_by_price_range = self.split_dfs(dataframes, price_ranges)
        for price_range, df in dfs_by_price_range.itmes():
            ois = self.split_dataframe_by_expiration_ranges(df, expiration_ranges)
            ois_dictionary[price_range] = ois
        
    def merge_options_dataframes(self, dataframes : List[pd.DataFrame], obj) -> pd.DataFrame:
        """ 
            Merges multiple books into one dataframe
            books : List[pd.DataFrame] -- list of books to merge
        """
        if len(dataframes) > 1:
            concatenated_df = pd.concat(dataframes, axis=1, keys=[f'DF{i}' for i in range(len(dataframes))])
            concatenated_df.columns = [f'{i}_{col}' for i, col in concatenated_df.columns]
            merged_columns = {'strikes': [], 'days_left': [], 'weighted_avg_price': [], 'sum_ois': []}
            for (strike, days), group in concatenated_df.groupby([col for col in concatenated_df.columns if col.endswith('_strikes') + col for col in concatenated_df.columns if col.endswith('_days_left')]):
                total_ois = group[[col for col in group.columns if col.endswith('_ois')]].sum(axis=1).sum()
                total_weighted_prices = (group[[col for col in group.columns if col.endswith('_prices')]] * group[[col for col in group.columns if col.endswith('_ois')]]).sum().sum()
                weighted_avg_price = total_weighted_prices / total_ois if total_ois != 0 else 0
                merged_columns['strikes'].append(strike)
                merged_columns['days_left'].append(days)
                merged_columns['weighted_avg_price'].append(weighted_avg_price)
                merged_columns['sum_ois'].append(total_ois)
            result_df = pd.DataFrame(merged_columns)
            return result_df
        elif len(dataframes) == 1:
            return dataframes[0]
        else:
            return pd.DataFrame()
        
    @staticmethod
    def merge_ticks_buys_sells(uptick_data, down_tick):
        """ merges tick data of trades and liquidations """
        down_tick = {
                key: [{"amount": -entry["quantity"], "price": entry["price"]} for entry in value]
                for key, value in down_tick.items()
            }
        merged_data = {key: uptick_data.get(key, []) + down_tick.get(key, []) for key in set(uptick_data) | set(down_tick)}
        return merged_data

    @staticmethod
    def merge_ticks(dicts):
        merged_dict = defaultdict(list)

        for d in dicts:
            for key, value in d.items():
                merged_dict[key].extend(value)
        
        return dict(merged_dict)

    def make_cbooks_dictionary(self, dataframes : List[pd.DataFrame]): 
        """ 
            Merges trades and books into one dataframe to extract canceled books
            books : List[pd.DataFrame] -- list books and trades
        """
        trades_depth_history = self.merge_dataframes(dataframes, 'sum')
        canceled_depth = trades_depth_history.diff()
        canceled_depth = canceled_depth.where(canceled_depth < 0, 0).dropna().sum().abs()
        return canceled_depth.to_dict()

    def make_rbooks_dictionary(self, dataframes : List[pd.DataFrame]): 
        """ 
            Merges trades and books into one dataframe to extract canceled books
            books : List[pd.DataFrame] -- list of books to merge
        """
        trades_depth_history = self.merge_dataframes(dataframes, 'sum')
        canceled_depth = trades_depth_history.diff()
        canceled_depth = canceled_depth.where(canceled_depth > 0, 0).dropna().sum()
        return canceled_depth.to_dict()

    def dataframe_to_dictionary(self, dataframe : pd.DataFrame):
        """ aggregated trades by dictionary by timeinterval and returns a dictionary in json format"""
        return dataframe.sum().to_dict()

class depthflow(CommonFlowFunctionalities):
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

        self.stream_data = dict()
        self.market_state = dict()
        self.saving_directory = ""
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
        # Helpers
        self.last_receive_time = 0
        self.running = False
           
    async def input_data_api(self, data:str):
        """ inputs books from api into dataframe"""
        try:
            processed_data = await self.api_on_message(data, self.market_state, self.stream_data)
            await self.books.update_data(processed_data)
        except:
            return

    async def input_data_ws(self, data:str):
        """ inputs books from ws into dataframe"""
        try:
            processed_data = await self.ws_on_message(data, self.market_state, self.stream_data)
            recieve_time = processed_data.get("timestamp")
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
            await asyncio.sleep(self.book_snap_interval)

    async def schedule_processing_dataframe(self):
        """ Generates dataframe of processed books """
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.books_process_interval)

                for col in self.df.columns:
                    self.df[col] = self.df[col].replace(0, pd.NA).ffill()
                    self.df[col] = self.df[col].replace(0, pd.NA).bfill()
                
                id_ = self.get_id()
                inst_type = self.get_inst_type()
                self.market_state.raw_data["dataframes_to_merge"]["depth"][inst_type][id_] = self.df.copy()
                
                if self.mode == "testing":
                    self.dump_df_to_csv()
                
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
        id_ = self.get_id()
        inst_type = self.get_inst_type()
        filepath = f"{self.folderpath}\\sample_data\\plots\\depth_{id_}.json"
        df = self.market_state.raw_data["dataframes_to_merge"]["depth"][inst_type][id_]
        try:
            for index, row in df.iterrows():
                if not all(row == 0):
                    break
            plot_data = {
                'x': [float(x) for x in row.index.tolist()],
                'y': row.values.tolist(),
                'price' : self.find_level(self.books.price),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'BooksSnap, {id_}'
            }
            with open(filepath, 'w') as file:
                json.dump(plot_data, file)
        except Exception as e:
            print(e)
            
    def dump_df_to_csv(self):
        """ processed, raw"""
        id_ = self.get_id()
        file_path = f"{self.folderpath}\\sample_data\\dfpandas\\depth_{id_}.csv"
        self.df.to_csv(file_path, index=False)
       
class tradesflow(CommonFlowFunctionalities):
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
        self.stream_data = MarketState([])
        self.market_state = dict()
        self.Trades = MarketTradesLiquidations()
        
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = inst_type.split("_")[0]
        self.on_message = on_message
        self.price_level_size = float(price_level_size)
        self.trades_process_interval = trades_process_interval
        
        # helpers        
        self.folderpath = ""
        self.mode = mode


    async def input_data(self, data, *args, **kwargs) :
        """ inputs data"""
        try:
            processed_data = await self.on_message(data, self.market_state, self.stream_data)
            await self.Trades.add_trades(processed_data)
        except:
            return
    
    def create_pandas_dataframe(self, type_):
        """
            Common method to process trades and update the DataFrame
            type_ : buys or sells
        """
        data_object = self.Trades.buys if type_ == "buys" else self.Trades.sells

        if data_object != {}:
            trades = [
                [int(t % self.trades_process_interval), str(self.find_level(trade["price"])), trade["quantity"]]
                for t in data_object for trade in data_object[t]
            ]

            df = pd.DataFrame(trades, columns=['timestamp', 'level', 'quantity'])
            grouped_df = df.groupby(['timestamp', 'level']).sum().reset_index()
            transposed_df = grouped_df.pivot(index='timestamp', columns='level', values='quantity').fillna(0)
            all_timestamps = pd.Index(range(self.trades_process_interval))
            transposed_df = transposed_df.reindex(all_timestamps, fill_value=0)
            transposed_df.columns.name = None
            transposed_df.columns = transposed_df.columns.astype(str)
            return transposed_df
        else:
            all_timestamps = pd.Index(range(self.trades_process_interval))
            transposed_df = pd.DataFrame(index=all_timestamps).fillna(0)
            return transposed_df
    
    def make_dataframes(self):
        """ generates processed dataframes of trades """
        id_ = self.get_id()
        inst_type = self.get_inst_type()        
        buys = self.create_pandas_dataframe("buys")
        sells = self.create_pandas_dataframe("sells")
        dataframes = {
            "buys": buys.copy(),
            "sells": sells.copy(),
            "total": self.merge_dataframes([buys, sells], "sum"),
        }
        for type_, df in dataframes.items():                
            self.market_state.raw_data["dataframes_to_merge"]["trades"][inst_type][type_][id_] = df.copy()
    
    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        _id = self.get_id()
        inst_type = self.get_inst_type()
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.trades_process_interval)
                
                self.make_dataframes()
                self.market_state.raw_data["ticks_data_to_merge"]["trades"][inst_type][_id] = self.merge_ticks_buys_sells(self.Trades.buys, self.Trades.sells)
                
                if self.mode == "testing":
                    self.dump_df_to_csv()
                    self.generate_data_for_plot()

                await self.Trades.reset_trades()
                
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")

    def generate_data_for_plot(self):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            inst_type = self.get_inst_type()
            _id = self.get_id()
            for _type in ["total"]:
                df = self.market_state.raw_data["dataframes_to_merge"]["trades"][inst_type][_type][_id]
                filepath = f"{self.folderpath}\\sample_data\\plots\\trades_{_type}_{_id}.json"
                plot_data = {
                    'x': [float(x) for x in df.columns],
                    'y': df.sum().tolist(),
                    'xlabel': 'Level',
                    'ylabel': 'Amount',
                    'legend': f'Trades_{_type}, {_id}'
                }
                with open(filepath, 'w') as file:
                    json.dump(plot_data, file)

        except Exception as e:
            print(e)

    def dump_df_to_csv(self):
        """ processed, raw"""
        _id = self.get_id()
        inst_type = self.get_inst_type()
        for _type in ["total"]:
            file_path = f"{self.folderpath}\\sample_data\\dfpandas\\trades_{_type}_{_id}.csv"
            df = self.market_state.raw_data["dataframes_to_merge"]["trades"][inst_type][_type][_id]
            df.to_csv(file_path, index=False)

class oiflow(CommonFlowFunctionalities):
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
        self.market_state = MarketState([])
        self.ois = OpenInterest()
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = inst_type
        self.on_message = on_message

        self.price_level_size = float(price_level_size)
        self.oi_process_interval = oi_process_interval

        self.folderpath = ""
        self.last_recieve_time =  {}
        self.last_ois_by_instrument = {}


    async def input_data(self, data, *args, **kwargs):
        """ 
            inputs data into oi dictionary
            on message returns  {symbols : {"oi" : value,}, "timestamp" : "", "receive_time"}
        """
        try:
            oidata = await self.on_message(data, self.market_state, self.stream_data)
            for symbol in oidata:
                timestamp = oidata.get(symbol).get("timestamp")
                if timestamp > self.last_recieve_time.get(symbol, 0):
                    d = {"oi" : oidata.get(symbol).get("oi"), "price" : oidata.get(symbol).get("price"), "timestamp" :  oidata.get(symbol).get("timestamp")}
                    await self.ois.add_entry(d)
                    self.last_recieve_time[symbol] = timestamp
        except:
            return
        
    def make_dataframe_maps(self):
        """ creates dataframe of OIs"""
        
        ticks_oi_delta = {timestamp : [] for timestamp in self.ois.get_uniquetimestamp()}

        for instrument in self.ois.data:
            for entry in self.ois.data.get(instrument):
                open_interest = entry.get("oi")
                price = entry.get("price")
                timestamp = entry.get("timestamp")
                oi_difference = open_interest - self.last_ois_by_instrument.get(instrument, open_interest)
                if oi_difference != 0:
                    ticks_oi_delta[timestamp].append({"oi" : oi_difference,  "price" : price})

        oi_deltas = [
                    [int(t % self.oi_process_interval), str(self.find_level(oi_tick["price"])), oi_tick["oi"]]
                    for t in ticks_oi_delta for oi_tick in ticks_oi_delta[t]
            ]

        df = pd.DataFrame(oi_deltas, columns=['timestamp', 'level', 'quantity'])
        grouped_df = df.groupby(['timestamp', 'level']).sum().reset_index()
        transposed_df = grouped_df.pivot(index='timestamp', columns='level', values='quantity').fillna(0)
        all_timestamps = pd.Index(range(self.trades_process_interval))
        transposed_df = transposed_df.reindex(all_timestamps, fill_value=0)
        transposed_df.columns.name = None
        transposed_df.columns = transposed_df.columns.astype(str)
        return ticks_oi_delta, transposed_df


    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            id_ = self.get_id()
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.oi_process_interval)
                
                ticks_oi_delta, oideltas = self.make_dataframe_maps()
                self.market_state.raw_data["dataframes_to_merge"]["oi_deltas"][id_] = oideltas
                self.market_state.raw_data["ticks_data_to_merge"]["oi_deltas"][id_] = ticks_oi_delta
                
                if self.mode == "testing":
                    filepath = f"{self.folderpath}\\sample_data\\plots\\oi_delta_{id_}.csv"
                    oideltas.to_csv()
                    self.generate_data_for_plot(filepath, index=False)
                
                await self.ois.reset_data()
                
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
        
    def generate_data_for_plot(self):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:

            id_ = self.get_id()            
            df = self.market_state.raw_data["dataframes_to_merge"]["oi_delta"][id_]
            filepath = f"{self.folderpath}\\sample_data\\plots\\oi_delta_{id_}.json"
            plot_data = {
                'x': [float(x) for x in df.columns],
                'y': df.sum().tolist(),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'Changes of OIs {id_}'
            }

            with open(filepath, 'w') as file:
                json.dump(plot_data, file)

        except Exception as e:
            print(e)

class liqflow(CommonFlowFunctionalities):
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
        self.stream_data = MarketState([])
        self.market_state = dict()
        self.Liquidations = MarketTradesLiquidations()

        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = inst_type
        self.on_message = on_message
        self.price_level_size = float(price_level_size)
        self.liquidations_process_interval = liquidations_process_interval

        self.folderpath = ""
        self.mode = mode


    async def input_data(self, data, *args, **kwargs) :
        """ inputs data"""
        try:
            processed_data = await self.on_message(data, self.market_state, self.stream_data)
            await self.Liquidations.add_liquidations(processed_data)
        except:
            return
    
    
    def create_pandas_dataframe(self, type_):
        """
            Common method to process liquidations and update the DataFrame
            type_ : longs or shorts
        """
        data_object = self.Liquidations.longs if type_ == "longs" else self.Liquidations.shorts
        df = pd.DataFrame(index=list(range(0, self.liquidations_process_interval)))
        liquidations = [
            [int(t % self.liquidations_process_interval), str(self.find_level(trade["price"])), trade["quantity"]]
            for t in data_object for trade in data_object[t]
        ]
        df = pd.DataFrame(liquidations, columns=['timestamp', 'level', 'quantity'])
        grouped_df = df.groupby(['timestamp', 'level']).sum().reset_index()
        transposed_df = grouped_df.pivot(index='timestamp', columns='level', values='quantity').fillna(0)
        all_timestamps = pd.Index(range(self.liquidations_process_interval))
        transposed_df = transposed_df.reindex(all_timestamps, fill_value=0)
        transposed_df.columns.name = None
        transposed_df.columns = transposed_df.columns.astype(str)
        return transposed_df


    def make_dataframes(self):
        """ generates processed dataframes of liquidations """

        id_ = self.get_id()
        inst_type = self.get_inst_type()        
        longs = self.create_pandas_dataframe("longs")
        shorts = self.create_pandas_dataframe("shorts")
        dataframes = {
            "longs": longs,
            "shorts": shorts,
            "total": self.merge_dataframes([longs, shorts], "sum"),
            "delta": self.merge_dataframes([longs, shorts], "delta")
        }
        for type_, df in dataframes.items():                
            self.market_state.raw_data["dataframes_to_merge"]["liquidations"][type_][id_] = df.copy()


    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        _id = self.get_id()
        inst_type = self.get_inst_type()
        try:
            await asyncio.sleep(1)
            while True:
                await asyncio.sleep(self.liquidations_process_interval)
                
                self.make_dataframes()
                self.market_state.raw_data["ticks_data_to_merge"]["liquidations"][_id] = self.merge_ticks_buys_sells(self.Liquidations.buys, self.Liquidations.sells)
                
                if self.mode == "testing":
                    self.dump_df_to_csv()
                    self.generate_data_for_plot()

                await self.Liquidations.reset_trades()
                
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
        

    def dump_df_to_csv(self):
        """ processed, raw"""
        _id = self.get_id()
        inst_type = self.get_inst_type()
        for _type in ["longs", "shorts", "total", "delta"]:
            file_path = f"{self.folderpath}\\sample_data\\dfpandas\\liquidations_{_type}_{_id}.csv"
            df = self.market_state.raw_data["dataframes_to_merge"]["liquidations"][_type][_id]
            df.to_csv(file_path, index=False)


    def generate_data_for_plot(self):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            inst_type = self.get_inst_type()
            _id = self.get_id()
            for _type in ["longs", "shorts", "total", "delta"]:
                df = self.market_state.raw_data["dataframes_to_merge"]["liquidations"][_type][_id]
                filepath = f"{self.folderpath}\\sample_data\\plots\\liquidations_{_type}_{_id}.json"
                plot_data = {
                    'x': [float(x) for x in df.columns],
                    'y': df.sum().tolist(),
                    'xlabel': 'Level',
                    'ylabel': 'Amount',
                    'legend': f'Liquidations_{_type}, {_id}'
                }
                with open(filepath, 'w') as file:
                    json.dump(plot_data, file)

        except Exception as e:
            print(e)

class ooiflow(CommonFlowFunctionalities):

    def __init__(self,
                 exchange : str,
                 symbol : str,
                 on_message : callable,
                 option_process_interval : int = 10,
                 mode = "production",
                 *args,
                 **kwargs,
                 ):
        """ Cool init method"""
        self.market_state = MarketState([])
        self.stream_data = list()
        self.exchange = exchange
        self.symbol = symbol
        self.inst_type = "option"
        self.on_message = on_message
        self.option_data = OptionInstrumentsData()
        self.option_process_interval = option_process_interval
        self.mode = mode
                
    async def input_data(self, data:str):
        try:
        
            processed_data = await self.on_message(data, self.market_state, self.stream_data)
            await self.option_data.add_data_bulk(processed_data)
            
        except Exception as e:
            return

    @staticmethod
    def weighted_avg(df, value_column, weight_column):
        return np.average(df[value_column], weights=df[weight_column])

    def process_option_data(self, data:dict):
        """ processes option data"""

        df = pd.DataFrame(data)
        grouped_df = df.groupby(['days_left', 'strikes']).apply(
            lambda x: pd.Series({
                'prices': self.weighted_avg(x, 'prices', 'ois'),
                'ois': x['ois'].sum()
            })
                ).reset_index()
        return grouped_df
       
    def create_dataframes(self):
        """ creates puts and calls dataframes """
        call_data, put_data = self.odata.get_summary_by_option_type()
        id_ = self.get_id()
        self.market_state.raw_data["dataframes_to_merge"]["oi_option"]["puts"][id_] = self.process_option_data(put_data)
        self.market_state.raw_data["dataframes_to_merge"]["oi_option"]["calls"][id_] = self.process_option_data(call_data)        
    
    async def schedule_processing_dataframe(self):
        """ Processes dataframes in a while lloop """
        try:
            await asyncio.sleep(1)
            while True:
                
                await asyncio.sleep(self.option_process_interval)
                self.create_dataframes()
                if self.mode == "testing":
                    self.dump_df_to_csv()
                    self.generate_data_for_plot()

        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")

    def dump_df_to_csv(self):
        """ helper function to dump dataframes to csv """
        
        id_ = self.get_id()
        dfp = self.market_state.raw_data["dataframes_to_merge"]["oi_option"]["puts"][id_]
        dfc = self.market_state.raw_data["dataframes_to_merge"]["oi_option"]["calls"][id_]
        
        for type_, dff in zip(["Puts", "Calls"], [dfp, dfc]):
            file_path = f"{self.folderpath}\\sample_data\\dfpandas\\oi_option_{type_}_{id_}.csv"
            dff.to_csv(file_path, index=False)
            
    def generate_data_for_plot(self):
        """ generates plot of option OIS at a random timestamp to verify any discrepancies, good for testing """
        try:
            
            dfp = self.market_state.raw_data["dataframes_to_merge"]["oi_option"]["puts"][id_]
            dfc = self.market_state.raw_data["dataframes_to_merge"]["oi_option"]["calls"][id_]

            id_ = self.get_id()
            data_holder_key = f"oi_option"
            df_dict = {"put" : dfp, "call" : dfc}
            
            for option_type, df in df_dict.items():
                
                filepath = f"{self.folderpath}\\sample_data\\plots\\oi_option_{option_type}_{id_}.json"
                grouped = df.groupby('strike').sum()
                
                plot_data = {
                    'x': grouped["strike"].tolist(),
                    'y': grouped["total_open_interest"].tolist(),
                    'xlabel': 'Strike',
                    'ylabel': 'Open Interest',
                    'legend':f'Option OI, {id_}'
                }
                with open(filepath, 'w') as file:
                    json.dump(plot_data, file)

        except Exception as e:
            print(e)

class MarketDataFusion(CommonFlowFunctionalities):
    """ Mergers for pandas dataframes """
    def __init__(
            self, 
            options_price_ranges = [0.0, 1.0, 2.0, 5.0, 10.0], 
            options_index_price_symbols:dict = {"binance" : "BTCUSDT@spot@binance"}, 
            options_expiry_windows = [0.0, 1.0, 3.0, 7.0],
            depth_spot_aggregation_interval = None,
            depth_future_aggregation_interval = None,
            trades_spot_aggregation_interval = None,
            trades_future_aggregation_interval = None,
            trades_option_aggregation_interval = None,
            oi_deltas_aggregation_interval = None,
            liquidations_future_aggregation_interval = None,
            oi_options_aggregation_interval = None,
            canceled_books_spot_aggregation_interval = None,
            canceled_books_future_aggregation_interval = None,
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
        self.folderpath = ""

        self.aggregation_intervals = {
            "depth_spot": depth_spot_aggregation_interval,
            "depth_future": depth_future_aggregation_interval,
            "trades_spot": trades_spot_aggregation_interval,
            "trades_future": trades_future_aggregation_interval,
            "trades_option": trades_option_aggregation_interval,
            "oi_deltas": oi_deltas_aggregation_interval,
            "liquidations_future": liquidations_future_aggregation_interval,
            "oi_options": oi_options_aggregation_interval,
            "cdepth_spot": canceled_books_spot_aggregation_interval,
            "cdepth_future": canceled_books_future_aggregation_interval,
            "rdepth_spot": canceled_books_spot_aggregation_interval,
            "rdepth_future": canceled_books_future_aggregation_interval,
        }
        
        self.mode = mode

    async def schedule_aggregation_depth(self, aggregation_type, aggregation_lag:int=1, *args, **kwargs):
        """ helper for aggregation """
        inst_type = aggregation_type.split("_")[-1]
        try:
            interval = self.aggregation_intervals.get(aggregation_type)
            await asyncio.sleep(aggregation_lag)
            while True:
                await asyncio.sleep(interval)
                dataframes = list(self.market_state.raw_data.get("dataframes_to_merge").get("depth").get(inst_type).values())
                mergeddf = self.merge_dataframes(dataframes, "sum")
                self.market_state.raw_data["merged_dataframes"]["depth"][inst_type] = mergeddf

                depth_dict = self.dataframe_to_dictionary(mergeddf)
                self.market_state.staging_data["maps"][f"depth_{inst_type}"] = depth_dict

                if self.mode == "testing":
                    self.dump_df_to_csv(aggregation_type, mergeddf)
                    self.generate_depth_data_for_plot(inst_type, mergeddf)
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")

    async def schedule_aggregation_trades(self, aggregation_type, aggregation_lag:int=1, *args, **kwargs):
        """ helper for aggregation """
        inst_type = aggregation_type.split("_")[-1]
        try:
            interval = self.aggregation_intervals.get(aggregation_type)
            await asyncio.sleep(aggregation_lag)
            while True:
                await asyncio.sleep(interval)
                for trade_type in ["buys", "sells", "total"]:
                    dataframes = list(self.market_state.raw_data.get("dataframes_to_merge").get("trades").get(inst_type).get(trade_type).values())
                    mergeddf = self.merge_dataframes(dataframes, "sum")
                    self.market_state.input_merged_dataframe(metric="trades", inst_type=inst_type, metric_subtype=trade_type, df=mergeddf)    
                    if self.mode == "testing" and trade_type == "total":
                        self.dump_df_to_csv(aggregation_type, mergeddf)
                        self.generate_trades_data_for_plot(inst_type, trade_type, mergeddf)

                # Input maps and ticks into staging data
                buys_dict = self.dataframe_to_dictionary(self.market_state.raw_data["merged_dataframes"]["trades"][inst_type]["buys"])
                sells_dict = self.dataframe_to_dictionary(self.market_state.raw_data["merged_dataframes"]["trades"][inst_type]["sells"])
                merged_ticks = self.merge_ticks(list(self.market_state.raw_data.get("ticks_data_to_merge").get("trades").get(inst_type).values()))
                self.market_state.staging_data["ticks"][f"trades_{inst_type}"] = merged_ticks
                self.market_state.staging_data["maps"][f"buys_{inst_type}"] = buys_dict
                self.market_state.staging_data["maps"][f"sells_{inst_type}"] = sells_dict
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")  

    async def schedule_aggregation_oi_deltas(self, aggregation_lag:int=1, *args, **kwargs):
        """ helper for aggregation """
        try:
            interval = self.aggregation_intervals.get(f"oi_deltas")
            await asyncio.sleep(aggregation_lag)
            while True:
                await asyncio.sleep(interval)
                dataframes = list(self.market_state.raw_data.get("dataframes_to_merge").get("oi_deltas").values())
                mergeddf = self.merge_dataframes(dataframes, "sum")
                oi_deltas_dictionary = self.dataframe_to_dictionary(mergeddf)
                self.market_state.staging_data["maps"][f"oi_deltas"] = oi_deltas_dictionary
                
                merged_ticks = self.merge_ticks(list(self.market_state.raw_data.get("ticks_data_to_merge").get("oi_deltas").values()))
                self.market_state.staging_data["ticks"][f"oi_deltas"] = merged_ticks
                
                if self.mode == "testing":
                    self.dump_df_to_csv("oi_deltas", mergeddf)
                    self.generate_oi_data_for_plot(mergeddf)
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}") 

    async def schedule_aggregation_liquidations(self, aggregation_lag:int=1, *args, **kwargs):
        """ helper for aggregation of liquidations """
        inst_type = "future"
        try:
            interval = self.aggregation_intervals.get("liquidations_future")
            await asyncio.sleep(aggregation_lag)
            while True:
                await asyncio.sleep(interval)
                for liq_type in ["longs", "shorts", "total", "delta"]:
                    
                    dataframes = list(self.market_state.raw_data.get("dataframes_to_merge").get("liquidations").get(liq_type).values())
                    
                    mergeddf = self.merge_dataframes(dataframes, "sum")
                    buys_dict = self.dataframe_to_dictionary(self.market_state["merged_dataframes"]["liquidations"]["longs"])
                    sells_dict = self.dataframe_to_dictionary(self.market_state["merged_dataframes"]["liquidations"]["shorts"])
                    self.market_state.staging_data["maps"][f"longs"] = buys_dict
                    self.market_state.staging_data["maps"][f"shorts"] = sells_dict
                    
                    merged_ticks = self.merge_ticks(list(self.market_state.raw_data.get("ticks_data_to_merge").get("liquidations").values()))
                    self.market_state.staging_data["ticks"][f"liquidations"] = merged_ticks
                    
                    if self.mode == "testing":
                        self.dump_df_to_csv("liquidations_future", mergeddf)
                        self.generate_trades_data_for_plot(inst_type, liq_type, mergeddf)
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")  

    async def schedule_aggregation_cdepth_rdepth(self, aggregation_type, aggregation_lag:int=1, *args, **kwargs):
        """ helper for aggregation liiquations """
        inst_type = aggregation_type.split("_")[-1]
        depth_type = aggregation_type.split("_")[0]
        try:
            interval = self.aggregation_intervals.get(aggregation_type)
            await asyncio.sleep(aggregation_lag)
            while True:
                
                await asyncio.sleep(interval)
                
                depth = self.market_state.raw_data.get("merged_dataframes").get("trades").get(inst_type)
                trades = self.market_state.raw_data.get("merged_dataframes").get("trades").get(inst_type).get("total")
                
                if "cdepth" in aggregation_type:
                    depth_dict = self.make_cbooks_dictionary([depth, trades])
                    self.market_state.staging_data["maps"][aggregation_type] = depth_dict
                elif "rdepth" in aggregation_type:
                    depth_dict = self.make_cbooks_dictionary([depth, trades])
                    self.market_state.staging_data["maps"][aggregation_type] = depth_dict

                if self.mode == "testing":
                    self.generate_crdepth_data_for_plot(inst_type, depth_type, inst_type)
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}") 

    async def schedule_aggregation_oioption(self, aggregation_lag=1, *args, **kwargs): 
        try:
            interval = self.aggregation_intervals.get(f"oi_options")
            await asyncio.sleep(aggregation_lag)
            while True:
                
                await asyncio.sleep(interval)
                
                calls_to_merge = list(self.market_state.raw_data.get("dataframes_to_merge").get("oi_options").get("calls").values())
                puts_to_merge = list(self.market_state.raw_data.get("dataframes_to_merge").get("oi_options").get("puts").values())

                merged_calls = self.merge_options_dataframes(calls_to_merge)
                merged_puts = self.merge_options_dataframes(puts_to_merge)
                
                oi_dictionary = {
                    "calls" : self.process_options_dataframe(merged_calls), 
                    "puts" : self.process_options_dataframe(merged_puts),
                    }
                
                self.merket_state.staging_data["oi_option"] = oi_dictionary



                if self.mode == "testing":
                    self.dump_df_to_csv("oi_option_calls", merged_calls)
                    self.dump_df_to_csv("oi_option_puts", merged_puts)
                    self.generate_oioption_data_for_plot(oi_dictionary)
        except asyncio.CancelledError:
            print("Task was cancelled")
            raise
        except Exception as e:
            print(f"An error occurred: {e}") 

    def dump_df_to_csv(self, file_name:str, df:pd.DataFrame):
        """ dumps data """
        file_path = f"{self.folderpath}\\sample_data\\dfpandas\\{file_name}.csv"
        df.to_csv(file_path, index=False)

    def generate_crdepth_data_for_plot(self, data_dict, depth_type, inst_type):
        """ generates plot of cdepth, rdepth at a random timestamp to verify any discrepancies, good for testing """
        try:
            filepath = f"{self.folderpath}\\sample_data\\plots\\{depth_type}_{inst_type}.json"
            word = "Canceled Depth" if depth_type == "cdepth" else "Reinforced Depth"
            title = f'{word} of {inst_type}'
            plot_data = {
                'x': [float(x) for x in data_dict.keys()],
                'y': [float(x) for x in data_dict.values()],
                'price' : self.find_level(self.market_state.staging_data.get("global").get(f"price_{inst_type}", 70000)),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': title
            }
            with open(filepath, 'w') as file:
                json.dump(plot_data, file)
        except Exception as e:
            print(e)
            
    def generate_depth_data_for_plot(self, subtype, df):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """

        filepath = f"{self.folderpath}\\sample_data\\plots\\merged_depth_{subtype}.json"
        try:
            for index, row in df.iterrows():
                if not all(row == 0):
                    break
            plot_data = {
                'x': [float(x) for x in row.index.tolist()],
                'y': row.values.tolist(),
                'price' : self.find_level(self.market_state.staging_data.get("global").get(f"price_{subtype}", 70000)),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'Merged Depth Snap, {subtype}'
            }
            with open(filepath, 'w') as file:
                json.dump(plot_data, file)
        except Exception as e:
            print(e)

    def generate_trades_data_for_plot(self, inst_type, trade_type, df):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            filepath = f"{self.folderpath}\\sample_data\\plots\\merged_trades_{inst_type}_{trade_type}.json"
            plot_data = {
                'x': [float(x) for x in df.columns],
                'y': df.sum().tolist(),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'merged_trades_{inst_type}_{trade_type}'
            }
            with open(filepath, 'w') as file:
                json.dump(plot_data, file)

        except Exception as e:
            print(e)

    def generate_oi_data_for_plot(self, df):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            filepath = f"{self.folderpath}\\sample_data\\plots\\merged_oideltas.json"
            plot_data = {
                'x': [float(x) for x in df.columns],
                'y': df.sum().tolist(),
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'merged_oideltas'
            }
            with open(filepath, 'w') as file:
                json.dump(plot_data, file)

        except Exception as e:
            print(e)

    def generate_oioption_data_for_plot(self, dict_ois):
        """ generates plot of books at a random timestamp to verify any discrepancies, good for testing """
        try:
            filepath = f"{self.folderpath}\\sample_data\\plots\\merged_oideltas.json"
            plot_data = {
                'data' : dict_ois,
                'xlabel': 'Level',
                'ylabel': 'Amount',
                'legend': f'merged_option_oi'
            }
            with open(filepath, 'w') as file:
                json.dump(plot_data, file)

        except Exception as e:
            print(e)