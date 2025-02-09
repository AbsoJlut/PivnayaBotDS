import disnake
from disnake.ext import commands
import requests
from io import BytesIO
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Отправляет сообщение от имени бота в указанный канал (Админская команда)")
    @commands.has_permissions(administrator=True)
    async def say(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        message: str = None,
        attachment: disnake.Attachment = None,
        reply: str = None,
        channel: disnake.TextChannel = None
    ):
        try:
            # Откладываем ответ, чтобы избежать тайм-аута
            await interaction.response.defer(ephemeral=True)

            target_channel = channel or interaction.channel

            if message:
                message = message.replace("\\n", "\n")

            if reply:
                try:
                    # Преобразуем reply в int (ID сообщения)
                    message_id = int(reply)
                    # Пытаемся найти сообщение по ID
                    original_message = await target_channel.fetch_message(message_id)

                    if attachment:
                        response = requests.get(attachment.url)
                        data = BytesIO(response.content)
                        await original_message.reply(message, file=disnake.File(data, filename=attachment.filename))
                    elif message:
                        await original_message.reply(message)
                    else:
                        await interaction.followup.send("Вы должны отправить либо текст, либо фотографию, либо и то, и другое.", ephemeral=True)
                        return

                    await interaction.followup.send("Ответ успешно отправлен!", ephemeral=True)

                except ValueError:
                    # Если reply не является числом
                    await interaction.followup.send("ID сообщения должен быть числом.", ephemeral=True)
                except disnake.errors.NotFound:
                    # Если сообщение не найдено
                    await interaction.followup.send("Сообщение с таким ID не найдено.", ephemeral=True)
                except disnake.errors.Forbidden:
                    # Если у бота нет прав на чтение сообщений в канале
                    await interaction.followup.send("У меня нет прав на чтение сообщений в этом канале.", ephemeral=True)
                except Exception as e:
                    logger.error(f"Ошибка при отправке ответа: {e}")
                    await interaction.followup.send(f"Произошла ошибка: {e}", ephemeral=True)
            else:
                if attachment:
                    response = requests.get(attachment.url)
                    data = BytesIO(response.content)
                    await target_channel.send(message, file=disnake.File(data, filename=attachment.filename))
                elif message:
                    await target_channel.send(message)
                else:
                    await interaction.followup.send("Вы должны отправить либо текст, либо фотографию, либо и то, и другое.", ephemeral=True)
                    return

                await interaction.followup.send("Сообщение успешно отправлено!", ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде say: {e}")
            await interaction.followup.send("Произошла ошибка при отправке сообщения.", ephemeral=True)

    @say.error
    async def say_error(self, interaction: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("У вас недостаточно прав для использования этой команды.", ephemeral=True)
        else:
            await interaction.response.send_message("Произошла неизвестная ошибка.", ephemeral=True)

def setup(bot):
    bot.add_cog(Chat(bot))