from ProcessCenter.DataFlow import DaskClientSupport
import multiprocessing as mp
import dask.dataframe as dd
import pandas as pd
import numpy as np
import json


path = "/workspaces/fastmoonStreams/sample_data/raw/api_2/binance/binance_api_perpetual_depth_btcusdperp.json"
data_api = json.dumps(json.load(open(path, "r"))[0])

path_2 = "/workspaces/fastmoonStreams/sample_data/raw/ws/binance/binance_ws_perpetual_depth_btcusdperp.json"
print(data)

# DaskSupport = DaskClientSupport()

# if __name__ == '__main__':
#     mp.freeze_support()  # This is only necessary on Windows, but doesn't hurt on other platforms
#     try:
#         client = DaskSupport.start_dask_client()
#         import time
#         # while True:
        
#         path = "/workspaces/fastmoonStreams/sample_data/processed/api/binance/binance_api_perpetual_depth_btcusdperp.json"
#         data = json.dumps(json.load(open(path, "r"))[0])
#         print(data)
        
#         print(dd.from_pandas(pd.DataFrame()))

#     except KeyboardInterrupt:
#         print("Interrupted by user. Shutting down gracefully...")
#     except RuntimeError as e:
#         print(str(e))
#     finally:
#         if 'client' in locals():
#             print("Finished running dusk")
