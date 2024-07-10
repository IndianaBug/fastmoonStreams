import pytest
import json
import inspect
from functools import partial
import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

from streams import streams_data
from config import message_processor_fail_threshold
from ProcessCenter.StreamDataClasses import MarketState
market_state = MarketState(streams_data)

def depth(id_, processed_data ):
    """Depth datareturn tester."""
    # Retrieve ID with a fallback if 'id_ws' is not available
    message = f"Wrong parts:"

    is_timestamp = isinstance(processed_data['timestamp'], float)
    is_bids = all(isinstance(bid, list) for bid in processed_data['bids'])
    is_asks = all(isinstance(ask, list) for ask in processed_data['asks'])

    # Collect all failing parts
    wrong_parts = []
    if not is_timestamp:
        wrong_parts.append("timestamp")
    if not is_bids:
        wrong_parts.append("bids")
    if not is_asks:
        wrong_parts.append("asks")

    if wrong_parts:
        message += id_ + ", ".join(wrong_parts) + "."
        return message
    else:
        return True

def trades_liquidations(id_, processed_data):
    """ trades and liquidatiosn datareturn tester"""
    message = f" Wrong parts:"

    is_timestamp = isinstance(processed_data['timestamp'], float)
    is_trade_structure = all(
            all(
                isinstance(trade.get(field), expected_type) 
                for field, expected_type in [("side", str), ("price", float), ("quantity", float), ("timestamp", float)]
            ) for trade in processed_data['trades']
        )

    is_liquidaitons_structure = all(
            all(
                isinstance(trade.get(field), expected_type) 
                for field, expected_type in [("side", str), ("price", float), ("quantity", float), ("timestamp", float)]
            ) for trade in processed_data['liquidations']
        )

    wrong_parts = []
    if not is_timestamp:
        wrong_parts.append("timestamp")
    if not is_trade_structure:
        wrong_parts.append("trades")
    if not is_liquidaitons_structure:
        wrong_parts.append("liquidations")

    if wrong_parts:
        message += id_ + ", ".join(wrong_parts) + "."
        return message
    else:
        return True

def oi(id_, processed_data):
    """OI structure tester for dynamic keys."""
    message = f"Wrong parts:"

    wrong_parts = []
    
    for key, value in processed_data.items():

        if not isinstance(value, dict):
            wrong_parts.append(f"{key} (not a dict)")
            continue
        if not isinstance(value.get('oi'), float):
            wrong_parts.append(f"{key}.oi")
        if not isinstance(value.get('price'), float):
            wrong_parts.append(f"{key}.price")
        if not isinstance(value.get('timestamp'), float):
            wrong_parts.append(f"{key}.timestamp")


    if wrong_parts:
        message += id_ + ", ".join(wrong_parts) + "."
        return message
    else:
        return True

def oifunding(id_, processed_data):
    """OI structure tester for dynamic keys."""

    message = f" Wrong parts:"

    wrong_parts = []
    
    for key, value in processed_data.items():
        if key == "timestamp":
            continue
        if not isinstance(value, dict):
            wrong_parts.append(f"{key} (not a dict)")
            continue
        if not isinstance(value.get('oi'), float):
            wrong_parts.append(f"{key}.oi")
        if not isinstance(value.get('price'), float):
            wrong_parts.append(f"{key}.price")
            wrong_parts.append(f"{key}.oi")
        if not isinstance(value.get('funding'), float):
            wrong_parts.append(f"{key}.funding")
        if not isinstance(value.get('timestamp'), float):
            wrong_parts.append(f"{key}.timestamp")

    if wrong_parts:
        message += id_ + ", ".join(wrong_parts) + "."
        return message
    else:
        return True

def oioption_optionoi(id_, processed_data):
    """OI option structure tester for dynamic keys."""
    message = f"Wrong parts:"

    wrong_parts = []
    
    for key, value in processed_data.items():
        if key == "timestamp":
            continue
        if not isinstance(value, dict):
            wrong_parts.append(f"{key} (not a dict)")
            continue
        if not isinstance(value.get('symbol'), str):
            wrong_parts.append(f"{key}.symbol")
        if not isinstance(value.get('strike'), float):
            wrong_parts.append(f"{key}.strike")
        if not isinstance(value.get('days_left'), int):
            wrong_parts.append(f"{key}.days_left")
        if not isinstance(value.get('oi'), float):
            wrong_parts.append(f"{key}.oi")
        if not isinstance(value.get('price'), float):
            wrong_parts.append(f"{key}.price")

    if wrong_parts:
        message += id_ + ", ".join(wrong_parts) + "."
        return message
    else:
        return True

