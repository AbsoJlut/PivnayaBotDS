import disnake
from disnake.ext import commands
import random
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Бросает кубик")
    async def roll(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        sides: int = 20
    ):
        try:
            await interaction.response.defer()

            # Проверка на корректное количество граней
            if sides < 2:
                await interaction.followup.send("Количество граней должно быть не менее 2.", ephemeral=True)
                return

            # Симулируем бросок кубика
            if interaction.author.id == 455315397286035478:  # Пример для специального пользователя (шуточная функция которая позволяет всегда выбрасывать 20)
                result = sides
            else:
                result = random.randint(1, sides)

            # Создаем сообщение с анимацией кубика
            message = await interaction.followup.send("Бросаю кубик...")

            # Анимация кубика
            for _ in range(3):
                await message.edit(content="🎲")
                await asyncio.sleep(0.3)
                await message.edit(content="🎲🎲")
                await asyncio.sleep(0.3)
                await message.edit(content="🎲🎲🎲")
                await asyncio.sleep(0.3)

            # Проверяем на критические удачи и критические неудачи
            if result == sides:
                result_text = f"🎉 Критическая удача! Выпало число: {result}"
            elif result == 1:
                result_text = f"💥 Критическая неудача! Выпало число: {result}"
            else:
                result_text = f"Выпало число: {result}"

            # Отправляем результат
            await message.edit(content=result_text)

        except Exception as e:
            logger.error(f"Ошибка в команде roll: {e}")
            await interaction.followup.send("Произошла ошибка при броске кубика.", ephemeral=True)

def setup(bot):
    bot.add_cog(Roll(bot))