import disnake
from disnake.ext import commands
import logging
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Moder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Отправляет сообщение от имени бота в текущий канал с подписью модератора/админа (Админская команда)")
    async def moder(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        message: str,
        reply_to: disnake.Message = None
    ):
        try:
            # Получаем роли из переменной окружения
            moder_roles = list(map(int, os.getenv("MODER_ROLES").split(",")))

            # Проверяем, есть ли у пользователя необходимая роль
            if not any(role.id in moder_roles for role in interaction.author.roles):
                await interaction.response.send_message("У вас недостаточно прав для использования этой команды.", ephemeral=True)
                return

            # Заменяем \n на переносы строк
            message = message.replace("\\n", "\n")

            # Создаем Embed
            emb = disnake.Embed(
                title="Поддержка",
                description=message,
                colour=disnake.Color.magenta()  # Фиксированный цвет (FF00FF в RGB)
            )
            emb.set_footer(
                text=f'Ответ отправлен модератором - {interaction.author.name}',
                icon_url=interaction.author.display_avatar.url
            )

            # Если указан ID сообщения для ответа
            if reply_to:
                try:
                    # Получаем сообщение, на которое нужно ответить
                    target_message = await interaction.channel.fetch_message(reply_to.id)
                    # Отправляем ответ на это сообщение
                    await target_message.reply(embed=emb)
                except disnake.NotFound:
                    await interaction.response.send_message("Сообщение для ответа не найдено.", ephemeral=True)
                    return
            else:
                # Отправляем Embed в текущий канал без ответа
                await interaction.channel.send(embed=emb)

            # Уведомляем пользователя об успешной отправке
            await interaction.response.send_message("Сообщение успешно отправлено!", ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде moder: {e}")
            await interaction.response.send_message("Произошла ошибка при отправке сообщения.", ephemeral=True)

def setup(bot):
    bot.add_cog(Moder(bot))