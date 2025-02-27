import os
import asyncio
import disnake
from disnake.ext import commands
from disnake.ui import Button, View, Select
import aiomysql
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Получение переменных из .env
DB_HOST = os.getenv('MYSQL_HOST')
DB_USER = os.getenv('MYSQL_USER')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_NAME = os.getenv('MYSQL_DB_private_voice')
MUTE_ROLE_ID = int(os.getenv('MUTE_ROLE_ID'))  # ID роли мута из .env
ROLE_ID = int(os.getenv('ROLE_ID_DEFAULT'))  # ID роли из .env
CATEGORY_ID = int(os.getenv('CATEGORY_ID_PRIVATE_VOICE'))  # ID категории из .env
JOIN_CHANNEL_ID = int(os.getenv('JOIN_CHANNEL_ID_PRIVATE_VOICE'))  # ID канала для присоединения из .env

# Функция для подключения к базе данных
async def get_db_connection():
    return await aiomysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        cursorclass=aiomysql.DictCursor
    )

class PrivateVoiceChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.cleanup_channels_on_startup())

    async def cleanup_channels_on_startup(self):
        """Удаляет все приватные каналы и кикает участников при запуске бота."""
        await self.bot.wait_until_ready()  # Ждем, пока бот полностью загрузится
        active_channels = await self.get_active_channels()
        for channel_id in active_channels:
            channel = self.bot.get_channel(channel_id)
            if channel:  # Проверяем, существует ли канал
                try:
                    # Кикаем всех участников из канала
                    for member in channel.members:
                        try:
                            await member.move_to(None)
                        except disnake.HTTPException as e:
                            print(f"Не удалось кикнуть участника {member.display_name}: {e}")
    
                    # Удаляем канал
                    await channel.delete()
                    print(f"Канал {channel.name} (ID: {channel.id}) удален.")
                except disnake.NotFound:
                    print(f"Канал с ID {channel_id} не найден. Возможно, он уже был удален.")
                except disnake.HTTPException as e:
                    print(f"Ошибка при удалении канала {channel_id}: {e}")

            # Удаляем запись из базы данных
            connection = await get_db_connection()
            try:
                async with connection.cursor() as cursor:
                    sql = "DELETE FROM active_channels WHERE channel_voice = %s"
                    await cursor.execute(sql, (channel_id,))
                await connection.commit()
            except aiomysql.Error as e:
                print(f"Ошибка при удалении записи из базы данных для канала {channel_id}: {e}")
            finally:
                connection.close()
        print("Все приватные каналы удалены, участники кикнуты.")

    async def get_active_channels(self):
        """Получает активные каналы из базы данных."""
        connection = await get_db_connection()
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT channel_voice FROM active_channels"
                await cursor.execute(sql)
                result = await cursor.fetchall()
                return [row['channel_voice'] for row in result]  # Возвращаем список ID каналов
        finally:
            connection.close()

    async def create_private_channel(self, member):
        """Создает приватный голосовой канал."""
        guild = member.guild
        category = disnake.utils.get(guild.categories, id=CATEGORY_ID)
        if category is None:
            category = await guild.create_category(name='Приватные каналы')

        # Настройка прав доступа
        role = guild.get_role(ROLE_ID)
        mute_role = guild.get_role(MUTE_ROLE_ID)  # Получаем роль мута
        
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            role: disnake.PermissionOverwrite(connect=True, view_channel=True),
            mute_role: disnake.PermissionOverwrite(
                speak=False,              # Запрещаем говорить
                send_messages=False,      # Запрещаем отправлять сообщения
                embed_links=False         # Запрещаем встраивать ссылки
            ),
            member: disnake.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                stream=True
            )
        }

        # Создание канала
        new_channel = await category.create_voice_channel(
            name=f'Канал {member.display_name}',
            bitrate=64000,  # Битрейт
            user_limit=0,
            overwrites=overwrites
        )

        # Перемещение пользователя в новый канал
        await member.move_to(new_channel)

        # Сохраняем данные в БД
        connection = await get_db_connection()
        try:
            async with connection.cursor() as cursor:
                sql = "INSERT INTO active_channels (channel_voice, owner_id) VALUES (%s, %s)"
                await cursor.execute(sql, (new_channel.id, member.id))
            await connection.commit()
        finally:
            connection.close()

        # Обновляем панель управления
        await self.update_panel(new_channel, member.id)

    async def update_panel(self, channel, owner_id):
        """Создает панель управления для приватного канала."""
        try:
            view = View(timeout=None)
            view.add_item(Button(label="", style=disnake.ButtonStyle.grey, custom_id=f"private_close_{channel.id}", emoji="🔒"))  # Закрыть канал
            view.add_item(Button(label="", style=disnake.ButtonStyle.grey, custom_id=f"private_open_{channel.id}", emoji="🔓"))  # Открыть канал
            view.add_item(Button(label="", style=disnake.ButtonStyle.grey, custom_id=f"private_add_limit_{channel.id}", emoji="➕"))  # Увеличить лимит
            view.add_item(Button(label="", style=disnake.ButtonStyle.grey, custom_id=f"private_remove_limit_{channel.id}", emoji="➖"))  # Уменьшить лимит
            view.add_item(Button(label="", style=disnake.ButtonStyle.grey, custom_id=f"private_change_name_{channel.id}", emoji="✏️"))  # Изменить название
            view.add_item(Button(label="", style=disnake.ButtonStyle.red, custom_id=f"private_kick_member_{channel.id}", emoji="🚪"))  # Кикнуть участника

            # Отправляем панель управления
            panel_message = await channel.send(embed=disnake.Embed(
                title='Управление комнатой',
                description='Измените настройки комнаты с помощью панели управления. \n 🔒 - Закрыть канал \n 🔓 - Открыть канал \n ➕ - Добавить 1 слот \n ➖ - Убрать 1 слот \n ✏️ - Изменить название канала \n 🚪 - Исключить участника',
                color=disnake.Color.blue()
            ), view=view)

        except Exception as e:
            raise e

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        """Обработка нажатия кнопок для приватных каналов."""
        if not inter.component.custom_id or not inter.component.custom_id.startswith("private_"):
            return

        # Извлекаем ID канала из custom_id
        channel_id = int(inter.component.custom_id.split("_")[-1])
        channel = inter.guild.get_channel(channel_id)

        if not channel:
            await inter.response.send_message("Канал не найден.", ephemeral=True)
            return

        # Получаем владельца канала из базы данных
        owner_id = await self.get_channel_owner(channel_id)
        if inter.author.id != owner_id:
            await inter.response.send_message("Вы не являетесь владельцем этого канала.", ephemeral=True)
            return

        # Обработка кнопок
        if "private_close" in inter.component.custom_id:
            role = inter.guild.get_role(ROLE_ID)
            overwrites = channel.overwrites
            overwrites[role].update(connect=False)  # Запрещаем подключение
            await channel.edit(overwrites=overwrites)
            await inter.response.send_message("Канал закрыт: подключение запрещено.", ephemeral=True)

        elif "private_open" in inter.component.custom_id:
            role = inter.guild.get_role(ROLE_ID)
            overwrites = channel.overwrites
            overwrites[role].update(connect=True)  # Разрешаем подключение
            await channel.edit(overwrites=overwrites)
            await inter.response.send_message("Канал открыт: подключение разрешено.", ephemeral=True)

        elif "private_add_limit" in inter.component.custom_id:
            current_limit = channel.user_limit
            new_limit = current_limit + 1 if current_limit < 99 else 99
            await channel.edit(user_limit=new_limit)
            await inter.response.send_message(f"Лимит участников увеличен до {new_limit}.", ephemeral=True)

        elif "private_remove_limit" in inter.component.custom_id:
            current_limit = channel.user_limit
            new_limit = current_limit - 1 if current_limit > 0 else 0
            await channel.edit(user_limit=new_limit)
            await inter.response.send_message(f"Лимит участников уменьшен до {new_limit}.", ephemeral=True)

        elif "private_change_name" in inter.component.custom_id:
            await inter.response.send_message("Введите новое название канала:", ephemeral=True)
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == inter.author and m.channel == inter.channel,
                    timeout=30
                )
                new_name = response.content
                await channel.edit(name=new_name)
                await inter.followup.send(f"Название канала изменено на: {new_name}", ephemeral=True)
            except asyncio.TimeoutError:
                await inter.followup.send("Время ожидания истекло.", ephemeral=True)

        elif "private_kick_member" in inter.component.custom_id:
            members = [member for member in channel.members if not member.bot]
            if not members:
                await inter.response.send_message("В канале нет участников для кика.", ephemeral=True)
                return

            options = [disnake.SelectOption(label=member.display_name, value=str(member.id)) for member in members]
            select_menu = Select(placeholder="Выберите участника", options=options, custom_id="kick_member_select")

            view = View()
            view.add_item(select_menu)

            await inter.response.send_message("Выберите участника для кика:", view=view, ephemeral=True)

            def check_select(i):
                return i.data['custom_id'] == "kick_member_select" and i.user.id == inter.author.id

            try:
                select_interaction = await self.bot.wait_for("dropdown", check=check_select, timeout=30)
                member_id = int(select_interaction.data['values'][0])
                member_to_kick = inter.guild.get_member(member_id)
                if member_to_kick:
                    await member_to_kick.move_to(None)
                    await select_interaction.response.send_message(f"{member_to_kick.display_name} был кикнут.", ephemeral=True)
            except asyncio.TimeoutError:
                await inter.followup.send("Время ожидания истекло.", ephemeral=True)

    async def get_channel_owner(self, channel_id):
        """Получает владельца канала из базы данных."""
        connection = await get_db_connection()
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT owner_id FROM active_channels WHERE channel_voice = %s"
                await cursor.execute(sql, (channel_id,))
                result = await cursor.fetchone()
                return result['owner_id'] if result else None
        finally:
            connection.close()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Удаляет канал, если он пуст."""
        if before.channel is not None:
            active_channels = await self.get_active_channels()  # Получаем активные каналы
            if before.channel.id in active_channels:  # Проверяем, есть ли канал в списке активных
                if len(before.channel.members) == 0:
                    await before.channel.delete()

                    # Удаляем данные из БД
                    connection = await get_db_connection()
                    try:
                        async with connection.cursor() as cursor:
                            sql = "DELETE FROM active_channels WHERE channel_voice = %s"
                            await cursor.execute(sql, (before.channel.id,))
                        await connection.commit()
                    finally:
                        connection.close()

        if after.channel is not None and after.channel.id == JOIN_CHANNEL_ID:
            await self.create_private_channel(member)

def setup(bot):
    bot.add_cog(PrivateVoiceChannels(bot))
