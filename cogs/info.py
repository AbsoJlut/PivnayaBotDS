import disnake
from disnake.ext import commands
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Показывает информацию о сервере")
    async def info(self, interaction: disnake.ApplicationCommandInteraction):
        try:
            guild = interaction.guild

            # Основная информация о сервере
            region = guild.preferred_locale
            owner = guild.owner.mention
            created_at = guild.created_at.strftime("%d.%m.%Y %H:%M:%S")
            roles = len(guild.roles)
            emojis = len(guild.emojis)
            boosts = guild.premium_subscription_count
            boost_level = guild.premium_tier

            # Информация о участниках
            all_members = len(guild.members)
            members = len(list(filter(lambda m: not m.bot, guild.members)))
            bots = len(list(filter(lambda m: m.bot, guild.members)))

            # Статусы участников
            statuses = {
                "online": len(list(filter(lambda m: str(m.status) == "online", guild.members))),
                "idle": len(list(filter(lambda m: str(m.status) == "idle", guild.members))),
                "dnd": len(list(filter(lambda m: str(m.status) == "dnd", guild.members))),
                "offline": len(list(filter(lambda m: str(m.status) == "offline", guild.members)))
            }

            # Информация о каналах
            channels = {
                "text": len(list(filter(lambda m: str(m.type) == "text", guild.channels))),
                "voice": len(list(filter(lambda m: str(m.type) == "voice", guild.channels)))
            }

            # Создаем Embed
            embed = disnake.Embed(
                title=f"Информация о сервере {guild.name}",
                description=f"Сервер создан: {created_at}",
                color=disnake.Color.blue()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

            # Добавляем поля с информацией
            embed.add_field(name="Участники", value=f"Всего: {all_members}\nЛюди: {members}\nБоты: {bots}", inline=True)
            embed.add_field(name="Статусы", value=f"Онлайн: {statuses['online']}\nНе активен: {statuses['idle']}\nНе беспокоить: {statuses['dnd']}\nОффлайн: {statuses['offline']}", inline=True)
            embed.add_field(name="Каналы", value=f"Всего: {channels['text'] + channels['voice']}\nТекстовые: {channels['text']}\nГолосовые: {channels['voice']}", inline=True)
            embed.add_field(name="Регион", value=region, inline=True)
            embed.add_field(name="Владелец", value=owner, inline=True)
            embed.add_field(name="Роли", value=roles, inline=True)
            embed.add_field(name="Эмодзи", value=emojis, inline=True)
            embed.add_field(name="Бусты", value=f"Уровень: {boost_level}\nКоличество: {boosts}", inline=True)

            # Отправляем Embed
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Ошибка в команде info: {e}")
            await interaction.response.send_message("Произошла ошибка при получении информации о сервере.", ephemeral=True)

def setup(bot):
    bot.add_cog(Info(bot))