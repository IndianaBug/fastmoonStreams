import requests
import matplotlib.pyplot as plt

faust_metrics_url = 'http://localhost:6066/metrics'  
response = requests.get(faust_metrics_url)
metrics_data = response.json()

message_processing_rate = metrics_data.get('message_processing_rate', [])

timestamps = [metric['timestamp'] for metric in message_processing_rate]
values = [metric['value'] for metric in message_processing_rate]
plt.plot(timestamps, values)
plt.xlabel('Time')
plt.ylabel('Message Processing Rate')
plt.title('Message Processing Rate Over Time')
plt.show()