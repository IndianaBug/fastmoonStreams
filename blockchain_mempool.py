from scrapy import Spider
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class BlockchainMempoolSpider(Spider):
    name = 'blockchain_mempool'
    start_urls = ['https://www.blockchain.com/explorer/mempool/btc']

    def __init__(self):
        options = Options()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)


    def parse(self, response):
        # Extract information from the dynamic page using Splash response data
        #transactions = response.css('div.sc-7b53084c-1.czXdjN')
        self.driver.get(response.url)

        target_div = self.driver.find_element(By.CSS_SELECTOR, '.sc-7b53084c-1 czXdjN')

        print(target_div.get_attribute('outerHTML'))

        yield target_div.get_attribute('outerHTML')

        # for transaction in transactions:
        #     hash_value = transaction.css('.sc-35e7dcf5-6 GfnCE::text').get()
        #     time = transaction.css('.sc-35e7dcf5-7 fFAyKv::text').get()
        #     amount_btc = transaction.css('.sc-35e7dcf5-13 isCUBz::text').get()
        #     value_usd = transaction.css('.sc-35e7dcf5-14 bbQxqN::text').get()

        #     transaction_details = {
        #         'hash': hash_value.split()[-1] if hash_value else None,
        #         'time': time.split()[-1] if time else None,
        #         'amount_btc': amount_btc.split()[-1] if amount_btc else None,
        #         'value_usd': value_usd.split()[-1] if value_usd else None,
        #     }
        #     print(transaction_details)
            # yield transaction_details