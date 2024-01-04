import requests

# # https://www.okx.com/docs-v5/en/#public-data-rest-api-get-index-components
# url = "https://www.okx.com/api/v5/public/economic-calendar"
# params = {}

# r = requests.get(url, params=params)
# if r.status_code == 200:
#     data = r.json()
# else:
#     data = r.status_code

# print(data)
params = {}
#params = {"category": "linear", "symbol": "BTCUSDT", "period": "1d", "limit": 50}
url = "https://api.bybit.com/v5/market/insurance"   # Insurance fund grows as the result of liquidation fees
# url = "https://api.bybit.com/v5/market/account-ratio"
r = requests.get(url, params=params)
if r.status_code == 200:
    data = r.json()
else:
    data = r.status_code

print(data)