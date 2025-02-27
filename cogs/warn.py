# import disnake
# from disnake.ext import commands, tasks
# import pymysql
# from dotenv import load_dotenv
# import os
# from datetime import datetime, timedelta
# import asyncio

# load_dotenv()

# class WarnSystem(commands.Cog):
    # def __init__(self, bot):
        # self.bot = bot
        # self.db_connection = self.create_db_connection()
        # self.create_warns_table()
        # self.check_mute_expiry.start()

    # def create_db_connection(self):
        # try:
            # connection = pymysql.connect(
                # host=os.getenv('MYSQL_HOST'),
                # user=os.getenv('MYSQL_USER'),
                # password=os.getenv('MYSQL_PASSWORD'),
                # database=os.getenv('MYSQL_DB_warns'),
                # cursorclass=pymysql.cursors.DictCursor
            # )
            # return connection
        # except pymysql.Error as e:
            # print(f"Ошибка подключения к базе данных: {e}")
            # return None

    # def create_warns_table(self):
        # if self.db_connection:
            # with self.db_connection.cursor() as cursor:
                # cursor.execute('''
                    # CREATE TABLE IF NOT EXISTS warns (
                        # user_id BIGINT,
                        # guild_id BIGINT,
                        # warn_count INT,
                        # mute_expiry DATETIME,
                        # PRIMARY KEY (user_id, guild_id)
                    # )
                # ''')
            # self.db_connection.commit()

    # async def is_moderator(self, member: disnake.Member):
        # """Проверяет, есть ли у пользователя одна из ролей модератора."""
        # moderator_roles = os.getenv('MODER_ROLES')
        # if moderator_roles is None:
            # print("Ошибка: MODER_ROLES не найден в .env файле.")
            # return False

        # try:
            #Разделяем строку на отдельные ID ролей и преобразуем их в числа
            # moderator_role_ids = [int(role_id.strip()) for role_id in moderator_roles.split(',')]
        # except ValueError:
            # print("Ошибка: MODER_ROLES должен содержать только числа, разделённые запятыми.")
            # return False

        #Проверяем, есть ли у пользователя хотя бы одна из ролей
        # return any(role.id in moderator_role_ids for role in member.roles)

    # async def remove_mute_role(self, user_id: int, guild_id: int):
        # """Снимает роль мута у пользователя."""
        # guild = self.bot.get_guild(guild_id)
        # if guild:
            # user = guild.get_member(user_id)
            # if user:
                # mute_role = guild.get_role(int(os.getenv('MUTE_ROLE_ID')))
                # if mute_role and mute_role in user.roles:
                    # await user.remove_roles(mute_role)
                    # with self.db_connection.cursor() as cursor:
                        # cursor.execute('UPDATE warns SET mute_expiry = NULL, warn_count = 0 WHERE user_id = %s AND guild_id = %s', (user_id, guild_id))
                        # self.db_connection.commit()

    # async def restore_mutes_on_startup(self):
        # """Восстанавливает отсчёт времени мута при запуске бота."""
        # if not self.db_connection:
            # return

        # with self.db_connection.cursor() as cursor:
            # cursor.execute('SELECT user_id, guild_id, mute_expiry FROM warns WHERE mute_expiry IS NOT NULL')
            # results = cursor.fetchall()

            # for row in results:
                # user_id = row['user_id']
                # guild_id = row['guild_id']
                # mute_expiry = row['mute_expiry']

                # if datetime.now() < mute_expiry:
                    #Если время мута ещё не истекло, планируем снятие роли
                    # time_remaining = (mute_expiry - datetime.now()).total_seconds()
                    # await self.schedule_mute_removal(user_id, guild_id, time_remaining)

    # async def schedule_mute_removal(self, user_id: int, guild_id: int, delay: float):
        # """Планирует снятие роли мута через указанное время."""
        # await asyncio.sleep(delay)
        # await self.remove_mute_role(user_id, guild_id)

    # @commands.Cog.listener()
    # async def on_ready(self):
        # """Вызывается, когда бот готов к работе."""
        # await self.restore_mutes_on_startup()

    # @commands.slash_command(name="warn", description="Выдать предупреждение пользователю")
    # async def warn(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        #Проверка на роль модератора
        # if not await self.is_moderator(inter.author):
            # await inter.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)
            # return

        # if not self.db_connection:
            # await inter.response.send_message("Ошибка подключения к базе данных.", ephemeral=True)
            # return

        # with self.db_connection.cursor() as cursor:
            # cursor.execute('''
                # INSERT INTO warns (user_id, guild_id, warn_count, mute_expiry)
                # VALUES (%s, %s, 1, NULL)
                # ON DUPLICATE KEY UPDATE warn_count = warn_count + 1
            # ''', (user.id, inter.guild.id))
            # self.db_connection.commit()

            # cursor.execute('SELECT warn_count FROM warns WHERE user_id = %s AND guild_id = %s', (user.id, inter.guild.id))
            # result = cursor.fetchone()
            # warn_count = result['warn_count'] if result else 0

            # if warn_count >= 3:
                # mute_role = inter.guild.get_role(int(os.getenv('MUTE_ROLE_ID')))
                # if mute_role:
                    # await user.add_roles(mute_role)
                    # mute_expiry = datetime.now() + timedelta(hours=12)
                    # cursor.execute('UPDATE warns SET mute_expiry = %s WHERE user_id = %s AND guild_id = %s', (mute_expiry, user.id, inter.guild.id))
                    # self.db_connection.commit()
                    # await inter.response.send_message(f"{user.mention} получил 3 предупреждения и был замучен на 12 часов.")
                    #Планируем снятие роли через 12 часов
                    # await self.schedule_mute_removal(user.id, inter.guild.id, 12 * 3600)
                # else:
                    # await inter.response.send_message("Роль мута не найдена.", ephemeral=True)
            # else:
                # await inter.response.send_message(f"{user.mention} получил предупреждение. Текущее количество предупреждений: {warn_count}.")

    # @commands.slash_command(name="warns", description="Показать предупреждения пользователя")
    # async def warns(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        # if not self.db_connection:
            # await inter.response.send_message("Ошибка подключения к базе данных.", ephemeral=True)
            # return

        # with self.db_connection.cursor() as cursor:
            # cursor.execute('SELECT warn_count FROM warns WHERE user_id = %s AND guild_id = %s', (user.id, inter.guild.id))
            # result = cursor.fetchone()
            # warn_count = result['warn_count'] if result else 0

            # await inter.response.send_message(f"{user.mention} имеет {warn_count} предупреждений.")

    # @commands.slash_command(name="unwarn", description="Снять одно предупреждение у пользователя")
    # async def unwarn(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        #Проверка на роль модератора
        # if not await self.is_moderator(inter.author):
            # await inter.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)
            # return

        # if not self.db_connection:
            # await inter.response.send_message("Ошибка подключения к базе данных.", ephemeral=True)
            # return

        # with self.db_connection.cursor() as cursor:
            # cursor.execute('SELECT warn_count FROM warns WHERE user_id = %s AND guild_id = %s', (user.id, inter.guild.id))
            # result = cursor.fetchone()
            # if result and result['warn_count'] > 0:
                # cursor.execute('UPDATE warns SET warn_count = warn_count - 1 WHERE user_id = %s AND guild_id = %s', (user.id, inter.guild.id))
                # self.db_connection.commit()
                # await inter.response.send_message(f"Снято одно предупреждение у {user.mention}.")
            # else:
                # await inter.response.send_message(f"У {user.mention} нет предупреждений.", ephemeral=True)

    # @tasks.loop(minutes=1)
    # async def check_mute_expiry(self):
        # if not self.db_connection:
            # return

        # with self.db_connection.cursor() as cursor:
            # cursor.execute('SELECT user_id, guild_id, mute_expiry FROM warns WHERE mute_expiry IS NOT NULL')
            # results = cursor.fetchall()

            # for row in results:
                # user_id = row['user_id']
                # guild_id = row['guild_id']
                # mute_expiry = row['mute_expiry']

                # if datetime.now() >= mute_expiry:
                    # await self.remove_mute_role(user_id, guild_id)

    # def cog_unload(self):
        # self.check_mute_expiry.cancel()
        # if self.db_connection:
            # self.db_connection.close()

# def setup(bot):
    # bot.add_cog(WarnSystem(bot))
