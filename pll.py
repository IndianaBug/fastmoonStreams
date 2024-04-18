import subprocess
import time
import os

def start_single_server():

    sart_command = "chmod -R +x /workspaces/fastmoonStreams/kafka"

    zookeeper_command = r"/workspace/fastmoonStreams/kafka/bin/zookeeper-server-start.sh /workspace/fastmoonStreams/kafka/config/zookeeper.properties"
    broker0_command = r"/workspace/fastmoonStreams/kafka/bin/kafka-server-start.sh /workspace/fastmoonStreams/kafka/config/server.properties"
    
    # zookeeper_command = r"/workspaces/fastmoonStreams/kafka/bin/zookeeper-server-start.sh /workspaces/fastmoonStreams/kafka/config/zookeeper.properties"
    # broker0_command = r"/workspaces/fastmoonStreams/kafka/bin/kafka-server-start.sh /workspaces/fastmoonStreams/kafka/config/server.properties"

    # start_producer_command = "python producer_books.py"
    # start_consumer_command = r"faust -A consumer_books worker -l info --web-port 6066"
    # start_trading_command = "python app.py" 

    for command in [sart_command, zookeeper_command, broker0_command]:
            subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
            time.sleep(2)

start_single_server()
