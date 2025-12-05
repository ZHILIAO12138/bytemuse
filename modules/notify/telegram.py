import requests
import telebot
import os

from telebot import apihelper

from app.core.config import temp_folder, Settings
from app.utils.log import logger


class TelegramNotifier:
    bot_token = ''
    chat_id = ''
    bot: telebot.TeleBot = None
    proxies = {}
    headers = {
        'Referer': 'https://www.javbus.com/'
    }
    webhook_url = ''
    spoiler: bool = False
    whitelist: list = []

    def __init__(self, settings: Settings):
        if settings.TELEGRAM_BOT_TOKEN:
            try:
                self.bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)
                self.chat_id = settings.TELEGRAM_CHAT_ID
                apihelper.proxy = {'https': settings.PROXY}
                self.proxies = {
                    "http": settings.PROXY,
                    "https": settings.PROXY
                }
                self.spoiler = settings.TELEGRAM_SPOILER
                if settings.TELEGRAM_WHITELIST:
                    self.whitelist = [int(item) for item in settings.TELEGRAM_WHITELIST.split(',') if item]

            except Exception as e:
                logger.error(f"TG机器人创建失败：{e}")

    def send_text_message(self, from_chat_id=None, text=None):
        if self.bot:
            try:
                if from_chat_id:
                    self.bot.send_message(from_chat_id, text)
                else:
                    self.bot.send_message(self.chat_id, text)
            except Exception as e:
                logger.error(f"发送telegram消息失败：{e}")

    def reply_text_message(self, from_chat_id=None, text=None, message_id=None):
        if self.bot:
            try:
                self.bot.send_message(from_chat_id, text, reply_to_message_id=message_id)
            except Exception as e:
                logger.error(f"发送telegram消息失败：{e}")

    def send_photo_message(self, photo_url, caption=None):
        if self.bot:
            try:
                photo_path = self.download_image(photo_url)
                if photo_path:
                    with open(photo_path, 'rb') as photo_file:
                        self.bot.send_photo(self.chat_id, photo_file, has_spoiler=self.spoiler, caption=caption)
            except Exception as e:
                logger.error(f"发送telegram消息失败： {e}")

    def download_image(self, url):
        try:
            response = requests.get(url, proxies=self.proxies, stream=True, headers=self.headers)
            if response.ok:
                photo_path = os.path.join(temp_folder, url.split("/")[-1])
                with open(photo_path, 'wb') as out_file:
                    out_file.write(response.content)
                return photo_path
            else:
                logger.error(f"下载图片失败 {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"下载图片失败 {e}")
            return None
