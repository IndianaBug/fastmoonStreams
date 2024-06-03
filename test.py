import json

data = "C:\\coding\\fastmoon\\fastmoonStreams\\jsondata\\raw\\ws\\bingx\\bingx_ws_spot_trades_btcusdt.json"
data = "C:\\coding\\fastmoon\\fastmoonStreams\\sample_data\\raw\\ws\\deribit\\deribit_ws_future_tradesagg_btc.json"
data = json.dumps(json.loads(open(data, "r").read())[0])

from ProcessCenter.MessageProcessor import on_message
import asyncio

processor = on_message()
a = asyncio.run(processor.deribit_ws_future_perpetual_linear_inverse_option_trades_tradesagg_liquidations(data, {}, {"exchange_symbols":["BTC_USDT"]}))

print(a)
