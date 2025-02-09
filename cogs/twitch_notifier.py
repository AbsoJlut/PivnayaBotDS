import os
import disnake
from disnake.ext import commands, tasks
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv
from babel.dates import format_datetime
from datetime import datetime
import pytz
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TwitchNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch = Twitch(os.getenv('TWITCH_CLIENT_ID'), os.getenv('TWITCH_CLIENT_SECRET'))
        self.channel_id = int(os.getenv('TWITCH_CHANNEL_ID'))
        self.streamer_names = os.getenv('TWITCH_STREAMER_NAMES').split(',')
        self.streamer_role_fanat = int(os.getenv('TWITCH_ROLE_FANAT'))
        self.is_streaming = {name: False for name in self.streamer_names}
        self.check_stream.start()

    async def send_stream_notification(self, stream):
        user_profile_image_url = None
        async for user in self.twitch.get_users(logins=[stream.user_login]):
            user_profile_image_url = user.profile_image_url
            break

        # Получаем информацию об игре
        game_image_url = None
        async for game in self.twitch.get_games(names=[stream.game_name]):
            game_image_url = game.box_art_url.format(width=130, height=170)
            break

        # Преобразуем время начала стрима в московское время
        moscow_tz = pytz.timezone('Europe/Moscow')
        stream_started_at_moscow = stream.started_at.astimezone(moscow_tz)

        embed = disnake.Embed(
            title=f"{stream.title}",
            color=disnake.Color.purple()
        )
        embed.set_author(name=stream.user_name, icon_url=user_profile_image_url)
        embed.add_field(name="Игра", value=stream.game_name, inline=True)
        embed.set_image(url=stream.thumbnail_url.format(width=1920, height=1080))
        if game_image_url:
            embed.set_thumbnail(url=game_image_url)
        embed.set_footer(text=f"Начало стрима • {format_datetime(stream_started_at_moscow, 'EEEE, d MMMM y, HH:mm', locale='ru')}")
        message_content = f"<@&{self.streamer_role_fanat}>, {stream.user_name} запустил стрим по игре {stream.game_name}! Присоединяйся!! 💞\n\nhttps://twitch.tv/{stream.user_name}"
        button = disnake.ui.Button(
            style=disnake.ButtonStyle.link,
            label="Смотреть стрим",
            url=f"https://www.twitch.tv/{stream.user_name}"
        )
        view = disnake.ui.View()
        view.add_item(button)
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            await channel.send(content=message_content, embed=embed, view=view)
        else:
            logger.error(f"Канал с ID {self.channel_id} не найден.")

    async def check_stream_once(self):
        try:
            await self.twitch.authenticate_app([])
            for streamer_name in self.streamer_names:
                is_streaming_now = False
                async for stream in self.twitch.get_streams(user_login=[streamer_name]):
                    is_streaming_now = True
                    if not self.is_streaming[streamer_name]:
                        self.is_streaming[streamer_name] = True
                        await self.send_stream_notification(stream)
                    break  # Exit the loop after finding the first stream

                if not is_streaming_now:
                    self.is_streaming[streamer_name] = False
        except Exception as e:
            logger.error(f"Ошибка при проверке стрима: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_stream_once()

    @tasks.loop(minutes=1)
    async def check_stream(self):
        await self.check_stream_once()

    @check_stream.before_loop
    async def before_check_stream(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(TwitchNotifier(bot))