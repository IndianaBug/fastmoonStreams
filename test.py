import requests

# Replace this URL with the actual API endpoint you want to request
api_url = "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=1000"

# Make a GET request
response = requests.get(api_url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Print the JSON response
    data = response.json()
else:
    # Print an error message if the request was not successful
    print(f"Error: {response.status_code}")


print(data)