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

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moder_roles = list(map(int, os.getenv("MODER_ROLES").split(",")))
        self.mute_role_id = int(os.getenv("MUTE_ROLE_ID"))

    @commands.slash_command(description="Размучивает пользователя (Админская команда)")
    async def unmute(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        reason: str = "Причина не указана"
    ):
        try:
            # Проверяем, есть ли у пользователя необходимая роль
            if not any(role.id in self.moder_roles for role in interaction.author.roles):
                await interaction.response.send_message("У вас недостаточно прав для использования этой команды.", ephemeral=True)
                return

            role = user.guild.get_role(self.mute_role_id)  # айди роли которую будет снимать у юзера

            if not role:
                await interaction.response.send_message("Роль мута не найдена!", ephemeral=True)
                return

            if role in user.roles:
                await user.remove_roles(role)  # снимает мьют роль
                emb = disnake.Embed(
                    title='✅ Пользователь размучен',
                    description=f"Пользователь {user.mention} был размучен!",
                    colour=disnake.Color.green()
                )
                emb.add_field(name="Причина", value=reason, inline=False)
                emb.set_footer(text=f'Действие выполнено модератором/админом - {interaction.author.name}', icon_url=interaction.author.display_avatar.url)
                await interaction.response.send_message(embed=emb)
            else:
                await interaction.response.send_message(f"Пользователь {user.name} не имеет роли мута!", ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде unmute: {e}")
            await interaction.response.send_message("Произошла ошибка при размуте пользователя.", ephemeral=True)

    @unmute.error
    async def unmute_error(self, interaction: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingAnyRole):
            await interaction.response.send_message("У вас недостаточно прав для использования этой команды.", ephemeral=True)
        else:
            await interaction.response.send_message("Произошла неизвестная ошибка.", ephemeral=True)

def setup(bot):
    bot.add_cog(Unmute(bot))