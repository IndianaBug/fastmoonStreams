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
    
    
    
    
# import asyncio
# import json
# import unittest
# from unittest.mock import AsyncMock, patch

# class TestProcessor(unittest.TestCase):
#     def setUp(self):
#         # Set up paths
#         self.path = "/workspaces/fastmoonStreams/sample_data/raw/api_2/binance/binance_api_perpetual_depth_btcusdperp.json"
#         self.path_2 = "/workspaces/fastmoonStreams/sample_data/raw/ws/binance/binance_ws_perpetual_inverse_depth_btcusdperp.json"

#         # Load data
#         with open(self.path, "r") as file:
#             self.data_api = json.dumps(json.load(file)[0])
        
#         with open(self.path_2, "r") as file:
#             self.data_ws = json.load(file)

#         # Mock the processor
#         self.processor = AsyncMock()
#         self.processor.pass_market_state = AsyncMock()
#         self.processor.pass_connection_data = AsyncMock()
#         self.processor.input_data_ws = AsyncMock()
#         self.processor.input_data_api = AsyncMock()
#         self.processor.schedule_snapshot = AsyncMock()
#         self.processor.schedule_processing_dataframe = AsyncMock()

#     @patch('connection_data', [{'flowClass': self.processor}])
#     async def test_input_data(self):
#         # Pass initial data
#         self.processor.pass_market_state.assert_called_with({})
#         self.processor.pass_connection_data.assert_called_with({})

#         async def input_data____():
#             for d in self.data_ws[::-1]:
#                 await self.processor.input_data_ws(json.dumps(d))
#                 await asyncio.sleep(1)

#         tasks = [
#             asyncio.ensure_future(self.processor.input_data_api(self.data_api)),
#             asyncio.ensure_future(input_data____()),
#             asyncio.ensure_future(self.processor.schedule_snapshot()),
#             asyncio.ensure_future(self.processor.schedule_processing_dataframe())
#         ]

#         await asyncio.gather(*tasks, return_exceptions=True)

#         # Assertions
#         self.processor.input_data_api.assert_called_with(self.data_api)
#         self.assertEqual(self.processor.input_data_ws.call_count, len(self.data_ws))
#         self.processor.schedule_snapshot.assert_called()
#         self.processor.schedule_processing_dataframe.assert_called()

# if __name__ == "__main__":
#     asyncio.run(TestProcessor().test_input_data())







# class DaskClientSupport():
#     logger = logging.getLogger("Example")  # just a reference
#     def find_free_port(self, start=8787, end=8800):
#         for port in range(start, end):
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 try:
#                     s.bind(('', port))
#                     return port
#                 except OSError:
#                     self.logger.error("Dask error, free port: %s", OSError, exc_info=True)
#                     continue
#         raise RuntimeError(f"No free ports available in range {start}-{end}")

#     def start_dask_client(self):
#         for attempt in range(5):
#             try:
#                 # Check for an available port
#                 free_port = self.find_free_port()
#                 print(f"Using port: {free_port}")

#                 # Initialize the Dask Client with the available port
#                 client = Client(n_workers=1, threads_per_worker=1, port=free_port)
#                 return client
#             except RuntimeError as e:
#                 self.logger.error("Dask error, RuntimeError, reconnecting: %s", e, exc_info=True)
#                 print(f"Attempt {attempt + 1}: {str(e)}")
#             except Exception as e:
#                 self.logger.error("Dask error, Unexpected error: %s", e, exc_info=True)
#                 print(f"Attempt {attempt + 1}: Unexpected error: {str(e)}")
#         raise RuntimeError("Failed to start Dask Client after several attempts")