import requests
from producerAPI import miliseconds_to_strftime
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

# Build the URL for the API call
url = "https://www.okx.com/api/v5/public/insurance-fund?instType=SWAP&instFamily=BTC-USD&limit=1"

url = "https://www.okx.com/api/v5/public/insurance-fund?instType=FUTURES&instFamily=BTC-USD&limit=1"
url = "https://www.okx.com/api/v5/public/insurance-fund?instType=FUTURES&instFamily=BTC-USDT&limit=1"

url = "https://www.okx.com/api/v5/public/insurance-fund?instType=OPTION&instFamily=BTC-USD&limit=1"

url = "https://www.okx.com/api/v5/public/insurance-fund?instType=MARGIN&ccy=BTC&limit=1"
url = "https://www.okx.com/api/v5/public/insurance-fund?instType=MARGIN&ccy=USDT&limit=1"
url = "https://www.okx.com/api/v5/public/insurance-fund?instType=SWAP&instFamily=BTC-USDT&limit=1"

r = requests.get(url)
if r.status_code == 200:
    data = r.json()
else:
    data = r.status_code

print(data)