import subprocess
import time
import os

def start_single_server():

    zookeeper_command = r"/home/ec2-user/kafka/bin/zookeeper-server-start.sh /home/ec2-user/kafka/config/zookeeper.properties "
    broker0_command = r"/home/ec2-user/kafka/bin/kafka-server-start.sh /home/ec2-user/kafka/config/server.properties"

    topic_commands = [
        [

            r"/home/ec2-user/kafka/bin/kafka-topics.sh",
            "--bootstrap-server", "localhost:9092",
            "--topic", "binance",
            "--create",
            "--partitions", "2",
            "--replication-factor", "1"
        ],
        [
            r"/home/ec2-user/kafka/bin/kafka-topics.sh",
            "--bootstrap-server", "localhost:9092",
            "--topic", "bitget",
            "--create",
            "--partitions", "2",
            "--replication-factor", "1"
        ],
        [
            r"/home/ec2-user/kafka/bin/kafka-topics.sh",
            "--bootstrap-server", "localhost:9092",
            "--topic", "spreads",
            "--create",
            "--partitions", "2",
            "--replication-factor", "1"
        ],
        [
            r"/home/ec2-user/kafka/bin/kafka-configs.sh",
            "--bootstrap-server", "localhost:9092",
            "--entity-type", "topics",
            "--entity-name", "binance",
            "--alter",
            "--add-config", "retention.ms=600000"
        ],
        [
            r"/home/ec2-user/kafka/bin/kafka-configs.sh",
            "--bootstrap-server", "localhost:9092",
            "--entity-type", "topics",
            "--entity-name", "bitget",
            "--alter",
            "--add-config", "retention.ms=600000"
        ],
        [
            r"/home/ec2-user/kafka/bin/kafka-configs.sh",
            "--bootstrap-server", "localhost:9092",
            "--entity-type", "topics",
            "--entity-name", "spreads",
            "--alter",
            "--add-config", "retention.ms=600000"
        ]
    ]

    start_producer_command = "python producer_books.py"
    start_consumer_command = r"faust -A consumer_books worker -l info --web-port 6066"
    start_trading_command = "python app.py" 

    for command in [zookeeper_command, broker0_command, *topic_commands, start_producer_command, start_consumer_command, start_trading_command]:
        if command in [zookeeper_command, broker0_command, start_producer_command, start_consumer_command, start_trading_command]:
            if command in [start_producer_command, start_consumer_command]:
                sleep = 15
            else:
                sleep = 8
            subprocess.Popen(['start', 'cmd', '/k', command], shell=True)
            time.sleep(sleep)
        else:
            subprocess.run(command)
            time.sleep(2)



start_single_server()
#start_double_server()