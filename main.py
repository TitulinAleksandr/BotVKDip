from API.VKinderAPI import VKinderAPI as API
from API.VKinderAPI import VkBot
from config import TOKEN_API, TOKEN_BOT
from datetime import datetime

if "__main__" == __name__:
    bot = VkBot(TOKEN_BOT)
    bot.run()

