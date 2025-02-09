import disnake
from disnake.ext import commands
import random
import logging
import os
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env
load_dotenv()

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_messages = [
            "Добро пожаловать, {member.mention}! Рады видеть тебя здесь!",
            "Привет, {member.mention}! Добро пожаловать на наш сервер!",
            "Здравствуй, {member.mention}! Надеемся, тебе здесь понравится!",
            "{member.mention} уже здесь.",
            "Знакомьтесь, это {member.mention}!",
            "Дикий {member.mention} появился.",
            "Ура, {member.mention} теперь с нами!",
            "{member.mention} приземляется на сервере.",
            "Рады тебя видеть, {member.mention}.",
            "{member.mention} уже с нами!",
            "Рады встрече, {member.mention}.",
            "Добро пожаловать, {member.mention}. Мы ждали тебя ( ͡° ͜ʖ ͡°)",
            "Живая легенда {member.mention} показалась!!",
            "С прибытием, {member.mention}! Рады видеть тебя среди нас!",
            "Приветствуем тебя, {member.mention}! Добро пожаловать!"
        ]
        self.welcome_titles = [
            "Новый участник!",
            "К нам присоединился {member.name}!",
            "Свежая кровь!",
            "Новичок на борту!",
            "Добро пожаловать в нашу компанию!",
            "Новый друг появился!",
            "Сервер пополнился!",
            "Новый герой прибыл!",
            "Рады видеть тебя, {member.name}!",
            "Приветствуем нового участника!"
        ]
        self.welcome_gifs = [
            "https://media.tenor.com/8keClgrajIcAAAAj/umamusumeprettyderby.gif",  # Пример гифки 1
            "https://media1.tenor.com/m/aM3HmfQbEfQAAAAC/megumin-yunyun.gif",  # Пример гифки 2
            "https://media1.tenor.com/m/U20VhSWkO-EAAAAd/anime-cheers-anime-alcohol.gif",  # Пример гифки 3
            "https://media1.tenor.com/m/BBTZa4b7Li8AAAAd/xxl-bean-bag.gif"   # Пример гифки 4
        ]
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID"))  # ID канала из .env

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            channel = self.bot.get_channel(self.welcome_channel_id)
            if channel:
                message = random.choice(self.welcome_messages).format(member=member)
                title = random.choice(self.welcome_titles).format(member=member)
                gif_url = random.choice(self.welcome_gifs)  # Выбираем случайную гифку

                embed = disnake.Embed(
                    title=title,
                    description=message,
                    color=disnake.Color.green()
                )
                embed.set_image(url=gif_url)  # Устанавливаем случайную гифку
                await channel.send(embed=embed)
            else:
                logger.error(f"Канал с ID {self.welcome_channel_id} не найден.")
        except Exception as e:
            logger.error(f"Ошибка при отправке приветственного сообщения: {e}")

def setup(bot):
    bot.add_cog(Welcome(bot))