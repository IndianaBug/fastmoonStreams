import requests, json
import os, sys
import os
import sys
from urls import built_jwt_api

token = build_jwt()

import http.client
import json

conn = http.client.HTTPSConnection("api.coinbase.com")
payload = ''
headers = {
    "Authorization": f"Bearer {token}",
  'Content-Type': 'application/json'
}
conn.request("GET", "/api/v3/brokerage/product_book?product_id=BTC-USD", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))