def funding(id_, processed_data):
    """funding structure tester for dynamic keys."""
    message = f"Wrong parts:"

    wrong_parts = []
    
    for key, value in processed_data.items():
        if key == "timestamp":
            continue
        if not isinstance(value, dict):
            wrong_parts.append(f"{key} (not a dict)")
            continue
        if not isinstance(value.get('funding'), float):
            wrong_parts.append(f"{key}.funding")
        if not isinstance(value.get('timestamp'), float):
            wrong_parts.append(f"{key}.timestamp")

    if wrong_parts:
        message += id_ + ", ".join(wrong_parts) + "."
        return message
    else:
        return True

def gta_tta_ttp(id_, processed_data):
    """funding structure tester for dynamic keys."""
    message = f"Wrong parts:"

    wrong_parts = []

    possible_metrics = [
        "tta_long_ratio", "tta_short_ratio", "tta_ratio",
        "ttp_long_ratio", "ttp_short_ratio", "ttp_ratio",
        "gta_long_ratio", "gta_short_ratio", "gta_ratio",
        "ttp_size_ratio", "tta_size_ratio", "gta_size_ratio"
    ]

    for key, value in processed_data.items():
        if key == "timestamp":
            continue
        if not isinstance(value, dict):
            wrong_parts.append(f"{key} (not a dict)")
            continue

        valid_metrics = any(isinstance(value.get(metric), float) for metric in possible_metrics)

        if not valid_metrics:
            wrong_parts.append(f"{key}.None of the required metrics are valid")


    if wrong_parts:
        message += id_ + ", ".join(wrong_parts) + "."
        return message
    else:
        return True

def find_testing_method(objective, inst_type):
    """ finds testing method"""
    if objective in ["trades", "liquidations", "optionTrades", "tradesagg"]:
        return trades_liquidations
    if objective in ["depth"]:
        return depth
    if objective in ["funding"]:
        return funding
    if objective in ["oi"] and inst_type != "option":
        return oi
    if objective in ["oi", "oioption", "oifunding"] and inst_type == "option":
        return oioption_optionoi
    if objective in ["oifunding", "fundingoi"] and inst_type != "option":
        return oifunding
    if objective in ["gta", "tta", "ttp"]:
        return gta_tta_ttp

def open_json_file(path):
    with open(path, 'r') as file:
        return json.load(file)        

async def create_testing_object(streams_data, parent_dir):
    testing_object = []

    for stream_data in streams_data:
        
        
        if stream_data.get("objective") == "heartbeats":
            continue

        exchange = stream_data.get("exchange")
        
        id_ = stream_data.get('id_ws') or stream_data.get('id_api')

        api_ws_str = "ws" if "ws" in id_ else "api"

        objective = stream_data.get("objective") or stream_data.get("objectives")
        inst_type = stream_data.get("instType") or stream_data.get("instTypes")
        path_json = parent_dir + f"\\sample_data\\raw\\{api_ws_str}\\{exchange}\\{id_}.json" 
        
        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        data_generator = partial(open_json_file, path_json)
        method_tester = find_testing_method(objective, inst_type)
        processing_method = stream_data.get("on_message_method_api") or stream_data.get("on_message_method_ws")
        
        testing_object.append({
            "id": id_, 
            "data_generator": data_generator, 
            "processing_method": processing_method, 
            "method_tester": method_tester,
            "stream_data" : stream_data,
        })

        if "id_api_2" in stream_data and stream_data.get("id_api_2") != "":
            
            if stream_data.get("id_ws") == "bingx_ws_spot_depth_btcusdt":
                continue

            id_ = stream_data.get("id_api_2")

            path_api_2 = parent_dir + f"\\sample_data\\raw\\api_2\\{exchange}\\{id_}.json"
            
            data_generator = partial(open_json_file, path_api_2)

            processing_method = stream_data.get("on_message_method_api_2")
            
            testing_object.append({
                "id": id_, 
                "data_generator": data_generator, 
                "processing_method": processing_method, 
                "method_tester": method_tester,
                "stream_data" : stream_data,
            })

    return testing_object

test_cases = asyncio.run(create_testing_object(streams_data, parent_dir))

@pytest.mark.parametrize("case", test_cases)
@pytest.mark.asyncio
async def test_dynamic(case):

    id_ = case["id"]
    data_generator = case["data_generator"]
    processing_method = case["processing_method"]
    method_tester = case["method_tester"]
    stream_data = case["stream_data"]

    results = []
    for data in data_generator():
        try:
            data = json.dumps(data)
            processed_data = await processing_method(data, market_state, stream_data)
            result = method_tester(id_, processed_data)
            results.append(result)
        except:
            results.append(False)

    true_count = results.count(True)
    total_count = len(results)
    threshold_count = message_processor_fail_threshold * total_count

    assert true_count >= threshold_count, (
        f"Test {id_} failed: Only {true_count}/{total_count} "
        f"({(true_count/total_count)*100:.2f}%) passed. "
        f"Threshold is {message_processor_fail_threshold*100:.2f}%"
    )

