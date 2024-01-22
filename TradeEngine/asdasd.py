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





# Options Helpers

def ohelper_percentage_difference(center, value):
    if center == 0 and value > center:
        return float(100)
    if value == 0 and value < center:
        return float(9999999999)
    else:
        diff = value - center
        average = (center + value) / 2
        percentage_diff = (diff / average) * 100
        return percentage_diff
    

def ohelper_get_columns(price_percentage_ranges: np.array, what="ranges"):
    price_percentage_ranges = np.unique(np.sort(np.concatenate((price_percentage_ranges, -price_percentage_ranges)), axis=0))
    price_percentage_ranges[price_percentage_ranges == -0] = 0
    price_percentage_ranges[price_percentage_ranges == price_percentage_ranges[0]] = 0
    price_percentage_ranges = np.unique(price_percentage_ranges)
    columns = np.concatenate((np.array(['timestamp']), price_percentage_ranges), axis=0)
    if what == "columns":
        return columns
    else:
        return price_percentage_ranges
    

def ohelper_create_dic_df_exp(expiration_ranges, columns):
    df_dic = {}
    for i, exp_range in enumerate(expiration_ranges):
        if i in [0, len(expiration_ranges)-1]:
            df_dic[f'{int(exp_range)}'] = pd.DataFrame(columns=columns) #.set_index('timestamp')
            df_dic[f'{int(exp_range)}']['timestamp'] = pd.to_datetime([])
            df_dic[f'{int(exp_range)}'].set_index('timestamp', inplace=True)
        if i in [len(expiration_ranges)-1]:
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns) #.set_index('timestamp')
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
        else:
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns) #.set_index('timestamp')
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
    df_dic.pop(f"{int(np.max(expiration_ranges))}_{int(np.min(expiration_ranges))}")
    return df_dic

def ohelper_get_countdowns_df(countdown_ranges, countdowns):
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

def ohelper_get_exp_day(date):                                  
    today_day = datetime.now().timetuple().tm_yday
    today_year = datetime.now().year
    f = datetime.strptime(date, "%d%b%y")
    expiration_date = f.timetuple().tm_yday
    expiration_year = f.year
    if today_year == expiration_year:
        r = expiration_date - today_day
    if today_year == expiration_year + 1:
        r = 365 + expiration_date - today_day
    return float(r)

def ohelper_choose_range(ppr, value):
    for index, r in enumerate(ppr):
        if index == 0 and value < r:
            return ppr[0]
        if index == len(ppr)-1 and value > r:
            return ppr[-1]
        if value < r and value >= ppr[index-1]:
            return r
        

def ohelper_get_exp_day_okx (date_string):
    date_format = '%y%m%d'
    target_date = datetime.strptime(date_string, date_format)
    current_date = datetime.now()
    days_left = (target_date - current_date).days
    return days_left


# import requests

# def get_current_price(symbol):
#     url = f"https://api.binance.com/api/v3/avgPrice?symbol={symbol}"
#     response = requests.get(url)
#     data = response.json()
#     # price = data["price"]
#     return data