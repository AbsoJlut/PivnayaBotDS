import disnake
from disnake.ext import commands
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Показывает список команд и их описания")
    async def help(self, interaction: disnake.ApplicationCommandInteraction):
        try:
            # Создаем Embed
            embed = disnake.Embed(
                title="Список команд",
                description="Вот список команд, которые доступны для использования:",
                color=disnake.Color.green()
            )

            # Группируем команды по категориям (Cog)
            categories = {}
            for command in self.bot.slash_commands:
                # Получаем Cog команды
                cog = command.cog
                if cog:
                    category_name = cog.qualified_name  # Название категории (Cog)
                else:
                    category_name = "Без категории"  # Если команда не принадлежит ни к одному Cog

                # Добавляем команду в соответствующую категорию
                if category_name not in categories:
                    categories[category_name] = []
                categories[category_name].append(command)

            # Добавляем команды в Embed по категориям
            for category, commands_list in categories.items():
                # Формируем текст для списка команд
                commands_text = "\n".join(f"`/{cmd.name}`: {cmd.description}" for cmd in commands_list)
                # Добавляем поле в Embed
                embed.add_field(name=category, value=commands_text, inline=False)

            # Отправляем Embed
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде help: {e}")
            await interaction.response.send_message("Произошла ошибка при отображении списка команд.", ephemeral=True)

def setup(bot):
    bot.add_cog(Help(bot))