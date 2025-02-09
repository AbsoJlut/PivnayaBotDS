import disnake
from disnake.ext import commands
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Получить аватар пользователя")
    async def avatar(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None):
        try:
            # Если пользователь не указан, используем автора команды
            target_user = user or inter.author

            # Получаем URL аватара (включая GIF, если он анимированный)
            avatar_url = target_user.display_avatar.url

            # Создаем Embed
            embed = disnake.Embed(title=f"Аватар {target_user.name}", color=disnake.Color.blurple())
            embed.set_image(url=avatar_url)
            embed.set_footer(text=f"Запрошено {inter.author.name}", icon_url=inter.author.display_avatar.url)

            # Отправляем Embed
            await inter.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде avatar: {e}")
            await inter.response.send_message("Произошла ошибка при получении аватара.", ephemeral=True)

def setup(bot):
    bot.add_cog(Avatar(bot))