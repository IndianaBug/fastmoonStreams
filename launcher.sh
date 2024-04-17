#!/bin/bash
chmod -R +x /workspaces/fastmoonStreams/kafka

tail -f /workspaces/fastmoonStreams/kafka/bin/zookeeper-server-start.sh /workspaces/fastmoonStreams/kafka/config/zookeeper.properties &
tail -f /workspaces/fastmoonStreams/kafka/bin/kafka-server-start.sh /workspaces/fastmoonStreams/kafka/config/server.properties &
# python clauncher.py
# python plauncher.py

# chmod +x run_modules.sh
# ls -l /workspaces/fastmoonStreams/kafka/bin/zookeeper-server-start.sh
# ls -l /workspaces/fastmoonStreams/kafka/bin/kafka-server-start.sh
# chmod +x /workspaces/fastmoonStreams/kafka/bin/kafka-server-start.sh
# chmod +x /workspaces/fastmoonStreams/kafka/bin/zookeeper-server-start.sh

# chmod -R +x /workspaces/fastmoonStreams/kafka
