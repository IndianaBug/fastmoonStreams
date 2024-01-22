import numpy as np
import pandas as pd
from datetime import datetime, timedelta

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