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


def create_data_frame(dftype, bucker_list):                                
    if dftype == 'sec':      
        r = list(range(0, 60, 1))     # Seconds in a minute
    if dftype == 'min':
        r = list(range(0, 10080, 1))  # Minutes in a week
    if dftype == 'h':
        r = list(range(0, 365*24, 1)) # Since the next leap year is 2100
    columns = ["_".join([str(x[0]), str(x[1])]) for x in bucker_list]
    df = pd.DataFrame(index=r, columns=['price', 'volume'] + columns)
    df.fillna(float(0), inplace=True)
    return df