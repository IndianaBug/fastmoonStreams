from telegram import Bot
import logging

class TelegramHandler(logging.Handler):
    """ Sends messages to a telegram channel"""
    def __init__(self, token, chat_id):
        super().__init__()
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def emit_message(self, record):
        """ sends message to a telegram channel"""
        log_entry = self.format(record)
        await self.bot.send_message(chat_id=self.chat_id, text=log_entry)