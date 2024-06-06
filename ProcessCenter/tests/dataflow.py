import pandas as pd
import numpy as np
import json
import asyncio
import os
import sys


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

from streams import connection_data
flow_types = ["booksflow", "tradesflow", "oiflow", "liqflow", "fundingflow", "gtaflow", "ttaflow", "ttpflow"]


class _test_booksflow():
    
    def __init__(self, stream_id_parts, market_state = {"BTCUSD_PERP@perpetual@binance" : {"price" : 70000}}, connection_data = connection_data):
        self.stream_id_parts = stream_id_parts
        self.market_state = market_state
        self.connection_data = connection_data

    def return_processor(self):
        """ LAzy unit test of booksflow class """
        stream_data =  self.connection_data.get(next(all(part in id_ for part in self.stream_id_parts.spllit("_")) for id_ in connection_data))
        processors_names = [x for x in stream_data if flow_types]
        processors = {}
        for processor_name in processors_names:
            processor = stream_data.get("flowClass")
            processor.pass_market_state(market_state=self.market_state)
            processor.pass_connection_data(stream_data)
            processors[processor_name] = processor 
            processor.pass_savefolder_path(parent_dir)
        return processors 
    
    async def input_apiws_books(self, data_ws, data_api,  processor):
        """ helper """
        await asyncio.sleep(1)
        await processor.input_data_api(json.dumps(json.loads(data_api)[0]))
        for d in data_ws[::-1]:
            await processor.input_data_ws(json.dumps(d))
            await asyncio.sleep(1)

    async def input_apiws_data(self, data, processor):
        """ helper """
        for d in data[::-1]:
            await processor.input_data(json.dumps(d))
            await asyncio.sleep(1)
            
    async def input_api2_data(self, data, processor):
        """ helper """
        await processor.input_data(json.dumps(json.loads(data)[0]))
        await asyncio.sleep(1)

    async def flow_test(self, path_dataws=None, path_dataapi=None, path_dataapi2=None):
        """ Lazy unit test of booksflow module """
        exchange = path_dataws.split("_")[0] if path_dataws else path_dataapi.split("_")[0]
        path_api = parent_dir+f"/sample_data/raw/api/{exchange}/{path_dataapi}.json"
        path_api_2 = parent_dir+f"/sample_data/raw/api_2/{exchange}/{path_dataapi2}.json"
        path_ws = parent_dir+f"/sample_data/raw/ws/{exchange}/{path_dataws}.json"
        dataapi = json.dumps(json.load(open(path_api, "r"))[0])
        dataws = json.load(open(path_ws, "r"))
        dataapi2 = json.dumps(json.load(open(path_api_2, "r"))[0])
        processors = self.return_processor()
        
        for processor in processors:
            if processor == "booksflow":
                await self.input_apiws_books(dataws, dataapi2, processor)
            if processor in ["fundingflow", "gtaflow", "ttaflow", "ttpflow", "oiflow"]:
                self.input_apiws_data(dataapi, processor)
            if processor in ["liqflow", "tradesflow"]:
                self.input_apiws_data(dataws, processor)
        
    async def main(self):
        tasks = []
        tasks.append(asyncio.ensure_future(processor.flow_test()))
        await asyncio.gather(*tasks, return_exceptions=True)
        
# if __name__ == "__main__":
#     asyncio.run(main())


# binance_api_perpetual_depth_btcusdperp
# binance_ws_perpetual_inverse_depth_btcusdperp
    

booksdlow_test()

processor = connection_data[0].get("flowClass")
processor.pass_market_state(market_state={})
processor.pass_connection_data({})


# async def input_data____():
#     for d in data_ws[::-1]:
#         await processor.input_data_ws(json.dumps(d))
#         await asyncio.sleep(1)

# async def main():
#     tasks = []
#     tasks.append(asyncio.ensure_future(processor.input_data_api(data_api)))
#     tasks.append(asyncio.ensure_future(input_data____()))
#     tasks.append(asyncio.ensure_future(processor.schedule_snapshot()))
#     tasks.append(asyncio.ensure_future(processor.schedule_processing_dataframe()))
#     await asyncio.gather(*tasks, return_exceptions=True)

# if __name__ == "__main__":
#     asyncio.run(main())


