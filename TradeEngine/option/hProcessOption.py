import numpy as np
import pandas as pd
import json
import time
from utilis_option import ohelper_percentage_difference, ohelper_get_columns, ohelper_create_dic_df_exp 
from utilis_option import ohelper_get_countdowns_df, ohelper_get_exp_day, ohelper_choose_range, ohelper_get_exp_day_okx

class hProcess_option_Deribit():

    """
        AN EXAMPLE OF A LOGIC AT THE END OF THE FILE
    """

    def __init__ (self, expiration_ranges : np.array, price_levels : np.array):

        """
            The main objects of the class are  self.df_call self.df_put that contain dictionaries of dataframes of OIs by strices by expiration ranges of puts and calls options

            expiration_ranges :  is used to create heatmaps of OI per strike per expiration limit.
                                 np.array([1.0, 7.0, 35.0]) will create 4 expiration ranges 
                                    - (0 , 1]
                                    - (1 , 7]
                                    - (7, 35]
                                    - (35, +inf)
            price_levels : these are % ranges from the current price.
                           used to create levels of oi by strike from the current price
                           np.array([0, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 100.0])  will create 16 levels
                           (-ing, -25)
                           [-25, -10)
                           ....
                           [25, +inf]
                           The 100 value is actually a helping value, can by any as long as it is > 25 
        """
        self.expiration_ranges = expiration_ranges
        self.price_levels = price_levels
        self.df_call = ohelper_create_dic_df_exp(expiration_ranges, ohelper_get_columns(price_levels, what="columns"))  # Creates a dictionary with dfs containing data by expiration of options
        self.df_put = ohelper_create_dic_df_exp(expiration_ranges, ohelper_get_columns(price_levels, what="columns"))

    def input_oi(self, raw_data : dict,  indexPrice : float):
        self.input_oi_helper(raw_data=raw_data, 
                            df_side=self.df_call, 
                            logic_side="C",
                            indexPrice=indexPrice)
        
        self.input_oi_helper(raw_data=raw_data, 
                            df_side=self.df_put, 
                            logic_side="P",
                            indexPrice=indexPrice)


    def input_oi_helper(self, raw_data : dict, df_side : pd.DataFrame,  logic_side : str, indexPrice : float):
        options_data_raw = raw_data
        options_data = {
                            "strikes" : np.array([float(x["instrument_name"].split('-')[-2]) for x in options_data_raw["result"] if x["instrument_name"].split('-')[-1] == logic_side]),
                            "countdown" : np.array([ohelper_get_exp_day(x["instrument_name"].split('-')[1]) for x in options_data_raw["result"] if x["instrument_name"].split('-')[-1] == logic_side]),
                            "oi" : np.array([float(x["open_interest"]) for x in options_data_raw["result"] if x["instrument_name"].split('-')[-1] == logic_side]),
                        }

        raw_pd = pd.DataFrame(options_data).groupby(['countdown', 'strikes']).sum().reset_index()
        belong_bict = ohelper_get_countdowns_df(list(df_side.keys()), raw_pd['countdown'].unique())
        ranges = ohelper_get_columns(self.price_levels, what="r")
        for df_ident in belong_bict.keys():
            empty_df = pd.DataFrame()
            for countdown in belong_bict[df_ident]:
                df = raw_pd[raw_pd['countdown'] == countdown ].drop(columns=['countdown'])
                df['pcd'] = df['strikes'].apply(lambda x : ohelper_percentage_difference(indexPrice, x))
                df['range'] = df['pcd'].apply(lambda x: ohelper_choose_range(ranges, x))
                df = df.groupby(['range']).sum().reset_index().drop(columns=["strikes", "pcd"]).set_index('range')
                missing_values = np.setdiff1d(ranges, df.index.values)
                new_rows = pd.DataFrame({'oi': 0}, index=missing_values)
                combined_df = pd.concat([df, new_rows])
                combined_df = combined_df.transpose() 
                combined_df['timestamp'] = pd.to_datetime(int(time.time()) // 3600 * 3600, unit='s')
                combined_df.set_index('timestamp', inplace=True)
                combined_df = combined_df.sort_index(axis=1)
                empty_df = pd.concat([empty_df, combined_df], ignore_index=True)
            df_side[df_ident].loc[pd.to_datetime(int(time.time()) // 3600 * 3600, unit='s')]  = empty_df.sum(axis=0).values.T
            df_side[df_ident] = df_side[df_ident].tail(1)



class hProcess_option_Bybit():

    """
        AN EXAMPLE OF A LOGIC AT THE END OF THE FILE
    """

    def __init__ (self, expiration_ranges : np.array, price_levels : np.array):

        """
            The main objects of the class are  self.df_call self.df_put that contain dictionaries of dataframes of OIs by strices by expiration ranges of puts and calls options

            expiration_ranges :  is used to create heatmaps of OI per strike per expiration limit.
                                 np.array([1.0, 7.0, 35.0]) will create 4 expiration ranges 
                                    - (0 , 1]
                                    - (1 , 7]
                                    - (7, 35]
                                    - (35, +inf)
            price_levels : these are % ranges from the current price.
                           used to create levels of oi by strike from the current price
                           np.array([0, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 100.0])  will create 16 levels
                           (-ing, -25)
                           [-25, -10)
                           ....
                           [25, +inf]
                           The 100 value is actually a helping value, can by any as long as it is > 25 
        """
        self.expiration_ranges = expiration_ranges
        self.price_levels = price_levels
        self.df_call = ohelper_create_dic_df_exp(expiration_ranges, ohelper_get_columns(price_levels, what="columns"))  # Creates a dictionary with dfs containing data by expiration of options
        self.df_put = ohelper_create_dic_df_exp(expiration_ranges, ohelper_get_columns(price_levels, what="columns"))

    def input_oi(self, raw_data : dict,  indexPrice : float):
        """
            Inputs OI by expiration range, by strike by put and call
        """
        self.input_oi_helper(raw_data=raw_data, 
                            df_side=self.df_call, 
                            logic_side="C",
                            indexPrice=indexPrice)
        
        self.input_oi_helper(raw_data=raw_data, 
                            df_side=self.df_put, 
                            logic_side="P",
                            indexPrice=indexPrice)



    def input_oi_helper(self, raw_data : dict, df_side : pd.DataFrame,  logic_side : str, indexPrice : float):
        """

            Explanaition of processing data of recieving json object
        
            raw data : raw dictionary of options summary
            df_side : df_calls, df_puts
            logic_result, logic_instrument_name, logic_opne_interest, logic_side : dictionary logic
            indexPrice : index price
            logic_side: P, C (puts calls)

        """
        options_data_raw = raw_data
        options_data = {
                            "strikes" : np.array([float(x["symbol"].split('-')[-2]) for x in options_data_raw["result"]["list"] if x["symbol"].split('-')[-1] == logic_side]),
                            "countdown" : np.array([ohelper_get_exp_day(x["symbol"].split('-')[1]) for x in options_data_raw["result"]["list"] if x["symbol"].split('-')[-1] == logic_side]),
                            "oi" : np.array([float(x["openInterest"]) for x in options_data_raw["result"]["list"] if x["symbol"].split('-')[-1] == logic_side]),
                        }

        raw_pd = pd.DataFrame(options_data).groupby(['countdown', 'strikes']).sum().reset_index()
        belong_bict = ohelper_get_countdowns_df(list(df_side.keys()), raw_pd['countdown'].unique())
        ranges = ohelper_get_columns(self.price_levels, what="r")
        for df_ident in belong_bict.keys():
            empty_df = pd.DataFrame()
            for countdown in belong_bict[df_ident]:
                df = raw_pd[raw_pd['countdown'] == countdown ].drop(columns=['countdown'])
                df['pcd'] = df['strikes'].apply(lambda x : ohelper_percentage_difference(indexPrice, x))
                df['range'] = df['pcd'].apply(lambda x: ohelper_choose_range(ranges, x))
                df = df.groupby(['range']).sum().reset_index().drop(columns=["strikes", "pcd"]).set_index('range')
                missing_values = np.setdiff1d(ranges, df.index.values)
                new_rows = pd.DataFrame({'oi': 0}, index=missing_values)
                combined_df = pd.concat([df, new_rows])
                combined_df = combined_df.transpose() 
                combined_df['timestamp'] = pd.to_datetime(int(time.time()) // 3600 * 3600, unit='s')
                combined_df.set_index('timestamp', inplace=True)
                combined_df = combined_df.sort_index(axis=1)
                empty_df = pd.concat([empty_df, combined_df], ignore_index=True)
            df_side[df_ident].loc[pd.to_datetime(int(time.time()) // 3600 * 3600, unit='s')]  = empty_df.sum(axis=0).values.T
            df_side[df_ident] = df_side[df_ident].tail(1)




class hProcess_option_Okx():

    """
        AN EXAMPLE OF A LOGIC AT THE END OF THE FILE
    """

    def __init__ (self, expiration_ranges : np.array, price_levels : np.array):

        """
            The main objects of the class are  self.df_call self.df_put that contain dictionaries of dataframes of OIs by strices by expiration ranges of puts and calls options

            expiration_ranges :  is used to create heatmaps of OI per strike per expiration limit.
                                 np.array([1.0, 7.0, 35.0]) will create 4 expiration ranges 
                                    - (0 , 1]
                                    - (1 , 7]
                                    - (7, 35]
                                    - (35, +inf)
            price_levels : these are % ranges from the current price.
                           used to create levels of oi by strike from the current price
                           np.array([0, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 100.0])  will create 16 levels
                           (-ing, -25)
                           [-25, -10)
                           ....
                           [25, +inf]
                           The 100 value is actually a helping value, can by any as long as it is > 25 
        """
        self.expiration_ranges = expiration_ranges
        self.price_levels = price_levels
        self.df_call = ohelper_create_dic_df_exp(expiration_ranges, ohelper_get_columns(price_levels, what="columns"))  # Creates a dictionary with dfs containing data by expiration of options
        self.df_put = ohelper_create_dic_df_exp(expiration_ranges, ohelper_get_columns(price_levels, what="columns"))

    def input_oi(self, raw_data : dict, indexPrice : float):
        """
            Inputs OI by expiration range, by strike by put and call
        """
        self.input_oi_helper(raw_data=raw_data, 
                            df_side=self.df_call, 
                            logic_side="C",
                            indexPrice=indexPrice)
        
        self.input_oi_helper(raw_data=raw_data, 
                            df_side=self.df_put, 
                            logic_side="P",
                            indexPrice=indexPrice)


    def input_oi_helper(self, raw_data : dict, df_side : pd.DataFrame, logic_side : str, indexPrice : float):
        options_data_raw = raw_data
        options_data = {
                            "strikes" : np.array([float(x["instId"].split('-')[-2]) for x in options_data_raw["data"] if x["instId"].split('-')[-1] == logic_side]),
                            "countdown" : np.array([ohelper_get_exp_day_okx(x["instId"].split('-')[2]) for x in options_data_raw["data"] if x["instId"].split('-')[-1] == logic_side]),
                            "oi" : np.array([float(x["oiCcy"]) for x in options_data_raw["data"] if x["instId"].split('-')[-1] == logic_side]),
                        }
        
        raw_pd = pd.DataFrame(options_data).groupby(['countdown', 'strikes']).sum().reset_index()
        belong_bict = ohelper_get_countdowns_df(list(df_side.keys()), raw_pd['countdown'].unique())
        ranges = ohelper_get_columns(self.price_levels, what="r")
        for df_ident in belong_bict.keys():
            empty_df = pd.DataFrame()
            for countdown in belong_bict[df_ident]:
                df = raw_pd[raw_pd['countdown'] == countdown ].drop(columns=['countdown'])
                df['pcd'] = df['strikes'].apply(lambda x : ohelper_percentage_difference(indexPrice, x))
                df['range'] = df['pcd'].apply(lambda x: ohelper_choose_range(ranges, x))
                df = df.groupby(['range']).sum().reset_index().drop(columns=["strikes", "pcd"]).set_index('range')
                missing_values = np.setdiff1d(ranges, df.index.values)
                new_rows = pd.DataFrame({'oi': 0}, index=missing_values)
                combined_df = pd.concat([df, new_rows])
                combined_df = combined_df.transpose() 
                combined_df['timestamp'] = pd.to_datetime(int(time.time()) // 3600 * 3600, unit='s')
                combined_df.set_index('timestamp', inplace=True)
                combined_df = combined_df.sort_index(axis=1)
                empty_df = pd.concat([empty_df, combined_df], ignore_index=True)
            df_side[df_ident].loc[pd.to_datetime(int(time.time()) // 3600 * 3600, unit='s')]  = empty_df.sum(axis=0).values.T
            df_side[df_ident] = df_side[df_ident].tail(1)

