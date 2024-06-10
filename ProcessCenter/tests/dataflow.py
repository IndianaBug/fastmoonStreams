import pandas as pd
import numpy as np
import json
import asyncio
import os
import sys
from ProcessCenter.DataFlow import MarketDataFusion


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

flow_types = ["booksflow", "tradesflow", "oiflow", "liqflow", "fundingflow", "gtaflow", "ttaflow", "ttpflow"]


class _test_flow():
    
    def __init__(self, stream_data, market_state = {"BTCUSD_PERP@perpetual@binance" : {"price" : 70000}}):
        self.market_state = market_state
        self.stream_data = stream_data
        self.processors = self.return_processors()

    def return_processors(self):
        """ Testing of any flow """
        processors_names = [x for x in self.stream_data if x in flow_types]
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
        try:
            data_ws = json.load(data_ws)
            data_api = json.load(data_api)
            await asyncio.sleep(1)
            await processor.input_data_api(json.dumps(data_api[0]))
            for d in data_ws[::-1]:
                await processor.input_data_ws(json.dumps(d))
                await asyncio.sleep(1)
                # print(processor.books.bids)
        except Exception as e:
            print(e)

    async def input_apiws_data(self, data, processor):
        """ helper """
        try:
            data = json.load(data)
            for d in data[::-1]:
                await processor.input_data(json.dumps(d))
        except Exception as e:
            print(e)
            

    async def cereate_tasks(self):
        """ Lazy unit test of booksflow module """
        try:

            tasks = []

            exchange = self.stream_data.get("exchange") #.split("_")[0] if self.stream_data.get("id_ws") else self.stream_data.get("id_api").split("_")[0]

            path_api = parent_dir+f"\\sample_data\\raw\\api\\{exchange}\\{self.stream_data.get('id_api')}.json"

            path_api_2 = parent_dir+f"\\sample_data\\raw\\api_2\\{exchange}\\{self.stream_data.get('id_api_2')}.json"

            path_ws = parent_dir+f"\\sample_data\\raw\\ws\\{exchange}\\{self.stream_data.get('id_ws')}.json"

            if self.stream_data.get("id_api", "") != "":
                dataapi = open(path_api, "r")
            if self.stream_data.get("id_ws", "") != "":
                dataws = open(path_ws, "r")
            if self.stream_data.get("id_api_2", "") != "":
                dataapi2 = open(path_api_2, "r")
            
            for processor in self.processors:
                if processor == "booksflow":
                    tasks.append(asyncio.ensure_future(self.input_apiws_books(dataws, dataapi2, self.processors.get(processor))))
                    tasks.append(asyncio.ensure_future(self.processors.get(processor).schedule_snapshot()))
                elif processor in ["fundingflow", "gtaflow", "ttaflow", "ttpflow", "oiflow"]:
                    tasks.append(asyncio.ensure_future(self.input_apiws_data(dataapi, self.processors.get(processor))))
                elif processor in ["liqflow", "tradesflow"]:
                    tasks.append(asyncio.ensure_future(self.input_apiws_data(dataws, self.processors.get(processor))))

                try:
                    tasks.append(asyncio.ensure_future(self.processors.get(processor).schedule_processing_dataframe()))
                except:
                    pass

            return tasks

        except Exception as e:
            
            id_ = self.stream_data.get("id_api") if "id_api" in self.stream_data else self.stream_data.get("id_ws")

            print(f"Something went wrong with {id_} : {e}")        

    async def main(self):
        tasks = await self.cereate_tasks()
        await asyncio.gather(*tasks, return_exceptions=True)


class test_mergers():

    fusion = MarketDataFusion(
        books_aggregation_interval = 10,
    )

    def test_books(self, isnt_type):
        """ Test if books are merged correctly """
        directory_path = parent_dir+f"\\sample_data\\dfpandas\\processed\\"
        entries = os.listdir(directory_path)
        files = [entry for entry in entries if os.path.isfile(os.path.join(directory_path, entry))]
        files = [file for file in files if "processed_books" in file and "perpetual" in file]
        dataframes = [pd.read_csv(directory_path+"\\"+file) for file in files]
        self.fusion.merge_books(dataframes)

        return dataframes
        

    


# if __name__ == "__main__":
#     stream_data = None
#     market_state = None
#     test_class = _test_flow(stream_data, market_state)
#     # or gather flow test to test in bulk
#     asyncio.run(test_class.main())
        

