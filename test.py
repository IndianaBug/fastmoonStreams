import requests
from datetime import datetime, timedelta

# Current time in milliseconds
current_time_milliseconds = int(datetime.timestamp(datetime.now()) * 1000)

# Time 5 minutes ago in milliseconds
five_minutes_ago = datetime.now() - timedelta(minutes=5)
five_minutes_ago_milliseconds = int(datetime.timestamp(datetime.now() - timedelta(minutes=5)) * 1000)

print(five_minutes_ago_milliseconds)

api_url = "wss://test.deribit.com/ws/api/v2/public"

# Endpoint for book summary by currency
endpoint = "/get_book_summary_by_currency"

# Specify the currency pair (e.g., BTC-USD)
currency_pair = "BTC-USD"

a = {"exchange":"okx", "insType":"STATISTIC_GENERAL", "obj":"calendar", "snapshotInterval":300, "instrument": "integrated", "url" : "https://www.okx.com/api/v5/public/economic-calendar"} # Need authentication


r = requests.get(a['url'])
if r.status_code == 200:
    data = r.json()
else:
    data = r.status_code

print(data)