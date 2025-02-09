import disnake
from disnake.ext import commands
import pymysql
import os
from dotenv import load_dotenv
from disnake.ext.commands import MissingPermissions

# Загружаем переменные из .env
load_dotenv()

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = None
        self.cursor = None

    async def connect_to_mysql(self):
        """Подключение к MySQL."""
        try:
            self.conn = pymysql.connect(
                host=os.getenv('MYSQL_HOST'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                database=os.getenv('MYSQL_DB_rolles'),
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
            print("Успешное подключение к MySQL")
        except pymysql.Error as e:
            print(f"Ошибка подключения к MySQL: {e}")

    async def ensure_custom_roles_position(self, guild):
        """Проверяет и корректирует позиции всех кастомных ролей."""
        # Получаем роли бустеров и стандартной роли
        booster_role = disnake.utils.get(guild.roles, name="мажор(бубустер)")  # Убедитесь, что название роли точное. Высшая роль ниже которой будут кастом роли
        default_role = disnake.utils.get(guild.roles, name="Ботяры")  # Убедитесь, что название роли точное. Нисшая роль выше которой будут кастом роли

        if not booster_role or not default_role:
            print("Роли бустеров или стандартной роли не найдены.")
            return

        # Получаем список всех ролей на сервере
        all_roles = await guild.fetch_roles()

        # Проходим по всем ролям
        for role in all_roles:
            # Проверяем, является ли роль кастомной (созданной ботом)
            self.cursor.execute("SELECT role_name FROM roles WHERE role_name = %s", (role.name,))
            if self.cursor.fetchone():
                # Проверяем, находится ли роль ниже стандартной роли
                if role.position < default_role.position:
                    # Поднимаем роль выше стандартной роли
                    await role.edit(position=default_role.position + 1)
                    print(f"Роль {role.name} была поднята выше стандартной роли.")

                # Проверяем, находится ли роль выше роли бустеров
                if role.position > booster_role.position:
                    # Опускаем роль ниже роли бустеров
                    await role.edit(position=booster_role.position - 1)
                    print(f"Роль {role.name} была опущена ниже роли бустеров.")

    @commands.slash_command(description="Создать кастомную роль")
    async def setrole(
        self,
        ctx,
        role_name: str,
        color: str = None  # Необязательный аргумент для цвета в HEX-формате
    ):
        # Откладываем ответ, чтобы избежать InteractionTimedOut
        await ctx.response.defer(ephemeral=True)

        if self.conn is None:
            await self.connect_to_mysql()

        if self.conn is None:
            await ctx.edit_original_response(content='Ошибка подключения к базе данных.')
            return

        # Проверка длины названия роли
        if len(role_name) < 3 or len(role_name) > 20:
            await ctx.edit_original_response(content="Название роли должно быть от 3 до 20 символов.")
            return

        # Проверяем, есть ли у пользователя уже роль
        self.cursor.execute("SELECT role_name FROM roles WHERE user_id = %s", (ctx.author.id,))
        existing_role = self.cursor.fetchone()

        if existing_role:
            await ctx.edit_original_response(content="У вас уже есть кастомная роль. Вы не можете создать более одной роли. Используйте /renrole для переименования.")
            return

        # Преобразуем HEX-цвет в disnake.Color
        role_color = disnake.Color.default()  # По умолчанию цвет роли
        if color:
            try:
                role_color = disnake.Color(int(color.lstrip("#"), 16))  # Преобразуем HEX в int
            except ValueError:
                await ctx.edit_original_response(content="Некорректный формат цвета. Используйте HEX-формат (например, #FF0000).")
                return

        # Получаем роль бустеров
        booster_role = disnake.utils.get(ctx.guild.roles, name="мажор(бубустер)")  # Убедитесь, что название роли точное

        if not booster_role:
            await ctx.edit_original_response(content="Роль бустеров не найдена. Обратитесь к администратору.")
            return

        # Создаем новую роль с указанным цветом и hoist=True
        role = await ctx.guild.create_role(name=role_name, color=role_color, hoist=True)

        # Устанавливаем позицию новой роли ниже роли бустеров
        await role.edit(position=booster_role.position - 1)

        # Выдаем роль пользователю
        await ctx.author.add_roles(role)

        # Сохраняем название роли в базе данных
        self.cursor.execute("INSERT INTO roles (user_id, role_name) VALUES (%s, %s)", (ctx.author.id, role_name))
        self.conn.commit()

        # Проверяем и корректируем позиции всех кастомных ролей
        await self.ensure_custom_roles_position(ctx.guild)

        await ctx.edit_original_response(content=f'Вы получили роль: {role_name}')

    @commands.slash_command(description="Переименовать кастомную роль")
    async def renrole(
        self,
        ctx,
        new_role_name: str,
        new_color: str = None  # Необязательный аргумент для нового цвета в HEX-формате
    ):
        # Откладываем ответ, чтобы избежать InteractionTimedOut
        await ctx.response.defer(ephemeral=True)

        if self.conn is None:
            await self.connect_to_mysql()

        if self.conn is None:
            await ctx.edit_original_response(content='Ошибка подключения к базе данных.')
            return

        # Проверка длины нового названия роли
        if len(new_role_name) < 3 or len(new_role_name) > 20:
            await ctx.edit_original_response(content="Название роли должно быть от 3 до 20 символов.")
            return

        # Проверяем, есть ли у пользователя кастомная роль
        self.cursor.execute("SELECT role_name FROM roles WHERE user_id = %s", (ctx.author.id,))
        existing_role = self.cursor.fetchone()

        if not existing_role:
            await ctx.edit_original_response(content="У вас нет кастомной роли для переименования.")
            return

        # Получаем текущую роль пользователя
        role = disnake.utils.get(ctx.guild.roles, name=existing_role['role_name'])
        if role:
            # Переименовываем роль
            await role.edit(name=new_role_name)

            # Если указан новый цвет, обновляем цвет роли
            if new_color:
                try:
                    new_role_color = disnake.Color(int(new_color.lstrip("#"), 16))  # Преобразуем HEX в int
                    await role.edit(color=new_role_color)
                except ValueError:
                    await ctx.edit_original_response(content="Некорректный формат цвета. Используйте HEX-формат (например, #FF0000).")
                    return

            # Проверяем и корректируем позиции всех кастомных ролей
            await self.ensure_custom_roles_position(ctx.guild)

            # Обновляем название роли в базе данных
            self.cursor.execute("UPDATE roles SET role_name = %s WHERE user_id = %s", (new_role_name, ctx.author.id))
            self.conn.commit()

            await ctx.edit_original_response(content=f'Ваша роль была переименована на: {new_role_name}')
        else:
            await ctx.edit_original_response(content="Роль не найдена на сервере.")

    @commands.has_permissions(administrator=True)
    @commands.slash_command(description="Инициализация системы ролей")
    async def rstart(self, ctx):
        # Откладываем ответ, чтобы избежать InteractionTimedOut
        await ctx.response.defer(ephemeral=True)

        await self.connect_to_mysql()

        if self.conn is None:
            await ctx.edit_original_response(content='Ошибка подключения к базе данных.')
            return

        # Создаем таблицу, если её нет
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                user_id BIGINT PRIMARY KEY,
                role_name VARCHAR(255) NOT NULL
            )
        ''')
        self.conn.commit()

        await ctx.edit_original_response(embed=disnake.Embed(
            title="Успех",
            colour=0x2F3136,
            description="Система ролей инициализирована. Таблица создана или уже существует."
        ))

    @rstart.error
    async def rstart_error(self, ctx, error):
        """Обработка ошибки отсутствия прав для команды /rstart."""
        if isinstance(error, MissingPermissions):
            await ctx.send("У вас недостаточно прав для выполнения этой команды. Требуются права администратора.", ephemeral=True)

    def cog_unload(self):
        """Закрываем соединение с базой данных при выгрузке кога."""
        if self.conn:
            self.cursor.close()
            self.conn.close()
            print("Соединение с MySQL закрыто.")

def setup(bot):
    bot.add_cog(Roles(bot))