#!/bin/bash

/workspaces/fastmoonStreams/kafka/bin/zookeeper-server-start.sh /workspaces/fastmoonStreams/kafka/config/zookeeper.properties
/workspaces/fastmoonStreams/kafka/bin/kafka-server-start.sh /workspaces/fastmoonStreams/kafka/config/server.properties
# python clauncher.py
# python plauncher.py

# chmod +x run_modules.sh
# ls -l /workspaces/fastmoonStreams/kafka/bin/zookeeper-server-start.sh
# ls -l /workspaces/fastmoonStreams/kafka/bin/kafka-server-start.sh