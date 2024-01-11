from selenium import webdriver
from selenium.webdriver.firefox.service import Service

# Specify the path to the geckodriver executable with the new variable name
custom_geckodriver_path = 'selenium_driver/geckodriver'  # Change this path if necessary

# Specify the path to the Firefox binary
firefox_binary_path = '/path/to/firefox/firefox'  # Change this path if necessary

# Set up the Firefox webdriver with geckodriver and Firefox binary path
service = Service(custom_geckodriver_path)
firefox_options = webdriver.FirefoxOptions()
firefox_options.binary_location = firefox_binary_path
driver = webdriver.Firefox(service=service, options=firefox_options)

# Open a website (you can change the URL)
driver.get("https://www.example.com")

# Close the webdriver
driver.quit()