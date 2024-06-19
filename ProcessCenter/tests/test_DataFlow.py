import json
import asyncio
import os
import sys
import pandas as pd
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

flow_types = ["depthflow", "tradesflow", "oiflow", "liqflow", "fundingflow"]

from ProcessCenter.DataFlow import MarketDataFusion
from ProcessCenter.StreamDataClasses import MarketState
from streams import streams_data, merge_types

market_state = MarketState(streams_data)
fusor = MarketDataFusion(
    depth_spot_aggregation_interval = None,
    depth_future_aggregation_interval = None,
    trades_spot_aggregation_interval = None,
    trades_future_aggregation_interval = None,
    trades_option_aggregation_interval = None,
    oi_deltas_aggregation_interval = None,
    liquidations_future_aggregation_interval = None,
    oi_options_aggregation_interval = 4,
    canceled_books_spot_aggregation_interval = None,
    canceled_books_future_aggregation_interval = None,
    mode="testing"
    )
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

async def input_apiws_books(data_ws, data_api,  processor):
    """ helper to input books """
    try:
        try:
            data_api = json.load(data_api)
            await processor.input_data_api(json.dumps(data_api[0]))
        except:
            print("Fucken here")
        try:
            data_ws = json.load(data_ws)
            await asyncio.sleep(1)
            for d in data_ws[::-1]:
                await processor.input_data_ws(json.dumps(d))
                await asyncio.sleep(1)
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)

async def input_apiws_data(data, processor):
    """ helper """
    try:
        data = json.load(data)
        for d in data[::-1]:
            await processor.input_data(json.dumps(d))
            await asyncio.sleep(0.4)
    except Exception as e:
        print(e)

async def cereate_tasks_single_dataflow(stream_data):
    """ Creates tasks so you can run them at once"""
    id_ = stream_data.get("id_api") if "id_api" in stream_data else stream_data.get("id_ws")
    if id_ != "bingx_api_perpetual_depth_btcusdt":
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
                if processor_name != "tradesflow":
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
    for aggregation_type in fusor.aggregation_intervals:
        if fusor.aggregation_intervals.get(aggregation_type):
            if aggregation_type in ["depth_spot", "depth_future"]:
                tasks.append(asyncio.ensure_future(fusor.schedule_aggregation_depth(aggregation_type=aggregation_type, aggregation_lag = 1)))
            elif aggregation_type in ["trades_spot", "trades_future"]:
                tasks.append(asyncio.ensure_future(fusor.schedule_aggregation_trades(aggregation_type=aggregation_type, aggregation_lag = 1)))
            elif aggregation_type in ["liquidations_future"]:
                tasks.append(asyncio.ensure_future(fusor.schedule_aggregation_liquidations(aggregation_type=aggregation_type, aggregation_lag = 1)))
            elif aggregation_type in ["oi_deltas"]:
                tasks.append(asyncio.ensure_future(fusor.schedule_aggregation_oi_deltas(aggregation_type=aggregation_type, aggregation_lag = 1)))
            elif aggregation_type in ["oi_options"]:
                tasks.append(asyncio.ensure_future(fusor.schedule_aggregation_oioption(aggregation_type=aggregation_type, aggregation_lag = 1)))
    return tasks

async def run_all_tasks():
    """ Creates tasks so you can run them at once"""
    all_tasks = []
    for stream_data in streams_data:
        tasks = await cereate_tasks_single_dataflow(stream_data)
        if tasks:
            all_tasks.extend(tasks)
    fusors = cereate_tasks_datafusion()
    all_tasks.extend(fusors)

    await asyncio.gather(*all_tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(run_all_tasks())



def check_dataframes_empty(data, path="", parent_key=""):
    """ Recursively checks if any pandas DataFrame in a nested dictionary is empty,
        with specific exceptions for certain keys under 'ticks_data_to_merge'.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            if parent_key == "ticks_data_to_merge" and key in ["spot", "future", "option", "oi_delta", "liquidations"]:
                if isinstance(value, dict) and not value:  # Checks if dictionary is empty
                    assert False, f"Dictionary at {new_path} is empty but shouldn't be"
            check_dataframes_empty(value, new_path, key)
    elif isinstance(data, pd.DataFrame):
        assert not data.empty, f"DataFrame at {path} is empty"
    else:
        pass

                 

        

