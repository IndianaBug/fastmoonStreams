# PowerShell script to set multiple environment variables

$env_vars = @{
    "coinbase_secret" = @"
-----BEGIN EC PRIVATE KEY-----
Private_KEY
-----END EC PRIVATE KEY-----
"@
    "coinbase_api" = "your_key"
    "kucoin_api" = "your_key"
    "kucoin_pass" = "your_key"
    "kucoin_secret" = "your_key"
    "elastic_password" = "your_key"
    "telegram_bot_token" = "your_key"
    "telegram_chat_id" = "your_key"
    "elastic_certificate_fingerprint" = "your_key"
    "elastic_kibana_enrolment_token" = "your_key"
    "elastic_nodes_enrolment_token" = "your_key"
}

foreach ($key in $env_vars.Keys) {
    [System.Environment]::SetEnvironmentVariable($key, $env_vars[$key], [System.EnvironmentVariableTarget]::User)
}

Write-Output "Environment variables have been set successfully."