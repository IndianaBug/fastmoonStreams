import pandas as pd
import numpy as np
import json
import asyncio

from streams import connectionData as connection_data


# path = "/workspaces/fastmoonStreams/sample_data/raw/api_2/binance/binance_api_perpetual_depth_btcusdperp.json"
path = "C:\\coding\\fastmoon\\fastmoonStreams\\sample_data\\raw\\api_2\\binance\\binance_api_perpetual_depth_btcusdperp.json"
data_api = json.dumps(json.load(open(path, "r"))[0])

#path_2 = "/workspaces/fastmoonStreams/sample_data/raw/ws/binance/binance_ws_perpetual_depth_btcusdperp.json"
path_2 = "C:\\coding\\fastmoon\\fastmoonStreams\\sample_data\\raw\ws\\binance\\binance_ws_perpetual_inverse_depth_btcusdperp.json"
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
