import disnake
from disnake.ext import commands
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Показывает информацию о пользователе")
    async def user(self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        try:
            if member is None:
                member = interaction.author

            # Получаем роли пользователя
            roles = [role for role in member.roles if role.name != "@everyone"]
            roles_text = ", ".join(role.mention for role in roles) if roles else "Нет ролей"

            # Получаем статус пользователя
            status = str(member.status)
            status_emoji = {
                "online": "🟢",
                "idle": "🟡",
                "dnd": "🔴",
                "offline": "⚫"
            }.get(status, "⚫")

            # Получаем активность пользователя
            activity = member.activity
            activity_text = f"**{activity.name}** ({activity.type})" if activity else "Нет активности"

            # Создаем Embed
            embed = disnake.Embed(
                title=f"Информация о пользователе {member.name}",
                color=member.color if member.color else disnake.Color.blurple()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Никнейм", value=member.display_name, inline=True)
            embed.add_field(name="Статус", value=f"{status_emoji} {status.capitalize()}", inline=True)
            embed.add_field(name="Активность", value=activity_text, inline=False)
            embed.add_field(name="Дата создания аккаунта", value=member.created_at.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
            embed.add_field(name="Дата вступления на сервер", value=member.joined_at.strftime("%d.%m.%Y %H:%M:%S"), inline=True)
            embed.add_field(name="Роли", value=roles_text if len(roles_text) <= 1024 else "Слишком много ролей для отображения", inline=False)
            embed.add_field(name="Высшая роль", value=member.top_role.mention, inline=True)
            embed.add_field(name="Бот?", value="Да" if member.bot else "Нет", inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Ошибка в команде user: {e}")
            await interaction.response.send_message("Произошла ошибка при получении информации о пользователе.", ephemeral=True)

def setup(bot):
    bot.add_cog(UserInfo(bot))