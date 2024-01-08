import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets

key_name = "organizations/b6a02fc1-cbb0-4658-8bb2-702437518d70/apiKeys/938c15ca-cbd4-473d-9864-2e3563da54f7" 
key_secret = "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIJuCG6lX0FjTnsjnYuYbFzn0Xky8qXWVoqpx5h4VFLL5oAoGCCqGSM49\nAwEHoUQDQgAEcii4LTxmIknSaA7JgBHK+u6KiOx672ZXSXcvwjlWrlynob6y/sPt\ntWO0tXV07MAEXy+8GAfsKd6VyAZBce11eg==\n-----END EC PRIVATE KEY-----\n" 
service_name = "public_websocket_api"

def build_jwt():
    private_key_bytes = key_secret.encode('utf-8')
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
    jwt_payload = {
        'sub': key_name,
        'iss': "coinbase-cloud",
        'nbf': int(time.time()),
        'exp': int(time.time()) + 60,
        'aud': [service_name],
    }
    jwt_token = jwt.encode(
        jwt_payload,
        private_key,
        algorithm='ES256',
        headers={'kid': key_name, 'nonce': secrets.token_hex()},
    )
    return jwt_token
