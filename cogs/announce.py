import disnake
from disnake.ext import commands
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Announce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Отправляет сообщение от имени бота в указанный канал (Админская команда)")
    @commands.has_permissions(administrator=True)
    async def announce(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        title: str,
        message: str,
        footer: str = None,
        signature: bool = False,
        color: str = "0000FF",
        image: disnake.Attachment = None,
        channel: disnake.TextChannel = None
    ):
        try:
            # Если канал не указан, используем текущий канал
            target_channel = channel or interaction.channel

            # Заменяем \n на переносы строк
            message = message.replace("\\n", "\n")

            # Проверка формата цвета
            if not color.startswith("#"):
                color = f"#{color}"
            try:
                color_int = int(color.lstrip("#"), 16)
            except ValueError:
                await interaction.send("Некорректный формат цвета. Используйте HEX-формат (например, `0000FF` или `#FF0000`).", ephemeral=True)
                return

            # Создаем Embed
            emb = disnake.Embed(title=title, description=message, colour=color_int)

            # Добавляем изображение, если оно есть
            if image:
                emb.set_image(url=image.url)

            # Добавляем подпись и футер
            if footer:
                if signature:
                    footer_text = f"{footer} | © {interaction.author.name}"
                    emb.set_footer(text=footer_text, icon_url=interaction.author.display_avatar.url)
                else:
                    emb.set_footer(text=footer)

            # Отправляем Embed в указанный канал
            await target_channel.send(embed=emb)
            await interaction.send("Сообщение успешно отправлено!", ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде announce: {e}")
            await interaction.send("Произошла ошибка при отправке сообщения.", ephemeral=True)

    @announce.error
    async def announce_error(self, interaction: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.send("У вас недостаточно прав для использования этой команды.", ephemeral=True)
        else:
            await interaction.send("Произошла неизвестная ошибка.", ephemeral=True)

def setup(bot):
    bot.add_cog(Announce(bot))