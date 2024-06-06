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


class _test_flow():
    
    def __init__(self, stream_data, market_state = {"BTCUSD_PERP@perpetual@binance" : {"price" : 70000}}):
        self.market_state = market_state
        self.stream_data = stream_data
        self.processors = self.return_processors()

    def return_processors(self):
        """ Testing of any flow """
        processors_names = [x for x in self.stream_data if flow_types]
        processors = {}
        for processor_name in processors_names:
            processor = self.stream_data.get(processor_name)
            processor.pass_market_state(self.market_state)
            processor.pass_stream_data(self.stream_data)
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

    async def flow_test(self):
        """ Lazy unit test of booksflow module """
        exchange = self.stream_data.get("id_ws").split("_")[0] if self.stream_data.get("id_ws") else self.stream_data.get("id_api").split("_")[0]
        path_api = parent_dir+f"/sample_data/raw/api/{exchange}/{self.stream_data.get('id_api')}.json"
        path_api_2 = parent_dir+f"/sample_data/raw/api_2/{exchange}/{self.stream_data.get('id_api_2')}.json"
        path_ws = parent_dir+f"/sample_data/raw/ws/{exchange}/{self.stream_data.get('id_ws')}.json"
        dataapi = json.dumps(json.load(open(path_api, "r"))[0])
        dataws = json.load(open(path_ws, "r"))
        dataapi2 = json.dumps(json.load(open(path_api_2, "r"))[0])
        
        for processor in self.processors:
            if processor == "booksflow":
                await self.input_apiws_books(dataws, dataapi2, self.self.processors.get(processor))
            if processor in ["fundingflow", "gtaflow", "ttaflow", "ttpflow", "oiflow"]:
                self.input_apiws_data(dataapi, self.self.processors.get(processor))
            if processor in ["liqflow", "tradesflow"]:
                self.input_apiws_data(dataws, self.self.processors.get(processor))
        
    async def main(self):
        tasks = []
        tasks.append(asyncio.ensure_future(self.flow_test()))
        await asyncio.gather(*tasks, return_exceptions=True)
        

# if __name__ == "__main__":
#     stream_data = None
#     market_state = None
#     test_class = _test_flow(stream_data, market_state)
#     # or gather flow test to test in bulk
#     asyncio.run(test_class.main())
        

