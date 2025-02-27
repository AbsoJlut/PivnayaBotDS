import os
import asyncio
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import logging

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота
intents = disnake.Intents.all()
bot = commands.Bot(
    command_prefix="*",  # Префикс команд задаётся напрямую
    intents=intents,
    help_command=None  # Отключаем стандартную команду help
)

# Событие on_ready
@bot.event
async def on_ready():
    activity = disnake.Activity(
        type=disnake.ActivityType.watching,
        name="/help | Пивная🍻"
    )
    await bot.change_presence(status=disnake.Status.online, activity=activity)
    logger.info(f"=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n"
                f"Бот запущен\n"
                f"Name: {bot.user.name}#{bot.user.discriminator}\n"
                f"ID: {bot.user.id}\n"
                f"=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=")

# Обработка ошибок команд
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Команда не найдена. Используйте `/help` для списка команд.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("У вас недостаточно прав для выполнения этой команды.")
    else:
        logger.error(f"Ошибка в команде {ctx.command}: {error}")
        await ctx.send("Произошла ошибка при выполнении команды.")

# Обработка общих ошибок
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Ошибка в событии {event}: {args}, {kwargs}")

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
    # "cogs.warn",  # /warn
    # "cogs.warns",  # /warns
    "cogs.twitch_notifier",  # уведомлений о стримах
    "cogs.welcome",  # уведомлений о стримах
    "cogs.giveaway",  # розыгрыши
    "cogs.private_voice"  # создание приватных каналов
]

for cog in cogs:
    try:
        bot.load_extension(cog)
        logger.info(f"Загружен ког: {cog}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке кога {cog}: {e}")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
