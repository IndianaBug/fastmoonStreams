import aiohttp
import asyncio

token = "4a5d7e79d937913b9345c41fc6c217de363afe6b"


async def fetch_crypto_panic():
    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={token}&public=true&currencies=BTC,USDT,USDC,ETH,BNB,OKB&region=en'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    crypto_panic_data = await fetch_crypto_panic()
    for result in crypto_panic_data['results']:
        print(result)

if __name__ == '__main__':
    asyncio.run(main())