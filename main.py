from vk_tools.VKinderAPI import VKinderAPI as API
from vk_tools.VKinderAPI import VkBot
from config import TOKEN_API, TOKEN_BOT
from datetime import datetime

if "__main__" == __name__:
    bot = VkBot(TOKEN_BOT)
    bot.run()

