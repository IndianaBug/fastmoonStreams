import json
from datetime import datetime
import time
import numpy as np
import pandas as pd
from utilis import *

class sProcessBooks():
    """
        Important notes: 
            Keep current price and current timestamp consistent among all of the sProcessors
            If the book is above price_level_ceiling from the current price, it will be deleted for computational efficiency.
            It would be wise to assume that over 60 secods, very wide books are unimportant 
        
        Descrtiption: 
            Processes second streams of limit orders and market orders
            level_range : price range of buckets to aggregate books
            price_level_ceiling : % ceiling of price levels to ommit, default 5%
    """
    def __init__(self, exchange, symbol, start_price, level_range, price_level_ceiling=5):
        # Identification
        self.exchange = exchange
        self.symbol = symbol
        # levels
        self.level_range = level_range
        self.price_level_ceiling = price_level_ceiling
        self.level_ranges = get_level_ranges(start_price, level_range, price_level_ceiling)
        self.B = {"timestamp": 1, "current_price": float(start_price), "bids" : {}, "asks" : {}}
        # Raw data processors
        self.dfs_books = create_data_frame('sec', self.level_ranges)
    
    def update_current_price(self, price):
        self.B['current_price'] = price
    
    def update_books(self, total_books, bids_name, asks_name, t_name):
        """
            bids_name, asks_name, t_name : Different jsons have different name for bids and asks and timestamps
            t__name as if time.time()
        """
        self.update_books_helper(total_books[bids_name], 'bids')
        self.update_books_helper(total_books[asks_name], 'asks')
        self.B['timestamp'] = total_books[t_name]
        self.B['current_price'] = (max([float(x[0]) for x in total_books[bids_name]]) + min([float(x[0]) for x in total_books[asks_name]])) / 2

    def update_books_helper(self, books, side):
        """
          side: bids, asks
        """
        # Omit books above 5% from the current price
        for book in books:
            p = float(book[0])
            cp = float(self.B['current_price'])
            if percentage_difference(p, cp) > self.price_level_ceiling:
                continue
            if book[1] == "0" or book[1] == 0:
                del self.B[side][book[0]]
            else:
                self.B[side][book[0]] = book[1]

    def dfs_input_books(self):
        """
            Note: Try to call it every second
            Inputs bids and asks into dfs
        """
        # Raw data
        current_second = int(self.B['timestamp'] % 60)  
        current_price = (np.max([float(x) for x in self.B['bids'].keys()]) + np.min([float(x) for x in self.B['asks'].keys()])) / 2
        raw_books_quatities = np.array([float(x) for x in self.B['bids'].values()] + [float(x) for x in self.B['asks'].values()])
        raw_books_levels = np.array([float(x) for x in self.B['bids'].keys()] + [float(x) for x in self.B['asks'].keys()])
        # 
        self.dfs_books['price'] = current_price
        # New books levels
        start = np.floor(np.min(raw_books_levels) / self.level_range ) * self.level_range 
        end = np.ceil(np.max(raw_books_levels) / self.level_range ) * self.level_range 
        books_levels = np.arange(start, end+1, self.level_range)
        # Are there new levels currently not in dataframe?
        new_levels = np.setdiff1d(books_levels, self.level_ranges)
        # Indices and grouped values
        grouped_values = np.bincount(np.digitize(raw_books_levels, bins=books_levels), weights=raw_books_quatities)
        if new_levels.size == 0:
            self.dfs_books.loc[current_second, books_levels] = grouped_values
            self.dfs_books.ffill(inplace=True)
        else:
            # Create newcolumns pandas dataframe
            new_columns_data = pd.DataFrame({new_level: [float(0)] * len(self.dfs_books) for new_level in new_levels})
            self.dfs_books = pd.concat([self.dfs_books, new_columns_data], axis=1)
            # Input new values
            self.dfs_books.loc[current_second, books_levels] = grouped_values
            self.dfs_books.ffill(inplace=True)
            # Remove columns if those are not within 5% range
            columns_to_drop = filter_ranges(self.level_ranges, self.price_level_ceiling)
            self.dfs_books.drop(columns=columns_to_drop, inplace=True)
            self.level_ranges = np.setdiff1d(np.concatenate((self.level_ranges, new_levels)), columns_to_drop)

class sProcessTrades():
    """
        Important notes: 
            Keep current price and current timestamp consistent among all of the sProcessors
            If the book is above price_level_ceiling from the current price, it will be deleted for computational efficiency.
            It would be wise to assume that over 60 secods, very wide books are unimportant 
        
        Descrtiption: 
            Processes second streams of limit orders and market orders
            level_range : price range of buckets to aggregate books
            price_level_ceiling : % ceiling of price levels to ommit, default 5%
    """

    def __init__(self, exchange, symbol, start_price, level_range, price_level_ceiling=5):
        # Identification
        self.exchange = exchange
        self.symbol = symbol
        # levels
        self.level_range = level_range
        self.price_level_ceiling = price_level_ceiling
        self.level_ranges = np.array([])
        # Raw data processors
        self.price = start_price
        self.dfs_trades = pd.DataFrame(index=list(range(0, 60, 1)) , columns=np.array(columns = ['price']))
        self.snapshot  = None

    def dfs_input_trades(self, current_price, trade, t_name, p_name, q_name):
        """ 
            Note: For consistency use a price from a single instrument, rather than separate. This is indeed a good approximation
                  As well, keep the same timestamps

            t_name: timestamp name in the dictionary
            p_name: price name in the dictionary
            q_name: quantity name in the dictionary

            Inputs price, volume(amount) into dfs_trades frame
        """
        current_second = int(trade[t_name]% 60)  
        # current_price = float(trade[p_name]) 
        amount = float(trade['q'])
        level = np.floor_divide(current_price, self.level_range) * self.level_range
        # Not needed, just incase
        if (level in self.level_ranges) == False:
            new_column = pd.DataFrame({level: [float(0)] * len(self.dfs_trades)})
            self.dfs_trades = pd.concat([self.dfs_trades, new_column], axis=1)
            self.dfs_trades[current_second, level] += amount
            columns_to_drop = filter_ranges(self.level_ranges, self.price_level_ceiling)
            self.dfs_trades.drop(columns=columns_to_drop, inplace=True)
            self.level_ranges = np.setdiff1d(np.concatenate((self.level_ranges, np.array(level))), columns_to_drop)
        else:
            self.dfs_trades[current_second, level] += amount
        if current_second == 59:
            self.snapshot = self.dfs_trades.copy()
            self.dfs_trades[:] = 0


