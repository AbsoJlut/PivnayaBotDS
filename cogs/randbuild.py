import disnake
from disnake.ext import commands
import random
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RandBuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.perks = [
            'Связь', 'Прояви себя', 'Лидер', 'Спокойствие духа', 'Железная воля', 'Крушитель', 'Ловкое приземление', 
            'Городской бег', 'Уроки улиц', 'Туз в рукаве', 'Повысить ставки', 'Игра в открытую', 'Познания в ботанике', 
            'Адреналин', 'Быстрый и тихий', 'Решающий удар', 'Объект одержимости', 'Одолженное время', 'Оставленный позади', 
            'Несокрушимый', 'Аптекарь', 'Бессонница', 'Проснись', 'Выдержка', 'Детективное чутье', 'Выслеживание подозреваемого', 
            'Потанцуй со мной', 'Уникальная возможность', 'Через край', 'Диверсия', 'Освобождение', 'Самоучка', 'Уход за больным', 
            'Поломка', 'Искажение', 'Сострадание', 'Сам себе доктор', 'Спринтер', 'Единственный выживший', 'Тревога', 'Гибкость', 
            'Техник', 'Без сожаления', 'Крепкий орешек', 'Мы будем жить вечно', 'Солидарность', 'Равновесие', 'Напролом', 
            'Проверка на прочность', 'Пристегнись', 'Раскачка', 'Нянька', 'Товарищество', 'Второе дыхание', 'Внутренняя сила', 
            'Фиксация', 'Лучше вместе', 'Любыми средствами', 'Форсаж', 'Везение', 'Ради людей', 'Обман во благо', 'Без огласки', 
            'Скрытый союз', 'Кровавый договор', 'Оберег души', 'Визионер', 'Отчаянные меры', 'Строим на века', 'Изучение', 
            'Уловка', 'Отчаянная борьба', 'Самосохранение', 'Ударный забег', 'За чужой счет', 'Стиснув зубы', 'Световая граната', 
            'Дух новичка', 'Противодействие', 'Поправка', 'Фугасная мина', 'Дар уход в тень', 'Дар круг исцеления', 'Ясновидение', 
            'Преодоление', 'Корректировка', 'Дар экспонента', 'Родительская забота', 'Эмпатическая связь', 'Дар теория мрака', 
            'Собранность', 'Остаточное проявление', 'Усердие', 'Жучок', 'Ниже травы', 'Поспешное лечение', 'Полная сосредоточенность', 
            'Ободрение', 'Как новенький', 'Потенциальная энергия', 'Умудренный туманом', 'Быстрый гамбит', 'Дружеское состязание', 
            'Командная работа быстрая пара', 'На волю', 'Запасной игрок', 'Командная работа общая скрытность', 'Выше головы', 
            'Ремонтник', 'Призвание', 'Утилизатор', 'Драматургия', 'Партнер по сцене', 'Вот это поворот', 'Счастливая звезда', 
            'Химическая ловушка', 'Легкоступ', 'Воин света', 'Дар освещение', 'Дедлайн', 'Предчувствие', 'Сила во мраке', 'Дерзость', 
            'Зеркальная иллюзия', 'Вдохновение барда', 'Замри и увидишь', 'Темное чувство', 'Этому не бывать', 'Мелкая дичь', 
            'Мурашки по спине', 'Мы справимся', 'Дежавю', 'Чары пауки', 'Никто не остался позади', 'Мародерское чутье', 'Надежда'
        ]  # Список ваших перков

    @commands.slash_command(description="Составляет билд для DbD")
    async def randombuild(self, ctx):
        try:
            # Выбираем 4 уникальных перка
            selected_perks = random.sample(self.perks, 4)
            perk1, perk2, perk3, perk4 = selected_perks

            # Создаем Embed с информацией о перках
            embed = disnake.Embed(title="🎲 Рандомайзер билдов DbD", color=0x00ff00)
            embed.description = "Вот ваш случайный билд:"

            # Добавляем перки в Embed
            embed.add_field(name="Перк 1", value=perk1, inline=True)
            embed.add_field(name="Перк 2", value=perk2, inline=True)
            embed.add_field(name="Перк 3", value=perk3, inline=True)
            embed.add_field(name="Перк 4", value=perk4, inline=True)

            # Прикрепляем изображения перков
            files = []
            for perk in selected_perks:
                image_path = f'imageperk/{perk}.webp'
                if os.path.exists(image_path):  # Проверяем, существует ли файл
                    file = disnake.File(image_path, filename=f'{perk}.webp')
                    files.append(file)
                    embed.set_image(url=f"attachment://{perk}.webp")  # Устанавливаем изображение для Embed
                else:
                    logger.warning(f"Изображение для перка {perk} не найдено: {image_path}")

            # Отправляем Embed с изображениями
            if files:
                await ctx.send(embed=embed, files=files)
            else:
                await ctx.send("Изображения для перков не найдены.", ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка в команде randombuild: {e}")
            await ctx.send("Произошла ошибка при составлении билда.", ephemeral=True)

def setup(bot):
    bot.add_cog(RandBuild(bot))