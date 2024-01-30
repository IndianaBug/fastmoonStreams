import requests
import json
from utilis import books_snapshot


a = books_snapshot("coinbase", "spot", "btcusd", 100)

print(type(json.loads(a["response"])))