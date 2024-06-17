# from ProcessCenter.tests.dataflow import _test_flow, test_mergers
from streams import streams_data
from ProcessCenter.tests.test_messageProcess import MessageProcessTester
import asyncio
import unittest

# market_state = {
#     "BTCUSD_PERP@perpetual@binance" : {"price" : 70000},
#     "BTCUSDT@perpetual@binance" : {"price" : 70000},
#     "BTCUSDT@perpetual@bybit" : {"price" : 70000},
#     "BTCUSD@perpetual@bybit" : {"price" : 70000}
#     }



# async def aaaa():
#     tests = []
#     for stream_data in streams_data:
#         try:
#             test_class = _test_flow(stream_data, market_state)
#         except Exception as e:
#             print(e)
#         tasks = await test_class.cereate_tasks()
#         for task in tasks:
#             tests.append(task)
#     await asyncio.gather(*tests, return_exceptions=True)


message_test = MessageProcessTester()
message_test.setUpClass()



if __name__ == '__main__':
    unittest.main()

# mergers = test_mergers()
# mergers.test_books("perpetual")

# asyncio.run(aaaa())



    
    
    
    