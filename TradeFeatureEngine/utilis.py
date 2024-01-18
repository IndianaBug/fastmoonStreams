import json
from datetime import datetime
import time
import numpy as np
import pandas as pd
import math

def convert_timestamp(timestamp):
    return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')

def get_current_hour_of_year():
    now = datetime.now()
    hour_of_year = (now - datetime(now.year, 1, 1)).total_seconds() / 3600
    return int(hour_of_year)

def get_current_hour_of_week():
    now = datetime.now()
    current_hour_of_week = (now.weekday() * 24) + now.hour
    return current_hour_of_week

def get_current_secod():
    datetime_str  = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S UTC')
    return parsed_datetime.second 

def calculate_percentage_difference(old_value, new_value):
    try:
        percentage_difference = ((new_value - old_value) / abs(old_value)) * 100
        return percentage_difference
    except ZeroDivisionError:
        return float('inf')

def get_bucket_list(current_price, bucket_range, n_buckets):
    """
        For initialization of buckets
    """
    rounded_current_price = round(current_price / 20) * 20
    asbp = rounded_current_price + (bucket_range * n_buckets) + 1
    bsbp = rounded_current_price - (bucket_range * n_buckets) - 1
    bid_buckets = [i for i in range(rounded_current_price, bsbp, -bucket_range)]
    bid_buckets = [[b, a] for a, b in zip(bid_buckets, bid_buckets[1:])]
    ask_buckets = [i for i in range(rounded_current_price, asbp, bucket_range)]
    ask_buckets = [[a, b] for a, b in zip(ask_buckets, ask_buckets[1:])]
    full = sorted(bid_buckets + ask_buckets)
    return full


def create_data_frame(dftype, column_list):                                
    if dftype == 'sec':      
        r = list(range(0, 60, 1))     # Seconds in a minute
    if dftype == 'min':
        r = list(range(0, 10080, 1))  # Minutes in a week
    if dftype == 'h':
        r = list(range(0, 365*24, 1)) # Since the next leap year is 2100
    columns = ['price', 'volume'] + [float(x) for x in column_list.tolist()]
    df = pd.DataFrame(index=r, columns=np.array(columns))
    df.fillna(float(0), inplace=True)
    return df

def filter_ranges(data_array: np.array, percentage_range):
    lower_bound = np.ceil(np.percentile(data_array, (100 - percentage_range) / 2))
    upper_bound = np.floor(np.percentile(data_array, 100 - (100 - percentage_range) / 2))
    f = (data_array < lower_bound) | (data_array > upper_bound)
    filtered_array = np.array(data_array)[~f]
    return filtered_array

def find_level(range_array, value_to_find):
    if value_to_find < np.min(range_array):
        bin_index = None
    if value_to_find >= np.max(range_array):
        bin_index = None
    else:
        bin_index = np.digitize(value_to_find, bins=range_array, right=True)
    return range_array[bin_index]


def percentage_difference(value1, value2):
    if value1 == 0 or value2 == 0:
        return 0
    bigger_value = value1 if value1 > value2 else value2
    smaller_value = value1 if value1 < value2 else value2
    percentage_diff = ((bigger_value - smaller_value) / abs(smaller_value)) * 100
    return percentage_diff


def get_level_ranges(start_price, level_range, price_level_ceiling):
    ceil_price = np.ceil(start_price + (start_price * 0.01 * price_level_ceiling))
    floor_price = np.floor(start_price - (start_price * 0.01 * price_level_ceiling))
    levels = np.arange(floor_price, ceil_price+1, level_range)
    return levels




import requests

def get_current_price(symbol):
    url = f"https://api.binance.com/api/v3/avgPrice?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    # price = data["price"]
    return data