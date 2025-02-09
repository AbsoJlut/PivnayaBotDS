import disnake
from disnake.ext import commands
import time

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Проверить пинг до бота")
    async def ping(self, interaction: disnake.ApplicationCommandInteraction):
        start_time = time.time()
        await interaction.response.defer()  # Быстрый отложенный ответ
        end_time = time.time()
        
        latency = round((end_time - start_time) * 1000)  # Задержка до бота
        api_latency = round(self.bot.latency * 1000)  # Задержка до Discord API
        
        await interaction.edit_original_message(content=f"🏓 Понг! Задержка до бота: {latency}мс. Задержка до Discord API: {api_latency}мс.")

def setup(bot):
    bot.add_cog(Ping(bot))