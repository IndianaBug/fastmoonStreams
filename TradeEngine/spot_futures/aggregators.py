import pandas as pd
import numpy as np

from utilis_spot_futures import get_common_suffixes_agg_uni, sort_columns_agg_uni_mvb
from utilis_spot_futures import get_levels_list_mvb, get_grouped_var_by_range_mvb

class sAggregatorUniversal():

    def __init__(self, identification, processes):
        self.identification = identification
        self.processes = processes
        self.snapshot = None
        self.suffixes = get_common_suffixes_agg_uni(len(processes))

    def merge_snapshots(self):
        """
            Any snapshot merger, books, OI, Liquidations, Trades
        """
        list_napshots = [
            sort_columns_agg_uni_mvb(df.snapshot) for df in self.processes
        ]


        for index, df in enumerate(list_napshots):
            if index == 0:
                merged_df = pd.merge(list_napshots[0], list_napshots[1], how='outer', left_index=True, right_index=True, suffixes=(self.suffixes[index], self.suffixes[index+1]))
            if index == len(list_napshots)-1:
                break
            if index != 0 and index != len(list_napshots)-1:
                merged_df = pd.merge(merged_df, list_napshots[index+1], how='outer', left_index=True, right_index=True, suffixes=(self.suffixes[index], self.suffixes[index+1]))
      
        common_columns_dic = {column.split("_")[0] : [] for column in merged_df.columns.tolist() }
        for column in merged_df.columns.tolist():
            common_columns_dic[column.split("_")[0]].append(column)
        
        sum = pd.DataFrame()
        for common_columns in common_columns_dic.keys():
            for index, column in enumerate(common_columns_dic[common_columns]):
                if index == 0:
                    sum[common_columns] = merged_df[column]
                else:
                    sum[common_columns] = sum[common_columns] + merged_df[column]

        self.snapshot = sum.copy()


class m_Variance_books():
    """
        Processes heatmaps of variances of books  --  trades
        It is suppoused to capture weather spoofing, weather price chasers
    """

    def __init__ (self, processes, levels, snap_length=60*24*7):

        """
          processes : Aggregator if books and trades . [0]  - books,  [1] --- trades. Must be consistent
          snap_length : The length of the snapshot to keep
        """

        self.processes = processes
        self.snap_length = snap_length
        self.levels  = get_levels_list_mvb(levels)
        self.snapshot = pd.DataFrame(columns=[e.replace(".0", "").replace("-", "n_").replace(".", "_") for e in ["price_var"] + ["".join([str(x), "_var"]) for x in self.levels]], index=pd.to_datetime([]))


    def get_variances(self, current_price):

        df_books = self.processes[0].snapshot.copy()
        df_trades = self.processes[1].snapshot.copy()

        merged_df = pd.merge(df_books, df_trades, how='outer', left_index=True, right_index=True, suffixes=('_books', '_trades'))
        common_columns = df_books.columns.intersection(df_trades.columns).tolist()

        for column in common_columns:
            if "price" not in column:
                merged_df[column] = merged_df[column + '_books'].sub(merged_df[column + '_trades'], fill_value=0)
                merged_df = merged_df.drop([column + '_books', column + '_trades'], axis=1)
        merged_df = merged_df.drop('price_trades', axis=1)
        merged_df = merged_df.rename(columns={'price_books': 'price'})

        merged_df = sort_columns_agg_uni_mvb(merged_df)

        for index in range(len(merged_df)):
            if index != 0:
                merged_df.iloc[index-1] = merged_df.iloc[index].values - merged_df.iloc[index-1].values
        merged_df = merged_df.drop(merged_df.index[-1])
        merged_df = merged_df.var()
        merged_df = pd.DataFrame([merged_df.values], columns=merged_df.index)
        new_column_names = ["_".join([x.split('.')[0], "var"]) for x in merged_df.columns.tolist()]
        merged_df = merged_df.rename(columns=dict(zip(merged_df.columns, new_column_names)))

        price_var = merged_df["price_var"].values[0]
        merged_df = merged_df.drop("price_var", axis=1)
        columns_transformed_float = [float(x.split('_')[0]) for x in merged_df.columns.tolist()]
        values = get_grouped_var_by_range_mvb(current_price, self.levels, merged_df.values[0], columns_transformed_float)
        final = np.concatenate((np.array([price_var]), values))
        self.snapshot.loc[pd.Timestamp.now().round('T')] = final
        if len(self.snapshot) > self.snap_length:
            self.snapshot = self.snapshot.drop(0)