# import json
# import pickle
# import numpy as np

# staging_data_file_path = "C:\\coding\\fastmoon\\fastmoonStreams\\sample_data\\staging_data.json"
# staging_data = json.load(open(staging_data_file_path, "r"))

# raw_data_file_path = "C:\\coding\\fastmoon\\fastmoonStreams\\sample_data\\raw_data.pkl"
# with open(raw_data_file_path, 'rb') as file:
#     raw_data = pickle.load(file)

# for k, i in raw_data.get("merged_dataframes").items():
#     print("---")
#     print("---")
#     print(k)
#     print("---")
#     print("---")
#     print("---")
#     print(i)

# objective:
# -- Create a logger
# --- add module levels and all of the stuff dynamically. I mean, to have a nice understanding where the log come from.
# --- TimedRotatingFileHandler
# --- loging confings should be in the file # logging.conf:
# --- add a telegram handler
# --- So create a class that instantiates that module logger and all of the stuff.

import asyncio

bot_token = '7246419438:AAHOYcQGOOuajcf82ygRhj0DEqFKTu3LbLI'
bot = Bot(token=bot_token)
channel_id = '-1002197565621'
message = "Hello, this is a test message from my bot!"


import logging
from telegram import Bot
import logging.config
import sys
import os

class TelegramHandler(logging.Handler):
    def __init__(self, token, chat_id):
        super().__init__()
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def emit_message(self, record):
        """ sends message to a telegram channel"""
        log_entry = self.format(record)
        await self.bot.send_message(chat_id=self.chat_id, text=log_entry)


class LoggerSetup:
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup()

    def _setup(self):
        # Load configuration from logging.conf
        logging.config.fileConfig('logging.conf')
        self.logger = logging.getLogger('appLogger')
        
    def get_logger(self):
        return self.logger

# Usage
if __name__ == "__main__":
    # Example of using the logger setup
    logger_setup = LoggerSetup(__name__)
    logger = logger_setup.get_logger()
    
    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')
    logger.error('Error message')
    logger.critical('Critical message')


# import logging

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     filename='logs/app.log',  # Logs to a file
#     filemode='w'  # Write mode
# )

# logger = logging.getLogger(__name__)

# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.critical("This is a critical message")



# log_file = log_file / "logs/producerlogger.log"
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# file_handler = RotatingFileHandler(
#                 log_file, 
#                 maxBytes=maxBytes, 
#                 backupCount=backupCount      
#             )
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)







# import logging

# # Create and configure the root logger
# logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# # Create module-level loggers
# app_logger = logging.getLogger('app')
# module_logger = logging.getLogger('app.module')
# submodule_logger = logging.getLogger('app.module.submodule')

# # Set specific levels
# app_logger.setLevel(logging.DEBUG)
# module_logger.setLevel(logging.INFO)
# submodule_logger.setLevel(logging.ERROR)

# # Add handlers if needed (default is to propagate to root logger's handlers)
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
# app_logger.addHandler(console_handler)

# # Log messages
# app_logger.debug('App logger debug message')
# module_logger.info('Module logger info message')
# submodule_logger.error('Submodule logger error message')





# Handlers
# Handlers are responsible for sending the log messages to their final destination, such as the console, a file, or a remote server. You can add multiple handlers to a logger to send logs to multiple destinations.

# Common Handlers
# StreamHandler: Sends log messages to streams such as sys.stdout or sys.stderr.
# FileHandler: Sends log messages to a file.
# RotatingFileHandler: Sends log messages to a file, with the ability to rotate the log file after reaching a certain size.
# TimedRotatingFileHandler: Sends log messages to a file, with the ability to rotate the log file at certain timed intervals.
# SMTPHandler: Sends log messages via email.
# HTTPHandler: Sends log messages via HTTP to a web server.
# SocketHandler: Sends log messages to a network socket.
# Adding Handlers to a Logger
# Here's an example of adding a StreamHandler and a FileHandler to a custom logger:




# Logging Levels
# Logging levels indicate the severity of the log messages. The standard levels provided by the logging module are:

# DEBUG: Detailed information, typically of interest only when diagnosing problems.
# INFO: Confirmation that things are working as expected.
# WARNING: An indication that something unexpected happened, or indicative of some problem in the near future (e.g., ‘disk space low’). The software is still working as expected.
# ERROR: Due to a more serious problem, the software has not been able to perform some function.
# CRITICAL: A very serious error, indicating that the program itself may be unable to continue running.



# I use elasticsearch database. As I know they have logstash. Can I connect my python logger to logstash? i would be nice if 
# I could make some lerts with this python logger. Finally, can i make a python logger that it puts data in the log 
# file, when the isze reaches threshold it creates a new file. Also names of files should include dates for easier navigation
# also, its better for my software to use logging.conf file in order to make configurations help me to structure that.
# 





# logging.conf:

# ini
# Copy code
# [loggers]
# keys=root,app,module,submodule

# [handlers]
# keys=consoleHandler,fileHandler

# [formatters]
# keys=simpleFormatter

# [logger_root]
# level=WARNING
# handlers=consoleHandler

# [logger_app]
# level=DEBUG
# handlers=consoleHandler
# qualname=app
# propagate=0

# [logger_module]
# level=INFO
# handlers=consoleHandler
# qualname=app.module
# propagate=1

# [logger_submodule]
# level=ERROR
# handlers=consoleHandler
# qualname=app.module.submodule
# propagate=1

# [handler_consoleHandler]
# class=StreamHandler
# level=DEBUG
# formatter=simpleFormatter
# args=(sys.stdout,)

# [handler_fileHandler]
# class=FileHandler
# level=ERROR
# formatter=simpleFormatter
# args=('file.log', 'a')

# [formatter_simpleFormatter]
# format=%(name)s - %(levelname)s - %(message)s








# Custom Alerts with Telegram or Email
# For custom alerts using Telegram or email, you can create custom handlers or use existing libraries to integrate with these services.

# Example: Sending Alerts via Telegram
# You can use the python-telegram-bot library to send alerts to a Telegram chat.

# python
# Copy code
# import logging
# from logging import Handler
# from telegram import Bot

# class TelegramHandler(Handler):
#     def __init__(self, token, chat_id):
#         Handler.__init__(self)
#         self.bot = Bot(token=token)
#         self.chat_id = chat_id

#     def emit(self, record):
#         log_entry = self.format(record)
#         self.bot.send_message(chat_id=self.chat_id, text=log_entry)

# # Create a custom logger
# logger = logging.getLogger('telegram_logger')
# logger.setLevel(logging.ERROR)

# # Create a Telegram handler
# telegram_handler = TelegramHandler(token='your_telegram_bot_token', chat_id='your_chat_id')
# telegram_handler.setLevel(logging.ERROR)

# # Create a formatter and set it for the handler
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# telegram_handler.setFormatter(formatter)

# # Add the handler to the logger
# logger.addHandler(telegram_handler)

# # Log messages
# logger.error('This is an error message that will be sent to Telegram')