import requests

faust_metrics_url = 'http://localhost:6066/metrics'
try:
    response = requests.get(faust_metrics_url)
    response.raise_for_status()  # This will raise an exception for HTTP error codes
    metrics_data = response.json()
    print(metrics_data)
except requests.exceptions.HTTPError as errh:
    print("Http Error:", errh)
except requests.exceptions.ConnectionError as errc:
    print("Error Connecting:", errc)
except requests.exceptions.Timeout as errt:
    print("Timeout Error:", errt)
except requests.exceptions.RequestException as err:
    print("OOps: Something Else", err)



# Worker Health Metrics:
# worker_status: Status of the Faust worker (e.g., running, stopped, crashed).
# worker_restart_count: Number of times the worker has restarted.
# worker_uptime: Duration for which the worker has been running.
# Processing Metrics:
# message_processing_rate: Rate at which messages are processed by the worker.
# message_latency: Latency or processing time for messages.
# message_error_count: Count of messages that resulted in errors during processing.
# Resource Utilization Metrics:
# cpu_usage: CPU usage of the worker process.
# memory_usage: Memory usage of the worker process.
# thread_count: Number of threads used by the worker.
# Partition Assignment Metrics:
# assigned_partitions: Number of partitions assigned to the worker.
# assigned_topics: Number of topics assigned to the worker.
# Internal Faust Metrics:
# actor_spawned: Number of actors spawned by the worker.
# actor_active: Number of active actors.
# actor_died: Number of actors that have died.