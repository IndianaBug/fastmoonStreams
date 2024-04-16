import subprocess
import time
import os

def start_server_windows():

    zookeeper_command = r"C:/coding/SatoshiVault/kafka/bin/zookeeper-server-start.sh C:/coding/SatoshiVault/kafka/config/zookeeper.properties"
    broker0_command = r"C:/coding/SatoshiVault/kafka/bin/kafka-server-start.sh C:/coding/SatoshiVault/kafka/config/server.properties"
    start_producer_command = "python producers/main.py"
    start_consumer_command = r"faust -A C:/coding/SatoshiVault/producers/consumer.py worker -l info --web-port 6066"

    for command in [zookeeper_command, broker0_command, start_producer_command, start_consumer_command]:
        if command in [zookeeper_command, broker0_command, start_producer_command, start_consumer_command,]:
            if command in [start_producer_command, start_consumer_command]:
                sleep = 4
            else:
                sleep = 2
            subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
            time.sleep(sleep)
        else:
            subprocess.run(command)
            time.sleep(2)



start_server_windows()
