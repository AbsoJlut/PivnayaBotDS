import disnake
from disnake.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Мут пользователя на определенное время (Админская команда)")
    async def mute(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        time: int,
        reason: str
    ):
        try:
            # Получаем роли из переменной окружения
            moder_roles = list(map(int, os.getenv("MODER_ROLES").split(",")))

            # Проверяем, есть ли у пользователя необходимая роль
            if not any(role.id in moder_roles for role in interaction.author.roles):
                await interaction.send("У вас недостаточно прав для использования этой команды.", ephemeral=True)
                return

            # Список идентификаторов ролей, которые нельзя мутить
            restricted_roles = moder_roles  # Используем те же роли, что и для модераторов

            # Проверка, имеет ли указанный пользователь одну из запрещенных ролей
            if any(role.id in restricted_roles for role in user.roles):
                await interaction.send(f"Нельзя мутить пользователя с ролью {', '.join([role.name for role in user.roles if role.id in restricted_roles])}!", ephemeral=True)
                return

            # Получаем роль мута и AFK канал из переменных окружения
            mute_role_id = int(os.getenv("MUTE_ROLE_ID"))
            afk_channel_id = int(os.getenv("AFK_CHANNEL_ID"))

            mute_role = user.guild.get_role(mute_role_id)  # Роль мута
            afk_channel = user.guild.get_channel(afk_channel_id)  # AFK канал

            if not mute_role:
                await interaction.send("Роль мута не найдена!", ephemeral=True)
                return

            if not afk_channel:
                await interaction.send("AFK канал не найден!", ephemeral=True)
                return

            # Перемещаем пользователя в AFK канал, если он в голосовом канале
            if user.voice and user.voice.channel:
                await user.move_to(afk_channel)

            # Выдаем мут роль
            await user.add_roles(mute_role)

            # Отправляем сообщение о муте
            emb = disnake.Embed(
                title='✅ Получилось',
                description=f"Пользователю {user.mention} выдали мут!\nВремя пробывания в муте: {time} сек.\nПричина выдачи мута: {reason}!",
                colour=disnake.Color.green()
            )
            emb.set_footer(text=f'Действие выполнено модератором/админом - {interaction.author.name}', icon_url=interaction.author.display_avatar.url)
            await interaction.send(embed=emb)

            # Ждем указанное время
            await asyncio.sleep(time)

            # Снимаем мут роль
            await user.remove_roles(mute_role)

            # Отправляем сообщение о размуте
            emb = disnake.Embed(
                title='✅ Пользователь размучен',
                description=f"Пользователь {user.mention} был размучен!",
                colour=disnake.Color.green()
            )
            await interaction.send(embed=emb)

        except Exception as e:
            logger.error(f"Ошибка в команде mute: {e}")
            await interaction.send("Произошла ошибка при выполнении команды.", ephemeral=True)

def setup(bot):
    bot.add_cog(Mute(bot))