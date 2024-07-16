#!/bin/bash

# Set environment variables
export COINBASE_SECRET="-----BEGIN EC PRIVATE KEY-----
YOUR_PRIVATE_KEY
-----END EC PRIVATE KEY-----"
export COINBASE_API="your_key"
export KUCOIN_API="your_key"
export KUCOIN_PASS="your_key"
export KUCOIN_SECRET="your_key"
export ELASTIC_PASSWORD="your_key"
export TELEGRAM_BOT_TOKEN="your_key"
export TELEGRAM_CHAT_ID="your_key"
export ELASTIC_CERTIFICATE_FINGERPRINT="your_key"
export ELASTIC_KIBANA_ENROLMENT_TOKEN="your_key"
export ELASTIC_NODES_ENROLMENT_TOKEN="your_key"

# Print a message to confirm the variables have been set
echo "Environment variables have been set successfully."