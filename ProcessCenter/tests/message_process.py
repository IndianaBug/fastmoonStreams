import unittest
import json
import inspect
from functools import partial
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(parent_dir)

class MessageProcessTester(unittest.TestCase):
    
    
        
    streams_data = []  # Example placeholder, should be set with actual data
    fail_threshold = 0.5

    @classmethod
    def setUpClass(cls, streams_data, fail_threshold):
        cls.streams_data = streams_data
        cls.fail_threshold = fail_threshold
        cls.add_testing_methods(cls.streams_data)

    @classmethod
    def get_methods(cls):
        return [name for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)]

    @classmethod
    def test_depth(cls, data, stream_data):
        """Depth datareturn tester."""
        # Retrieve ID with a fallback if 'id_ws' is not available
        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        message = f"{id}, Wrong parts:"

        is_timestamp = isinstance(data['timestamp'], float)
        is_bids = all(isinstance(bid, list) for bid in data['bids'])
        is_asks = all(isinstance(ask, list) for ask in data['asks'])

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
    
    @classmethod
    def test_trades_liquidations(cls, data, stream_data):
        """ trades and liquidatiosn datareturn tester"""
        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        message = f"{id}, Wrong parts:"

        is_timestamp = isinstance(data['timestamp'], float)
        is_trade_structure = all(
              all(
                  isinstance(trade.get(field), expected_type) 
                  for field, expected_type in [("side", str), ("price", float), ("quantity", float), ("timestamp", float)]
              ) for trade in data['trades']
          )

        is_liquidaitons_structure = all(
              all(
                  isinstance(trade.get(field), expected_type) 
                  for field, expected_type in [("side", str), ("price", float), ("quantity", float), ("timestamp", float)]
              ) for trade in data['liquidations']
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

    @classmethod
    def test_oi(cls, data, stream_data):
        """OI structure tester for dynamic keys."""

        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        message = f"{id}, Wrong parts:"

        is_timestamp = isinstance(data.get('timestamp'), float)

        wrong_parts = []
        
        for key, value in data.items():
            if key == "timestamp":
                continue
            if not isinstance(value, dict):
                wrong_parts.append(f"{key} (not a dict)")
                continue
            if not isinstance(value.get('oi'), float):
                wrong_parts.append(f"{key}.oi")
            if not isinstance(value.get('price'), float):
                wrong_parts.append(f"{key}.price")

        if not is_timestamp:
            wrong_parts.append("timestamp")

        if wrong_parts:
            message += id_ + ", ".join(wrong_parts) + "."
            return message
        else:
            return True

    @classmethod
    def test_oifunding(cls, data, stream_data):
        """OI structure tester for dynamic keys."""

        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        message = f"{id}, Wrong parts:"

        is_timestamp = isinstance(data.get('timestamp'), float)

        wrong_parts = []
        
        for key, value in data.items():
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

        if not is_timestamp:
            wrong_parts.append("timestamp")

        if wrong_parts:
            message += id_ + ", ".join(wrong_parts) + "."
            return message
        else:
            return True

    @classmethod
    def test_oioption_optionoi(cls, data, stream_data):
        """OI option structure tester for dynamic keys."""
        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        message = f"{id}, Wrong parts:"

        is_timestamp = isinstance(data.get('timestamp'), float)

        wrong_parts = []
        
        for key, value in data.items():
            if key == "timestamp":
                continue
            if not isinstance(value, dict):
                wrong_parts.append(f"{key} (not a dict)")
                continue
            if not isinstance(value.get('symbol'), str):
                wrong_parts.append(f"{key}.symbol")
            if not isinstance(value.get('strike'), float):
                wrong_parts.append(f"{key}.strike")
            if not isinstance(value.get('days_left'), float):
                wrong_parts.append(f"{key}.days_left")
            if not isinstance(value.get('oi'), float):
                wrong_parts.append(f"{key}.oi")
            if not isinstance(value.get('price'), float):
                wrong_parts.append(f"{key}.price")

        if not is_timestamp:
            wrong_parts.append("timestamp")

        if wrong_parts:
            message += id_ + ", ".join(wrong_parts) + "."
            return message
        else:
            return True

    @classmethod
    def test_funding(cls, data, stream_data):
        """funding structure tester for dynamic keys."""
        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        message = f"{id}, Wrong parts:"

        is_timestamp = isinstance(data.get('timestamp'), float)

        wrong_parts = []
        
        for key, value in data.items():
            if key == "timestamp":
                continue
            if not isinstance(value, dict):
                wrong_parts.append(f"{key} (not a dict)")
                continue
            if not isinstance(value.get('funding'), str):
                wrong_parts.append(f"{key}.funding")

        if not is_timestamp:
            wrong_parts.append("timestamp")

        if wrong_parts:
            message += id_ + ", ".join(wrong_parts) + "."
            return message
        else:
            return True

    @classmethod
    def test_gta_tta_ttp(cls, data, stream_data):
        """funding structure tester for dynamic keys."""
        id_ = stream_data.get("id_ws") or stream_data.get("id_api")
        message = f"{id}, Wrong parts:"

        is_timestamp = isinstance(data.get('timestamp'), float)

        wrong_parts = []

        possible_metrics = [
            "tta_long_ratio", "tta_short_ratio", "tta_ratio",
            "ttp_long_ratio", "ttp_short_ratio", "ttp_ratio",
            "gta_long_ratio", "gta_short_ratio", "gta_ratio",
            "ttp_size_ratio", "tta_size_ratio", "gta_size_ratio"
        ]

        for key, value in data.items():
            if key == "timestamp":
                continue
            if not isinstance(value, dict):
                wrong_parts.append(f"{key} (not a dict)")
                continue

            valid_metrics = any(isinstance(value.get(metric), float) for metric in possible_metrics)
            if not valid_metrics:
                wrong_parts.append(f"{key}.None of the required metrics are valid")


        if not is_timestamp:
            wrong_parts.append("timestamp")

        if wrong_parts:
            message += id_ + ", ".join(wrong_parts) + "."
            return message
        else:
            return True

    @classmethod
    def find_testing_method(cls, objective, inst_type):
        """ finds testing method"""
        if objective in ["trades", "liquidations"]:
            return cls.test_trades_liquidations
        if objective in ["depth"]:
            return cls.test_depth
        if objective in ["funding"]:
            return cls.test_funding
        if objective in ["oi"] and inst_type != "option":
            return cls.test_oi
        if objective in ["oi", "oioption", "optionoi"] and inst_type == "option":
            return cls.test_oioption_optionoi
        if objective in ["oifunding", "fundingoi"] and inst_type != "option":
            return cls.test_oifunding
        if objective in ["gta", "tta", "ttp"]:
            return cls.test_gta_tta_ttp

    @staticmethod
    def open_json_file(path):
        with open(path, 'r') as file:
            return json.load(file)

    @classmethod
    def create_testing_object(cls, streams_data):
        """ create dictionry that contains the the data, the function that processes the data and its tester """
        
        testing_object = []
        for stream_data in streams_data:

            exchange = stream_data.get("exchange")
            objective = stream_data.get("objective") or stream_data.get("objectives")
            inst_type = stream_data.get("instType") or stream_data.get("instTypes")
            path_json = parent_dir+f"\\sample_data\\raw\\api\\{exchange}\\{stream_data.get('id_api')}.json" or parent_dir+f"\\sample_data\\raw\\ws\\{exchange}\\{stream_data.get('id_ws')}.json"
            id_ = stream_data.get("id_ws") or stream_data.get("id_api")
            data_method = partial(cls.open_json_file , path_json)
            tester = cls.find_testing_method(objective, inst_type)
            
            method = stream_data.get("on_message_method_api") or stream_data.get("on_message_method_ws")
            
            testing_object.append({"id" : id_, "data_method" : data_method, "method" : method, "tester" : tester})

            if "id_api_2" in stream_data:
                path_api_2 = parent_dir+f"\\sample_data\\raw\\api_2\\{exchange}\\{stream_data.get('id_api_2')}.json"
                id_ =  stream_data.get("id_api_2")
                data_method = partial(cls.open_json_file , path_api_2)
                method = stream_data.get("on_message_method_api_2")
                testing_object.append({"id" : id_, "data_method" : data_method, "method" : method, "tester" : tester})

        return testing_object

    @classmethod
    def create_test_method(cls, data_method, method, tester):
        """Factory to create a test method."""
        async def test_method(self):
            results = []
            for data in data_method():
                try:
                    rrr = await method(data)
                    result = tester(rrr)
                except Exception:
                    result = False
                results.append(result)
            true_count = results.count(True)
            total_count = len(results)
            self.assertTrue(true_count >= cls.fail_threshold * total_count, f"Only {true_count}/{total_count} ({(true_count/total_count)*100:.2f}%) passed")
        return test_method

    @classmethod
    def add_methods_to_class(cls, methods):
        """
        Adds methods to the given class.

        :param cls: The class to which methods will be added.
        :param methods: A dictionary where keys are method names and values are the method functions.
        """
        for name, method in methods.items():
            setattr(cls, name, method)

    @classmethod
    def add_testing_methods(cls, test_mapping):
        """Creates a test case class dynamically from a mapping."""
        
        test_mapping = cls.create_testing_object(cls.streams_data)
        
        for methods_stack in test_mapping:
            testing_method = cls.create_test_method(methods_stack.get("data_method"), methods_stack.get("method"), methods_stack.get("tester"))
            cls.add_methods_to_class(testing_method)

