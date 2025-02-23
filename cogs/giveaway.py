import disnake
from disnake.ext import commands, tasks
from disnake.ui import Button, View
from datetime import datetime, timedelta
import random
import aiomysql
import logging
import os
from dotenv import load_dotenv
import asyncio

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логгера
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GiveawayConfig:
    """Класс для хранения конфигурации розыгрышей."""
    def __init__(self):
        self.mysql_host = os.getenv("MYSQL_HOST")
        self.mysql_user = os.getenv("MYSQL_USER")
        self.mysql_password = os.getenv("MYSQL_PASSWORD")
        self.mysql_db = os.getenv("MYSQL_DB_giveaway")

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = {}
        self.config = GiveawayConfig()
        self.pool = None  # Используем пул соединений

    async def connect_to_database(self):
        """Создание пула соединений с базой данных."""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config.mysql_host,
                user=self.config.mysql_user,
                password=self.config.mysql_password,
                db=self.config.mysql_db,
                cursorclass=aiomysql.DictCursor,
                autocommit=True,
                minsize=1,
                maxsize=10
            )
            logger.info("Пул соединений с базой данных создан.")
        except aiomysql.Error as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            self.pool = None

    async def create_tables(self):
        """Создание таблиц в базе данных, если они не существуют."""
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("""
                            CREATE TABLE IF NOT EXISTS giveaways (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                message_id BIGINT,
                                channel_id BIGINT,
                                end_time DATETIME,
                                winners INT,
                                prize VARCHAR(255),
                                participants TEXT
                            )
                        """)
                        await conn.commit()
                        logger.info("Таблица giveaways создана или уже существует.")
            except aiomysql.Error as e:
                logger.error(f"Ошибка при создании таблиц: {e}")

    async def cleanup_old_giveaways(self):
        """Удаление старых розыгрышей из базы данных и их сообщений."""
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        # Выбираем завершённые розыгрыши
                        await cursor.execute("SELECT * FROM giveaways WHERE end_time < NOW()")
                        old_giveaways = await cursor.fetchall()

                        for giveaway in old_giveaways:
                            channel_id = giveaway["channel_id"]
                            message_id = giveaway["message_id"]

                            # Пытаемся удалить сообщение
                            try:
                                channel = self.bot.get_channel(channel_id)
                                if channel:
                                    message = await channel.fetch_message(message_id)
                                    await message.delete()
                                    logger.info(f"Сообщение розыгрыша {giveaway['id']} удалено из канала {channel_id}.")
                                else:
                                    logger.error(f"Канал с ID {channel_id} не найден.")
                            except disnake.NotFound:
                                logger.error(f"Сообщение с ID {message_id} не найдено в канале {channel_id}.")
                            except disnake.Forbidden:
                                logger.error(f"Нет прав для удаления сообщения в канале {channel_id}.")
                            except Exception as e:
                                logger.error(f"Ошибка при удалении сообщения: {e}")

                        # Удаляем старые розыгрыши из базы данных
                        await cursor.execute("DELETE FROM giveaways WHERE end_time < NOW()")
                        await conn.commit()
                        logger.info(f"Удалено {len(old_giveaways)} старых розыгрышей из базы данных.")
            except aiomysql.Error as e:
                logger.error(f"Ошибка при удалении старых розыгрышей: {e}")

    async def load_giveaways_on_startup(self):
        """Загрузка активных розыгрышей из базы данных при запуске бота."""
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT * FROM giveaways WHERE end_time > NOW()")
                        giveaways = await cursor.fetchall()
                        for giveaway in giveaways:
                            participants = list(map(int, giveaway["participants"].split(","))) if giveaway["participants"] else []
                            self.giveaways[giveaway["id"]] = {
                                "message_id": giveaway["message_id"],
                                "channel_id": giveaway["channel_id"],
                                "end_time": giveaway["end_time"],
                                "winners": giveaway["winners"],
                                "prize": giveaway["prize"],
                                "participants": participants,
                                "button": Button(style=disnake.ButtonStyle.green, label="Участвовать", custom_id=f"giveaway_{giveaway['id']}_participate"),
                                "view_participants_button": Button(style=disnake.ButtonStyle.blurple, label="Просмотр участников", custom_id=f"giveaway_{giveaway['id']}_view_participants")
                            }
                        logger.info(f"Загружено {len(giveaways)} активных розыгрышей из базы данных.")
            except aiomysql.Error as e:
                logger.error(f"Ошибка при загрузке розыгрышей из базы данных: {e}")

    async def save_giveaway_to_db(self, giveaway_id, message_id, channel_id, end_time, winners, prize):
        """Сохраняет розыгрыш в базе данных с повторной попыткой при ошибке."""
        max_retries = 3  # Максимальное количество попыток
        retry_delay = 2  # Задержка между попытками в секундах

        for attempt in range(max_retries):
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("""
                            INSERT INTO giveaways (id, message_id, channel_id, end_time, winners, prize, participants)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (giveaway_id, message_id, channel_id, end_time, winners, prize, ""))
                        await conn.commit()
                        logger.info(f"Розыгрыш {giveaway_id} сохранен в базе данных.")
                        return  # Успешное выполнение
            except aiomysql.Error as e:
                logger.error(f"Ошибка при сохранении розыгрыша (попытка {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Не удалось сохранить розыгрыш после {max_retries} попыток.")

    async def delete_giveaway_from_db(self, giveaway_id):
        """Удаляет розыгрыш из базы данных."""
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("DELETE FROM giveaways WHERE id = %s", (giveaway_id,))
                        await conn.commit()
                        logger.info(f"Розыгрыш {giveaway_id} удален из базы данных.")
            except aiomysql.Error as e:
                logger.error(f"Ошибка при удалении розыгрыша из базы данных: {e}")

    async def update_giveaway_in_db(self, giveaway_id, end_time):
        """Обновляет время окончания розыгрыша в базе данных."""
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("""
                            UPDATE giveaways
                            SET end_time = %s
                            WHERE id = %s
                        """, (end_time, giveaway_id))
                        await conn.commit()
                        logger.info(f"Время розыгрыша {giveaway_id} обновлено в базе данных.")
            except aiomysql.Error as e:
                logger.error(f"Ошибка при обновлении розыгрыша в базе данных: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Инициализация базы данных при запуске бота."""
        await self.connect_to_database()
        await self.create_tables()
        await self.cleanup_old_giveaways()  # Очистка старых розыгрышей
        await self.load_giveaways_on_startup()
        logger.info("Бот готов и загрузил активные розыгрыши.")
        self.check_giveaways.start()  # Запускаем задачу после инициализации

    @commands.Cog.listener()
    async def on_disconnect(self):
        """Закрытие пула соединений и остановка задач при отключении бота."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Пул соединений с базой данных закрыт.")

        # Останавливаем задачу check_giveaways и ждём её завершения
        if self.check_giveaways.is_running():
            self.check_giveaways.stop()
            logger.info("Задача check_giveaways остановлена.")
            await self.check_giveaways.wait()  # Ждём завершения задачи

    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        """Проверка завершения розыгрышей."""
        for giveaway_id, giveaway_data in list(self.giveaways.items()):
            if datetime.now() >= giveaway_data["end_time"]:
                participants = giveaway_data["participants"]
                winners_count = giveaway_data["winners"]
                prize = giveaway_data["prize"]

                if participants:
                    winners = random.sample(participants, min(winners_count, len(participants)))
                    winners_mention = ", ".join([f"<@{winner}>" for winner in winners])
                    result_embed = disnake.Embed(
                        title=f"🎉 Розыгрыш завершен! 🎉",
                        description=f"**Приз:** {prize}\n"
                                    f"**Победители:** {winners_mention}",
                        color=disnake.Color.gold()
                    )
                else:
                    result_embed = disnake.Embed(
                        title=f"🎉 Розыгрыш завершен! 🎉",
                        description="**Нет участников.**",
                        color=disnake.Color.red()
                    )

                # Получаем канал и сообщение
                channel = self.bot.get_channel(giveaway_data["channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(giveaway_data["message_id"])
                        await message.edit(embed=result_embed, view=None)
                    except disnake.NotFound:
                        logger.error(f"Сообщение с ID {giveaway_data['message_id']} не найдено в канале {channel.id}.")
                    except disnake.Forbidden:
                        logger.error(f"Нет прав для редактирования сообщения в канале {channel.id}.")
                else:
                    logger.error(f"Канал с ID {giveaway_data['channel_id']} не найден.")

                # Удаляем розыгрыш из памяти и базы данных
                del self.giveaways[giveaway_id]
                await self.delete_giveaway_from_db(giveaway_id)

    @commands.slash_command(name="giveaway", description="Создать розыгрыш")
    @commands.has_permissions(administrator=True)
    async def giveaway(
        self,
        inter: disnake.ApplicationCommandInteraction,
        duration: int = commands.Param(description="Длительность розыгрыша в минутах"),
        winners: int = commands.Param(description="Количество победителей"),
        prize: str = commands.Param(description="Приз")
    ):
        """Создание розыгрыша."""
        end_time = datetime.now() + timedelta(minutes=duration)
        giveaway_id = random.randint(1000, 9999)

        embed = disnake.Embed(
            title=f"🎉 Розыгрыш: {prize} 🎉",
            description=f"**Количество победителей:** {winners}\n"
                        f"**Завершится:** <t:{int(end_time.timestamp())}:R>\n"
                        f"**Участники:** 0",
            color=disnake.Color.green()
        )
        embed.set_footer(text=f"ID розыгрыша: {giveaway_id}")

        # Кнопки
        participate_button = Button(style=disnake.ButtonStyle.green, label="Участвовать", custom_id=f"giveaway_{giveaway_id}_participate")
        view_participants_button = Button(style=disnake.ButtonStyle.blurple, label="Просмотр участников", custom_id=f"giveaway_{giveaway_id}_view_participants")

        view = View()
        view.add_item(participate_button)
        view.add_item(view_participants_button)

        # Отправляем сообщение без ответа на команду
        await inter.send(embed=embed, view=view)
        message = await inter.original_message()

        # Сохраняем розыгрыш в базе данных
        await self.save_giveaway_to_db(giveaway_id, message.id, inter.channel_id, end_time, winners, prize)

        self.giveaways[giveaway_id] = {
            "message_id": message.id,
            "channel_id": inter.channel_id,
            "end_time": end_time,
            "winners": winners,
            "prize": prize,
            "participants": [],
            "button": participate_button,
            "view_participants_button": view_participants_button
        }

    @commands.slash_command(name="cancel_giveaway", description="Отменить розыгрыш")
    @commands.has_permissions(administrator=True)
    async def cancel_giveaway(self, inter: disnake.ApplicationCommandInteraction, giveaway_id: int):
        """Отмена розыгрыша."""
        if giveaway_id in self.giveaways:
            giveaway_data = self.giveaways[giveaway_id]
            channel_id = giveaway_data["channel_id"]
            message_id = giveaway_data["message_id"]

            # Удаляем сообщение с розыгрышем
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                    logger.info(f"Сообщение с розыгрышем {giveaway_id} удалено из канала {channel_id}.")
                else:
                    logger.error(f"Канал с ID {channel_id} не найден.")
            except disnake.NotFound:
                logger.error(f"Сообщение с ID {message_id} не найдено в канале {channel_id}.")
            except disnake.Forbidden:
                logger.error(f"Нет прав для удаления сообщения в канале {channel_id}.")
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")

            # Удаляем розыгрыш из памяти и базы данных
            del self.giveaways[giveaway_id]
            await self.delete_giveaway_from_db(giveaway_id)
            await inter.send(f"Розыгрыш {giveaway_id} отменен и сообщение удалено.", ephemeral=True)
            logger.info(f"Розыгрыш {giveaway_id} отменен.")
        else:
            await inter.send("Розыгрыш с таким ID не найден.", ephemeral=True)

    @commands.slash_command(name="extend_giveaway", description="Продлить розыгрыш")
    @commands.has_permissions(administrator=True)
    async def extend_giveaway(
        self,
        inter: disnake.ApplicationCommandInteraction,
        giveaway_id: int,
        additional_time: int = commands.Param(description="Дополнительное время в минутах")
    ):
        """Продление времени розыгрыша."""
        if giveaway_id in self.giveaways:
            giveaway_data = self.giveaways[giveaway_id]
            channel_id = giveaway_data["channel_id"]
            message_id = giveaway_data["message_id"]

            # Обновляем время окончания розыгрыша
            new_end_time = giveaway_data["end_time"] + timedelta(minutes=additional_time)
            giveaway_data["end_time"] = new_end_time

            # Обновляем время окончания в базе данных
            await self.update_giveaway_in_db(giveaway_id, new_end_time)

            # Получаем сообщение с розыгрышем
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    message = await channel.fetch_message(message_id)
                    embed = message.embeds[0]  # Получаем текущий embed

                    # Обновляем embed с новым временем окончания
                    embed.description = (
                        f"**Количество победителей:** {giveaway_data['winners']}\n"
                        f"**Завершится:** <t:{int(new_end_time.timestamp())}:R>\n"
                        f"**Участники:** {len(giveaway_data['participants'])}"
                    )

                    # Редактируем сообщение с обновленным embed
                    await message.edit(embed=embed)
                    logger.info(f"Время розыгрыша {giveaway_id} обновлено в сообщении.")
                else:
                    logger.error(f"Канал с ID {channel_id} не найден.")
            except disnake.NotFound:
                logger.error(f"Сообщение с ID {message_id} не найдено в канале {channel_id}.")
            except disnake.Forbidden:
                logger.error(f"Нет прав для редактирования сообщения в канале {channel_id}.")
            except Exception as e:
                logger.error(f"Ошибка при обновлении сообщения: {e}")

            # Отправляем подтверждение администратору
            await inter.send(
                f"Время розыгрыша {giveaway_id} продлено на {additional_time} минут.", ephemeral=True
            )
            logger.info(f"Время розыгрыша {giveaway_id} продлено на {additional_time} минут.")
        else:
            await inter.send("Розыгрыш с таким ID не найден.", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        """Обработка нажатия кнопки участия и просмотра участников."""
        if not inter.component.custom_id:
            return

        # Обработка только кнопок, связанных с розыгрышами
        if inter.component.custom_id.startswith("giveaway_"):
            giveaway_id = int(inter.component.custom_id.split("_")[1])  # Извлекаем ID розыгрыша из custom_id
            giveaway_data = self.giveaways.get(giveaway_id)

            if not giveaway_data:
                await inter.response.send_message("Розыгрыш не найден.", ephemeral=True)
                return

            if "participate" in inter.component.custom_id:
                if inter.author.id not in giveaway_data["participants"]:
                    giveaway_data["participants"].append(inter.author.id)
                    embed = inter.message.embeds[0]
                    embed.description = embed.description.replace(
                        f"**Участники:** {len(giveaway_data['participants']) - 1}",
                        f"**Участники:** {len(giveaway_data['participants'])}"
                    )
                    await inter.response.edit_message(embed=embed)
                    # Оповещение участнику через followup
                    await inter.followup.send(f"Вы успешно участвуете в розыгрыше! 🎉", ephemeral=True)
                else:
                    await inter.response.send_message("Вы уже участвуете в этом розыгрыше!", ephemeral=True)
            elif "view_participants" in inter.component.custom_id:
                participants = giveaway_data["participants"]
                if participants:
                    participants_mention = ", ".join([f"<@{participant}>" for participant in participants])
                    participants_embed = disnake.Embed(
                        title="Участники розыгрыша",
                        description=participants_mention,
                        color=disnake.Color.blue()
                    )
                    await inter.response.send_message(embed=participants_embed, ephemeral=True)
                else:
                    await inter.response.send_message("Участников пока нет.", ephemeral=True)

    @giveaway.error
    async def giveaway_error(self, inter: disnake.ApplicationCommandInteraction, error):
        """Обработчик ошибок для команды giveaway."""
        if isinstance(error, commands.MissingPermissions):
            if not inter.response.is_done():
                await inter.send("У вас недостаточно прав для использования этой команды.", ephemeral=True)
        else:
            if not inter.response.is_done():
                await inter.send("Произошла неизвестная ошибка.", ephemeral=True)
            logger.error(f"Ошибка в команде giveaway: {error}")

def setup(bot):
    """Функция для добавления кога в бота."""
    bot.add_cog(Giveaway(bot))
