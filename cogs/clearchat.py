import disnake
from disnake.ext import commands
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClearChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Удаляет указанное количество сообщений из текущего канала (Админская команда)")
    @commands.has_permissions(manage_messages=True)
    async def clearchat(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        amount: int,
        user: disnake.User = None
    ):
        try:
            # Проверка на разумное количество сообщений
            if amount <= 0:
                await interaction.response.send_message("Количество сообщений должно быть больше 0.", ephemeral=True)
                return
            if amount > 100:
                await interaction.response.send_message("Можно удалить не более 100 сообщений за раз.", ephemeral=True)
                return

            # Уведомление о начале удаления
            await interaction.response.send_message(f"Удаляю сообщения...", ephemeral=True)

            # Функция для фильтрации сообщений по пользователю
            def check_user(message):
                return user is None or message.author == user

            # Удаление сообщений
            deleted = await interaction.channel.purge(limit=amount + 1, check=check_user)  # +1 для учёта команды

            # Уведомление о завершении
            if user:
                await interaction.followup.send(content=f"Удалено {len(deleted) - 1} сообщений от пользователя {user.name}.", ephemeral=True)
            else:
                await interaction.followup.send(content=f"Удалено {len(deleted) - 1} сообщений.", ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде clearchat: {e}")
            await interaction.response.send_message("Произошла ошибка при удалении сообщений.", ephemeral=True)

    @clearchat.error
    async def clearchat_error(self, interaction: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("У вас недостаточно прав для использования этой команды.", ephemeral=True)
        else:
            await interaction.response.send_message("Произошла неизвестная ошибка.", ephemeral=True)

def setup(bot):
    bot.add_cog(ClearChat(bot))