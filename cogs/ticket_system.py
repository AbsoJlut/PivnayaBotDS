import disnake
from disnake import ButtonStyle
from disnake.ext import commands
from disnake.ext.commands import MissingPermissions  # Импортируем исключение
import pymysql  # Используем pymysql для работы с MySQL
import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получаем список ID ролей модераторов
MODER_ROLES = [int(role_id) for role_id in os.getenv('MODER_ROLES').split(',')]
TICKET_CATEGORY_ID = int(os.getenv('TICKET_CATEGORY_ID'))
CLOSED_TICKET_CATEGORY_ID = int(os.getenv('CLOSED_TICKET_CATEGORY_ID'))

# Настройки подключения к MySQL
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', '')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB_ticket', 'ticket_system')

def get_db_connection():
    """Создаёт и возвращает соединение с базой данных MySQL."""
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

class clb(disnake.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @disnake.ui.button(label="Удалить тикет", style=ButtonStyle.danger, emoji='<:ticketbutton:933130024356302898>', custom_id="delete_ticket")
    async def delete_ticket(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Проверка роли модератора
        if any(role.id in MODER_ROLES for role in interaction.author.roles):
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute('DELETE FROM tickets WHERE id_channel = %s', (interaction.channel.id,))
                    connection.commit()
                await interaction.channel.delete()
            finally:
                connection.close()
        else:
            await interaction.send("Вы не можете закрыть тикет, ожидайте администратора", ephemeral=True)

    @disnake.ui.button(label="Закрыть тикет", style=ButtonStyle.primary, emoji='<:ticketbutton:933130024356302898>', custom_id="close_ticket")
    async def close_ticket(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Проверка роли модератора
        if any(role.id in MODER_ROLES for role in interaction.author.roles):
            connection = get_db_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT id_member FROM tickets WHERE id_channel = %s', (interaction.channel.id,))
                    a = cursor.fetchone()
                    cursor.execute('DELETE FROM tickets WHERE id_channel = %s', (interaction.channel.id,))
                    connection.commit()

                    if a:
                        try:
                            member = await interaction.guild.fetch_member(a['id_member'])
                            overwrites = {
                                interaction.guild.default_role: disnake.PermissionOverwrite(view_channel=False, send_messages=False),
                                member: disnake.PermissionOverwrite(view_channel=False),
                            }
                            # Добавляем права для всех ролей модераторов
                            for role_id in MODER_ROLES:
                                role = disnake.utils.get(interaction.guild.roles, id=role_id)
                                if role:
                                    overwrites[role] = disnake.PermissionOverwrite(view_channel=True)

                            category = self.bot.get_channel(CLOSED_TICKET_CATEGORY_ID)
                            if category:
                                await interaction.channel.edit(category=category, overwrites=overwrites)
                                await interaction.send("Тикет закрыт.")
                                await interaction.message.delete()
                            else:
                                await interaction.send("Категория для закрытых тикетов не найдена.", ephemeral=True)
                        except disnake.NotFound:
                            await interaction.send("Участник не найден. Возможно, он покинул сервер.", ephemeral=True)
                        except Exception as e:
                            logger.error(f"Ошибка при закрытии тикета: {e}")
                            await interaction.send("Произошла ошибка при закрытии тикета.", ephemeral=True)
                    else:
                        await interaction.send("Тикет не найден в базе данных.", ephemeral=True)
            finally:
                connection.close()
        else:
            await interaction.send("Вы не можете закрыть тикет, ожидайте администратора", ephemeral=True)


class ticket_buttons(disnake.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @disnake.ui.button(label="Открыть тикет", style=ButtonStyle.primary, emoji='<:ticketbutton:933130024356302898>', custom_id="open_ticket")
    async def open_ticket(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id_member FROM tickets WHERE id_member = %s', (interaction.author.id,))
                a1 = cursor.fetchone()

                if a1 is None:
                    guild = interaction.guild
                    overwrites = {
                        guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                        interaction.author: disnake.PermissionOverwrite(view_channel=True),
                    }
                    # Добавляем права для всех ролей модераторов
                    for role_id in MODER_ROLES:
                        role = disnake.utils.get(interaction.guild.roles, id=role_id)
                        if role:
                            overwrites[role] = disnake.PermissionOverwrite(view_channel=True)

                    category = self.bot.get_channel(TICKET_CATEGORY_ID)
                    if category:
                        ticket_channel = await guild.create_text_channel(
                            name=f"Тикет-{interaction.author.name}".replace(" ", "_"),
                            category=category,
                            overwrites=overwrites
                        )
                        cursor.execute('INSERT INTO tickets (id_member, id_channel) VALUES (%s, %s)', (interaction.author.id, ticket_channel.id))
                        connection.commit()

                        ticket_embed = disnake.Embed(
                            title="Поддержка",
                            colour=0x2F3136,
                            description=(
                                f"Здравствуйте, {interaction.author.mention} ({interaction.author.name})! 👋\n\n"
                                "Мы готовы помочь вам с вашим вопросом или проблемой. Чтобы мы могли оперативно и эффективно решить ваш запрос, "
                                "пожалуйста, опишите ситуацию как можно подробнее. Чем больше деталей вы предоставите, тем быстрее мы сможем вам помочь.\n\n"
                                "**Что нужно сделать:**\n"
                                "1. Опишите вашу проблему или вопрос.\n"
                                "2. Укажите, если есть дополнительные детали (например, скриншоты, ссылки или примеры).\n"
                                "3. Будьте готовы ответить на уточняющие вопросы от администратора.\n\n"
                                "⏳ *Ожидание ответа администратора может занять некоторое время, но обычно это занимает не более 10–15 минут. "
                                "Спасибо за ваше понимание и терпение!*\n\n"
                                "Если у вас срочный вопрос, пожалуйста, укажите это в сообщении, и мы постараемся обработать ваш запрос как можно быстрее."
                            )
                        )
                        await ticket_channel.send(embed=ticket_embed, view=clb(bot=self.bot))
                        await interaction.send(f"Ваш тикет: {ticket_channel.mention}", ephemeral=True)
                    else:
                        await interaction.send("Категория для тикетов не найдена.", ephemeral=True)
                else:
                    cursor.execute('SELECT id_channel FROM tickets WHERE id_member = %s', (interaction.author.id,))
                    channel1 = cursor.fetchone()
                    if channel1:
                        await interaction.send(f"У вас уже есть тикет - <#{channel1['id_channel']}>, будьте терпиливее, ожидайте администрацию.", ephemeral=True)
                    else:
                        await interaction.send("Ошибка при поиске вашего тикета.", ephemeral=True)
        finally:
            connection.close()


class ticket_system(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistent_views_added = False

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id_channel FROM tickets WHERE id_member = %s', (member.id,))
                check1 = cursor.fetchone()
                if check1:
                    cursor.execute('DELETE FROM tickets WHERE id_member = %s', (member.id,))
                    connection.commit()
                    channel = self.bot.get_channel(check1['id_channel'])
                    if channel:
                        await channel.send(f"{member.name}, покинул сервер, <@403829627753070603>")
        finally:
            connection.close()

    @commands.has_permissions(administrator=True)
    @commands.slash_command(description="Setup системы тикетов (Админская команда)")
    async def tstart(self, ctx):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tickets (
                        id_member BIGINT,
                        id_channel BIGINT
                    )
                ''')
                connection.commit()
            tstartembed = disnake.Embed(
                title="Успех",
                colour=0x2F3136,
                description="Тикет бот успешно установлен, создана таблица для работы, осталось отправить сообщение от тикетов ``/ticket``"
            )
            await ctx.send(embed=tstartembed)
        finally:
            connection.close()

    @tstart.error
    async def tstart_error(self, ctx, error):
        """Обработчик ошибок для команды tstart."""
        if isinstance(error, MissingPermissions):
            await ctx.send("У вас недостаточно прав для использования этой команды.", ephemeral=True)
        else:
            await ctx.send("Произошла неизвестная ошибка.", ephemeral=True)
            logger.error(f"Ошибка в команде tstart: {error}")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.persistent_views_added:
            self.bot.add_view(ticket_buttons(bot=self.bot))
            self.bot.add_view(clb(bot=self.bot))
            self.persistent_views_added = True

    @commands.slash_command(description="Добавить кнопку создания тикета к сообщению (Админская команда)")
    @commands.has_permissions(administrator=True)
    async def add_ticket_button(self, ctx, message_id: str):
        try:
            message_id = int(message_id)
            channel = ctx.channel
            message = await channel.fetch_message(message_id)
            
            # Проверяем, есть ли уже кнопка на сообщении
            if not message.components:
                await message.edit(view=ticket_buttons(bot=self.bot))
                await ctx.send("Кнопка успешно добавлена к сообщению.", ephemeral=True)
            else:
                await ctx.send("На этом сообщении уже есть кнопка.", ephemeral=True)
        except disnake.NotFound:
            await ctx.send("Сообщение с таким ID не найдено.", ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка при добавлении кнопки: {e}")
            await ctx.send("Произошла ошибка при добавлении кнопки.", ephemeral=True)

    @add_ticket_button.error
    async def add_ticket_button_error(self, ctx, error):
        """Обработчик ошибок для команды add_ticket_button."""
        if isinstance(error, MissingPermissions):
            await ctx.send("У вас недостаточно прав для использования этой команды.", ephemeral=True)
        else:
            await ctx.send("Произошла неизвестная ошибка.", ephemeral=True)
            logger.error(f"Ошибка в команде add_ticket_button: {error}")


def setup(bot):
    bot.add_cog(ticket_system(bot))