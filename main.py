import os
import asyncio
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

intents = disnake.Intents.default()
intents.members = True  # Включаем интент для отслеживания участников

load_dotenv()
bot = commands.Bot(command_prefix="*", intents=disnake.Intents.all())

@bot.event
async def on_ready():
    activity = disnake.Activity(type=disnake.ActivityType.watching, name="/help | Пивная🍻")
    await bot.change_presence(status=disnake.Status.online, activity=activity)
    logger.info(f"=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\nБот запущен\nName: {bot.user.name}#{bot.user.discriminator}\nID: {bot.user.id}\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

# Загрузка когов
cogs = [
    "cogs.ping",  # /say
    "cogs.mute",  # /mute
    "cogs.unmute",  # /unmute
    "cogs.announce",  # /announce
    "cogs.info",  # /info
    "cogs.UserInfo",  # /user
    "cogs.clearchat",  # /clearchat
    "cogs.say",  # /say
    "cogs.ticket_system",  # /ticket
    "cogs.moder",  # /moder
    "cogs.randbuild",  # /randombuild
    "cogs.Roles",  # /Roles
    "cogs.Help",  # /help
    "cogs.Roll",  # /roll
    "cogs.avatar",  # /avatar
    "cogs.warn",  # /warn
    # "cogs.warns",  # /warns
    "cogs.twitch_notifier",  # уведомлений о стримах
    "cogs.welcome"  # уведомлений о стримах
]

for cog in cogs:
    try:
        bot.load_extension(cog)
        logger.info(f"Загружен ког: {cog}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке кога {cog}: {e}")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
