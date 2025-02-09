# import disnake
# from disnake.ext import commands
# import sqlite3

# class warns(commands.Cog):
    # def __init__(self, bot):
        # self.bot = bot
        # self.conn = sqlite3.connect('warnings.db')
        # self.c = self.conn.cursor()

    # @commands.slash_command(description="Показать все предупреждения пользователя")
    # async def warns(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        # self.c.execute("SELECT warnings FROM warnings WHERE user_id=?", (user.id,))
        # result = self.c.fetchone()
        # if result is None:
            # await inter.response.send_message(f"У пользователя {user.mention} нет предупреждений")
        # else:
            # warnings = eval(result[0])
            # embed = disnake.Embed(title=f"Предупреждения пользователя {user.name}")
            # for i, warning in enumerate(warnings):
                # embed.add_field(name=f"Предупреждение {i+1}", value=f"Причина: {warning}", inline=False)
            # await inter.response.send_message(embed=embed)

# def setup(bot):
    # bot.add_cog(warns(bot))
