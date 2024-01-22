import json
from datetime import datetime, timedelta
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


def get_common_suffixes_agg_uni(n):
    """
        The maximum amount of datasets to aggregate is the len(alphabet). 
        Modify this function to get more aggregation possibilities
    """
    alphabet = 'xyzabcdefghijklmnopqrstuvw'
    suffixes = [f'_{alphabet[i]}' for i in range(n)]
    return suffixes


def sort_columns_agg_uni_mvb(df :pd.DataFrame):
    first_str_column = next(iter(df.columns))
    float_columns = [col for col in df.columns if col != first_str_column]
    sorted_columns = [first_str_column] + sorted(float_columns, key=float)
    sorted_df = df[sorted_columns]
    str_col = list(map(str, sorted_columns))
    sorted_df.columns = str_col
    return sorted_df


def mvb_percentage_difference(center, value):
    if center == 0 and value > center:
        return float(100)
    if value == 0 and value < center:
        return float(9999999999)
    else:
        diff = value - center
        average = (center + value) / 2
        percentage_diff = (diff / average) * 100
        return percentage_diff

def choose_range_mvb(current_price, level, level_ranges):
    pd = mvb_percentage_difference(current_price, level)
    for index, r in enumerate(level_ranges):
        if index == 0 and pd < level_ranges[0]:
            return r
        elif index != 0 and index != len(level_ranges)-1 and pd >= level_ranges[index-1] and pd < level_ranges[index]:
            return r
        if index == len(level_ranges)-1 and pd >= level_ranges[index-1]:
            return r
        
def get_levels_list_mvb(levels):
    levels = np.sort(np.concatenate((levels, -1 * levels)))
    levels = levels[(levels != -0)]
    levels = np.append(levels, 100.0)
    return levels

def format_imput_vBooks_mvb(levels, uncomplete_levels, grouped_sum):
    array4 = np.zeros_like(levels)
    for i in range(len(levels)):
        if levels[i] in uncomplete_levels:
            array4[i] = grouped_sum[uncomplete_levels.tolist().index(levels[i])]
    return array4

def get_grouped_var_by_range_mvb(current_price, levels, raw_values, columns_float):
    try:
        choosen_level = np.array([choose_range_mvb(current_price, v, levels) for v in columns_float])
        unique_values, indices = np.unique(choosen_level, return_inverse=True)
        sums = [np.sum(raw_values[indices == val]) for val in unique_values]
        array4 = format_imput_vBooks_mvb(levels, unique_values, sums)
        return array4
    except:
        # In case there are only zeros, unlikely but possible
        return np.zeros_like(levels)