import json
import asyncio
import os
import sys
import pandas as pd
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

flow_types = ["depthflow", "tradesflow", "oiflow", "liqflow", "fundingflow", "gtaflow", "ttaflow", "ttpflow"]

from ProcessCenter.DataFlow import MarketDataFusion
from ProcessCenter.StreamDataClasses import MarketState
from streams import streams_data, merge_types

market_state = MarketState(streams_data)
fusor = MarketDataFusion(mode="testing")
### Reference All dependencies

def reference_dependencies_to_processor():
    """ passes dependencies to processor """
    for stream_data in streams_data:
        processors_names = [x for x in stream_data if x in flow_types]
        for processor_name in processors_names:
            stream_data.get(processor_name).reference_market_state(market_state)
            stream_data.get(processor_name).reference_stream_data(stream_data)
            stream_data.get(processor_name).reference_saving_directory(parent_dir)
    fusor.reference_market_state(market_state)
    fusor.reference_saving_directory(parent_dir)
    

reference_dependencies_to_processor()

## Simulate streams

async def input_apiws_books(data_ws, data_api,  processor):
    """ helper to input books """
    try:
        data_ws = json.load(data_ws)
        data_api = json.load(data_api)
        await asyncio.sleep(1)
        await processor.input_data_api(json.dumps(data_api[0]))
        for d in data_ws[::-1]:
            await processor.input_data_ws(json.dumps(d))
            await asyncio.sleep(1)
    except Exception as e:
        print(e)

async def input_apiws_data(data, processor):
    """ helper """
    try:
        data = json.load(data)
        for d in data[::-1]:
            await processor.input_data(json.dumps(d))
            # await asyncio.sleep(0.4)
    except Exception as e:
        print(e)

async def cereate_tasks_single_dataflow(stream_data):
    """ Creates tasks so you can run them at once"""
    try:
        tasks = []
        exchange = stream_data.get("exchange") 
        path_api = parent_dir+f"\\sample_data\\raw\\api\\{exchange}\\{stream_data.get('id_api')}.json"
        path_api_2 = parent_dir+f"\\sample_data\\raw\\api_2\\{exchange}\\{stream_data.get('id_api_2')}.json"
        path_ws = parent_dir+f"\\sample_data\\raw\\ws\\{exchange}\\{stream_data.get('id_ws')}.json"

        if stream_data.get("id_api", "") != "":
            dataapi = open(path_api, "r")
        if stream_data.get("id_ws", "") != "":
            dataws = open(path_ws, "r")
        if stream_data.get("id_api_2", "") != "":
            dataapi2 = open(path_api_2, "r")

        processors_names = [x for x in stream_data if x in flow_types]
        for processor_name in processors_names:
            processor = stream_data.get(processor_name)
            if processor_name == "depthflow":
                tasks.append(asyncio.ensure_future(input_apiws_books(dataws, dataapi2, processor)))
                tasks.append(asyncio.ensure_future(processor.schedule_snapshot()))
            elif processor_name in ["fundingflow", "gtaflow", "ttaflow", "ttpflow", "oiflow"]:
                tasks.append(asyncio.ensure_future(input_apiws_data(dataapi, processor)))
            elif processor_name in ["liqflow", "tradesflow"]:
                tasks.append(asyncio.ensure_future(input_apiws_data(dataws, processor)))

            tasks.append(asyncio.ensure_future(processor.schedule_processing_dataframe()))
        return tasks
    
    except Exception as e:
        id_ = stream_data.get("id_api") if "id_api" in stream_data else stream_data.get("id_ws")
        print(f"Something went wrong with {id_} : {e}")  

def cereate_tasks_datafusion():
    """ Creates tasks so you can run them at once"""
    tasks = []
    for aggregation_type in merge_types:
        if aggregation_type in ["depth_spot", "depth_future"]:
            tasks.append(asyncio.ensure_future(fusor.schedule_aggregation_depth(aggregation_type)))
        if aggregation_type in ["trades_spot", "trades_future", "trades_option"]:
            tasks.append(asyncio.ensure_future(fusor.schedule_aggregation_trades(aggregation_type)))
    return tasks

async def run_all_tasks():
    """ Creates tasks so you can run them at once"""
    all_tasks = []
    for stream_data in streams_data:
        tasks = await cereate_tasks_single_dataflow(stream_data)
        for task in tasks:
            all_tasks.append(asyncio.ensure_future(task))
    for task in cereate_tasks_datafusion():
        all_tasks.append(asyncio.ensure_future(task))
    # print(all_tasks)
    await asyncio.gather(*tasks, return_exceptions=True)



if __name__ == "__main__":
    asyncio.run(run_all_tasks())

# Pytest




# def depthflow_tester(stream_data):
#     """ depth datafrlow tester """
#     message = "Wrong parts: "
#     _id = stream_data.get("id_ws") or stream_data.get("id_api")
#     inst_type = stream_data.get("instType") or stream_data.get("instTypes")
#     dataframe = market_state.raw_data.get("depth").get(inst_type).get(_id)
#     is_dataframe = isinstance(dataframe, pd.DataFrame)
#     is_empty = (is_dataframe != 0).any(axis=1).any() if is_dataframe else False
#     wrong_parts = []
#     if not is_dataframe:
#         wrong_parts.append("NO dataframe found")
#     if not is_empty:
#         wrong_parts.append("Dataframe is empty")

#     if wrong_parts:
#         message += _id + ", ".join(wrong_parts) + "."
#         return message
#     else:
#         return True

                 

#     async def main(self):
#         tasks = await self.cereate_tasks()
#         await asyncio.gather(*tasks, return_exceptions=True)


# class test_mergers():

#     fusion = MarketDataFusion(
#         books_aggregation_interval = 10,
#     )

#     def test_books(self, isnt_type):
#         """ Test if books are merged correctly """
#         directory_path = parent_dir+f"\\sample_data\\dfpandas\\processed\\"
#         entries = os.listdir(directory_path)
#         files = [entry for entry in entries if os.path.isfile(os.path.join(directory_path, entry))]
#         files = [file for file in files if "processed_books" in file and "perpetual" in file]
#         dataframes = [pd.read_csv(directory_path+"\\"+file) for file in files]
#         self.fusion.merge_books(dataframes)

#         return dataframes
        

    


# if __name__ == "__main__":
#     stream_data = None
#     market_state = None
#     test_class = _test_flow(stream_data, market_state)
#     # or gather flow test to test in bulk
#     asyncio.run(test_class.main())
        

