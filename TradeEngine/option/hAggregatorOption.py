import pandas as pd
import numpy as np
import time

class hAggregator_Option():
    """
        Aggregates Option data from different exchanges
    """
    def __init__(self, processes: list, number_rows=741):
        """
            number_rows = The length of the dataset to keep
        """
        self.processes = processes
        self.snapshot_columns = ["price"]+[f"{vvv}_{v}_{vv}" for vvv in ["call", "put"] for v in self.processes[0].df_call.keys() for vv in list(self.processes[0].df_call[next(iter(self.processes[0].df_call))].columns)]
        self.snapshot = pd.DataFrame(index=pd.to_datetime([], utc=True), columns=[self.snapshot_columns]).rename_axis('timestamp')
        self.number_rows = number_rows

    def input_data(self, raw_data, index_price):

        dic_df_call = { key : pd.DataFrame() for key in self.processes[0].df_call.keys()}
        dic_df_put = { key : pd.DataFrame() for key in self.processes[0].df_put.keys()}
        
        for c, data in zip(self.processes, raw_data):
            c.input_oi(data, index_price)

        for c in self.processes:
            for key in c.df_put.keys():
                dic_df_call[key] = pd.concat([dic_df_call[key], c.df_call[key]], ignore_index=True)
                dic_df_put[key] = pd.concat([dic_df_call[key], c.df_put[key]], ignore_index=True)

        for frame in dic_df_call.keys():
            dic_df_call[frame] = dic_df_call[frame].sum().to_frame().T
            dic_df_put[frame] = dic_df_put[frame].sum().to_frame().T

        self.snapshot.loc[pd.to_datetime(time.time(), unit='s', utc=True)]  = np.concatenate((np.array([float(index_price])), pd.concat([dic_df_put[x] for x in dic_df_call] + [dic_df_put[x] for x in dic_df_put], axis=1, ignore_index=True).values[0]))

        if len(self.snapshot) > self.number_rows:
            self.snapshot.iloc[1:]
