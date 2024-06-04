import pandas as pd
import numpy as np
import json
import asyncio

from streams import connectionData as connection_data


path = "/workspaces/fastmoonStreams/sample_data/raw/api_2/binance/binance_api_perpetual_depth_btcusdperp.json"
# path = "C:\\coding\\fastmoon\\fastmoonStreams\\sample_data\\raw\\api_2\\binance\\binance_api_perpetual_depth_btcusdperp.json"
data_api = json.dumps(json.load(open(path, "r"))[0])

path_2 = "/workspaces/fastmoonStreams/sample_data/raw/ws/binance/binance_ws_perpetual_inverse_depth_btcusdperp.json"
# path_2 = "C:\\coding\\fastmoon\\fastmoonStreams\\sample_data\\raw\ws\\binance\\binance_ws_perpetual_inverse_depth_btcusdperp.json"
data_ws = json.load(open(path_2, "r"))


processor = connection_data[0].get("flowClass")
processor.pass_market_state(market_state={})
processor.pass_connection_data({})


async def input_data____():
    for d in data_ws[::-1]:
        await processor.input_data_ws(json.dumps(d))
        await asyncio.sleep(1)

async def main():
    tasks = []
    tasks.append(asyncio.ensure_future(processor.input_data_api(data_api)))
    tasks.append(asyncio.ensure_future(input_data____()))
    tasks.append(asyncio.ensure_future(processor.schedule_snapshot()))
    tasks.append(asyncio.ensure_future(processor.schedule_processing_dataframe()))
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())













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



# from dataclasses import dataclass, field
# import time
# import asyncio
# from numba import jit


# @dataclass
# class MarketState:
#     """ 
#       Holds market data for instruments
      
#       Every instrument should be named like this symbol@instType@exchange
#     """
#     _data : dict = field(default_factory=dict)
    
#     expiration_timeout = 600
#     symbol_remove_timeout = 600

#     def retrive_data(self, symbol, objective, default_return=None):
#         """Gets value for key in symbol's data."""
#         return self._data.get(symbol, {}).get(objective, default_return)

#     def retrive_symbol_data(self, symbol, default_return=None):
#         """Gets value for key in symbol's data."""
#         return self._data.get(symbol, default_return)

#     def create_symbol_dict(self, symbol):
#         """Sets value for key in symbol's data (creates dict if needed)."""
#         self._data[symbol] = {}

#     def update_from_dict(self, data_dict):
#         """Updates with new data based on condition."""
#         for symbol, symbol_data in data_dict.items():
#             if symbol not in self._data:
#                 self.create_symbol_dict(symbol)
#             self._data[symbol].update(symbol_data)
#             self._data[symbol]['update_time'] = time.time()
    
#     @jit(nopython=True)
#     async def remove_dead_instruments(self, check_interval):
#         while True:
#             current_time = time.time()
#             symbols_to_remove = [symbol for symbol, data in self._data.items() if current_time - data.get('update_time', 0) > self.expiration_timeout]
#             for symbol in symbols_to_remove:
#                 del self._data[symbol]
#             await asyncio.sleep(self.symbol_remove_timeout) 
    
#     @jit(nopython=True)
#     def retrive_data_by_objective(self, objectives:list=[], inst_types:list=[], exchanges:list=[]):
#         """ Retrives data by objective. If instrument type is passed in a list, these will be ignored"""
#         data = {obj : {} for obj in objectives}
#         for instrument in self._data:
#             isnt_type = instrument.split("@")[1]
#             if isnt_type in inst_types:
#                 for obj in objectives:
#                     data[obj][instrument] = self.retrive_data(instrument, obj)
#         return data

#     @jit(nopython=True)
#     def retrive_data_by_exchange(self, exchanges:list=[], objectives:list=[]):
#         """ Retrives data by objective. If instrument type is passed in a list, these will be ignored"""
#         data = {exchange : {obj : {} for oj in objectives} for exchange in exchanges}
#         for instrument in self._data:
#             exchange = instrument.split("@")[-1]
#             if exchange in exchanges:
#                 for obj in objectives:
#                     data[exchange][obj][instrument] = self._data.get(instrument).get(obj)
#         return data




    

# # Example usage
# market_state = MarketState()

# data_update = {"ETH": {"oi": 1}}
# market_state.update_from_dict(data_update)

# data_update = {"LL": {"oi": 1}}
# market_state.update_from_dict(data_update)

# data_update = {"ETH": {"oi": 2, "gta": 3}}
# market_state.update_from_dict(data_update)

# data_update = {"ETH": {"foo": 212, "gta": 3}}
# market_state.update_from_dict(data_update)

# print(market_state._data)  

# print(market_state.retrive_data("ETH", "oi"))