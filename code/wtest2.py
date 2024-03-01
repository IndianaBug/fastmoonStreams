from urls import AaWS
from utilis2 import AllStreamsByInstrumentS
streams = [
    ["gateio", "perpetual", "btcusdt"],
    ["htx", "perpetual", "btcusdt"],
    ["bingx", "perpetual", "btcusdt"],
    ["bitget", "perpetual", "btcusdt"],
    ["bitget", "spot", "btcusdt"],
    ["mexc", "spot", "btcusdt"],
    ["gateio", "spot", "btcusdt"],
    ["bitget", "spot", "btcusdt"],
    ["htx", "spot", "btcusdt"],
    ["mexc", "perpetual", "btcusdt"],
    ["kucoin", "perpetual", "btcusdt"],
    ["kucoin", "spot", "btcusdt"],
    ["htx", "spot", "btcusdt"],
    ["bingx", "spot", "btcusdt"],
    ["bybit", "spot", "btcusdc"],
    ["deribit", "perpetual", "btcusd"],
]

data = AllStreamsByInstrumentS(streams)

print([x for x in data if x["type"] == "api" and x["obj"] == "depth" and x["exchange"] == "bingx"] + [x for x in data if x["type"] == "api" and x["obj"] != "depth"])
