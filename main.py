from vk_tools.VKinderAPI import VkBot
from config import TOKEN_BOT

if "__main__" == __name__:
    bot = VkBot(TOKEN_BOT)
    bot.run()

