import disnake
from disnake.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
import datetime
from yt_dlp import YoutubeDL

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cwd = os.getcwd()
        self.names = {}

        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}
        self.inactivity_tasks = {}

        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'nonplaylist': 'True',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51
        self.embedDarkPink = 0x7d3243

        self.vc = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False
            self.inactivity_tasks[id] = None

            bot_member = guild.get_member(self.bot.user.id)
            nickname = bot_member.nick or bot_member.name
            self.names[id] = nickname

    async def check_inactivity(self, guild_id):
        await asyncio.sleep(300)  # 5 минут
        if self.vc[guild_id] and self.vc[guild_id].is_connected():
            if (not self.is_playing[guild_id] and not self.is_paused[guild_id]) or \
               (len(self.vc[guild_id].channel.members) == 1 and self.vc[guild_id].channel.members[0].id == self.bot.user.id):
                self.is_playing[guild_id] = False
                self.is_paused[guild_id] = False
                self.musicQueue[guild_id] = []
                self.queueIndex[guild_id] = 0
                await self.vc[guild_id].channel.send(f"{self.names[guild_id]} покинул канал из-за неактивности.")
                await self.vc[guild_id].disconnect()
                self.inactivity_tasks[guild_id] = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        id = int(member.guild.id)
        if member.id == self.bot.user.id and before.channel is None and after.channel is not None:
            if self.inactivity_tasks[id]:
                self.inactivity_tasks[id].cancel()
            self.inactivity_tasks[id] = self.bot.loop.create_task(self.check_inactivity(id))
        if member.id != self.bot.user.id and before.channel is not None and after.channel != before.channel:
            if self.vc[id] and self.vc[id].is_connected():
                remaining_members = before.channel.members
                if len(remaining_members) == 1 and remaining_members[0].id == self.bot.user.id:
                    if self.inactivity_tasks[id]:
                        self.inactivity_tasks[id].cancel()
                    self.inactivity_tasks[id] = self.bot.loop.create_task(self.check_inactivity(id))

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            with open('token.txt', 'r') as file:
                lines = file.readlines()
                if len(lines) < 2:
                    raise ValueError("Недостаточно строк в token.txt")
                user_id = int(lines[1].strip())
            if '#poop' in message.content and message.author.id == user_id:
                await message.channel.send("I gotcha fam ;)")
                await self.play_text(message.channel, "https://youtu.be/AkJYdRGu14Y")
        except Exception as e:
            print(f"Ошибка в on_message: {str(e)}")
        os.chdir(self.cwd)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print(f"[{datetime.datetime.now().time()}] {str(error)}")
        await ctx.send(embed=self.error_embed_gen(error))

    def error_embed_gen(self, error):
        embed = disnake.Embed(
            title="ОШИБКА :(",
            description=f"Произошла ошибка. Вы можете продолжать использовать бота.\n\nОшибка:\n**`{str(error)}`**",
            colour=self.embedDarkPink
        )
        return embed

    def generate_embed(self, ctx_or_channel, song, type):
        if isinstance(ctx_or_channel, disnake.TextChannel):
            AUTHOR = ctx_or_channel.guild.me
            AVATAR = AUTHOR.avatar.url if AUTHOR.avatar else AUTHOR.default_avatar.url
        else:
            AUTHOR = ctx_or_channel.author
            AVATAR = AUTHOR.avatar.url if AUTHOR.avatar else AUTHOR.default_avatar.url

        TITLE = song['title']
        LINK = song['link']
        THUMBNAIL = song['thumbnail']
        DURATION = song.get('duration', 0)
        duration_str = f"{DURATION // 60}:{DURATION % 60:02d}"

        if type == 1:
            embed = disnake.Embed(
                title="Сейчас играет",
                description=f'[{TITLE}]({LINK})\nДлительность: {duration_str}',
                colour=self.embedBlue
            )
            embed.set_thumbnail(url=THUMBNAIL)
            embed.set_footer(text=f"Добавил: {str(AUTHOR)}", icon_url=AVATAR)
            return embed

        if type == 2:
            embed = disnake.Embed(
                title="Песня добавлена в очередь!",
                description=f'[{TITLE}]({LINK})\nДлительность: {duration_str}',
                colour=self.embedRed
            )
            embed.set_thumbnail(url=THUMBNAIL)
            embed.set_footer(text=f"Добавил: {str(AUTHOR)}", icon_url=AVATAR)
            return embed

        if type == 3:
            embed = disnake.Embed(
                title="Песня удалена из очереди",
                description=f'[{TITLE}]({LINK})\nДлительность: {duration_str}',
                colour=self.embedRed
            )
            embed.set_thumbnail(url=THUMBNAIL)
            embed.set_footer(text=f"Добавил: {str(AUTHOR)}", icon_url=AVATAR)
            return embed

    async def join_vc(self, ctx_or_channel, channel):
        if isinstance(ctx_or_channel, disnake.TextChannel):
            id = int(ctx_or_channel.guild.id)
            send_func = ctx_or_channel.send
        else:
            id = int(ctx_or_channel.guild.id)
            send_func = ctx_or_channel.edit_original_response

        if self.vc[id] and self.vc[id].is_connected() and self.is_playing[id]:
            if channel != self.vc[id].channel:
                await send_func(content=f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
                return False
            return True

        for guild_id, vc in self.vc.items():
            if guild_id != id and vc and vc.is_connected():
                await send_func(content="Я уже играю в другом голосовом канале на другом сервере.")
                return False

        if self.vc[id] is None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()
            if self.vc[id] is None:
                await send_func(content="Не удалось подключиться к голосовому каналу.")
                return False
        else:
            await self.vc[id].move_to(channel)
        return True

    def get_yt_title(self, video_id):
        params = {"format": "json", "url": f"https://www.youtube.com/watch?v={video_id}"}
        url = "https://www.youtube.com/oembed?" + parse.urlencode(params)
        with request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data['title']

    def search_yt(self, search):
        query_string = parse.urlencode({'search_query': search})
        html_content = request.urlopen(f'http://www.youtube.com/results?{query_string}')
        search_results = re.findall(r'/watch\?v=(.{11})', html_content.read().decode())
        return search_results[:10]

    def extract_yt(self, url):
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
        return {
            'link': f'https://www.youtube.com/watch?v={url}',
            'thumbnail': info['thumbnails'][-1]['url'],
            'source': info['url'],
            'title': info['title'],
            'duration': info.get('duration', 0)
        }

    def play_next(self, ctx_or_channel):
        if isinstance(ctx_or_channel, disnake.TextChannel):
            id = int(ctx_or_channel.guild.id)
            send_func = ctx_or_channel.send
        else:
            id = int(ctx_or_channel.guild.id)
            send_func = ctx_or_channel.edit_original_response

        if not self.is_playing[id]:
            if self.inactivity_tasks[id]:
                self.inactivity_tasks[id].cancel()
            self.inactivity_tasks[id] = self.bot.loop.create_task(self.check_inactivity(id))
            return
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1
            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.generate_embed(ctx_or_channel, song, 1)
            coro = send_func(embed=message)
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            fut.result()
            self.vc[id].play(disnake.FFmpegPCMAudio(song['source'], **self.FFMPEG_OPTIONS), 
                           after=lambda e: self.play_next(ctx_or_channel))
        else:
            coro = send_func(content="Вы дошли до конца очереди!")
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            fut.result()
            self.queueIndex[id] += 1
            self.is_playing[id] = False
            if self.inactivity_tasks[id]:
                self.inactivity_tasks[id].cancel()
            self.inactivity_tasks[id] = self.bot.loop.create_task(self.check_inactivity(id))

    async def play_music(self, ctx_or_channel):
        if isinstance(ctx_or_channel, disnake.TextChannel):
            id = int(ctx_or_channel.guild.id)
            send_func = ctx_or_channel.send
        else:
            id = int(ctx_or_channel.guild.id)
            send_func = ctx_or_channel.edit_original_response

        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False
            if self.inactivity_tasks[id]:
                self.inactivity_tasks[id].cancel()
            self.inactivity_tasks[id] = None
            await self.join_vc(ctx_or_channel, self.musicQueue[id][self.queueIndex[id]][1])
            if self.vc[id] and self.vc[id].is_connected():  # Убедимся, что бот подключён
                song = self.musicQueue[id][self.queueIndex[id]][0]
                message = self.generate_embed(ctx_or_channel, song, 1)
                await send_func(embed=message)
                self.vc[id].play(disnake.FFmpegPCMAudio(song['source'], **self.FFMPEG_OPTIONS), 
                                after=lambda e: self.play_next(ctx_or_channel))
            else:
                await send_func(content="Не удалось начать воспроизведение: бот не подключён к каналу.")
        else:
            await send_func(content="В очереди нет песен для воспроизведения.")
            self.queueIndex[id] += 1
            self.is_playing[id] = False
            if self.inactivity_tasks[id]:
                self.inactivity_tasks[id].cancel()
            self.inactivity_tasks[id] = self.bot.loop.create_task(self.check_inactivity(id))

    async def play_text(self, channel, search):
        id = int(channel.guild.id)
        try:
            user_channel = channel.guild.me.voice.channel if channel.guild.me.voice else None
            if not user_channel:
                await channel.send("Я должен быть в голосовом канале для воспроизведения.")
                return
        except AttributeError:
            await channel.send("Я должен быть в голосовом канале для воспроизведения.")
            return

        search_results = self.search_yt(search)
        for i in range(10):
            song = self.extract_yt(search_results[i])
            if song and not ("shopify" in song['title'].lower()):
                break
        if not song:
            await channel.send("Не удалось загрузить песню. Неверный формат, попробуйте другой запрос.")
            return
        self.musicQueue[id].append([song, user_channel])
        if self.is_paused[id]:
            await channel.send("Аудио возобновлено!")
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()
        if not self.is_playing[id]:
            await self.play_music(channel)
        else:
            message = self.generate_embed(channel, song, 2)
            await channel.send(embed=message)

    async def check_user_channel(self, ctx):
        """Проверка, находится ли пользователь в том же канале, что и бот, если бот играет."""
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except AttributeError:
            return None
        
        if self.vc[id] and self.vc[id].is_connected() and self.is_playing[id]:
            if user_channel != self.vc[id].channel:
                return None
        return user_channel

    @commands.slash_command(name="play", description="Воспроизвести музыку или добавить в очередь")
    async def play(self, ctx, *, args=None):
        await ctx.response.defer()
        id = int(ctx.guild.id)
        user_channel = await self.check_user_channel(ctx)
        if user_channel is None:
            if not ctx.author.voice:
                await ctx.edit_original_response(content="Вы должны быть подключены к голосовому каналу.")
            else:
                await ctx.edit_original_response(content=f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
            return

        if not args:
            if self.is_playing[id] and self.vc[id] and self.vc[id].is_connected():
                await ctx.edit_original_response(content=f"Музыка уже играет в {self.vc[id].channel.name}.")
            elif self.musicQueue[id]:  # Если очередь не пуста, начинаем воспроизведение
                await self.play_music(ctx)
            else:
                await ctx.edit_original_response(content="Очередь пуста.")
            return
        else:
            search_results = self.search_yt(args)
            for i in range(10):
                song = self.extract_yt(search_results[i])
                if song and not ("shopify" in song['title'].lower()):
                    break
            if not song:
                await ctx.edit_original_response(content="Не удалось загрузить песню. Неверный формат, попробуйте другой запрос.")
                return
            self.musicQueue[id].append([song, user_channel])
            if self.is_paused[id]:
                await ctx.edit_original_response(content="Аудио возобновлено!")
                self.is_playing[id] = True
                self.is_paused[id] = False
                self.vc[id].resume()
            elif not self.is_playing[id]:
                await self.play_music(ctx)
            else:
                message = self.generate_embed(ctx, song, 2)
                await ctx.edit_original_response(embed=message)

    @commands.slash_command(name="add", description="Добавить музыку в очередь")
    async def add(self, ctx, *, args):
        await ctx.response.defer()
        id = int(ctx.guild.id)
        user_channel = await self.check_user_channel(ctx)
        if user_channel is None:
            if not ctx.author.voice:
                await ctx.edit_original_response(content="Вы должны быть подключены к голосовому каналу.")
            else:
                await ctx.edit_original_response(content=f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
            return

        song = self.extract_yt(self.search_yt(args)[0])
        if not song:
            await ctx.edit_original_response(content="Не удалось загрузить песню. Неверный формат, попробуйте другой запрос.")
            return
        self.musicQueue[id].append([song, user_channel])
        message = self.generate_embed(ctx, song, 2)
        await ctx.edit_original_response(embed=message)

    @commands.slash_command(name="remove", description="Удалить последнюю песню из очереди")
    async def remove(self, ctx):
        await ctx.response.defer()
        id = int(ctx.guild.id)
        user_channel = await self.check_user_channel(ctx)
        if user_channel is None:
            if not ctx.author.voice:
                await ctx.edit_original_response(content="Вы должны быть подключены к голосовому каналу.")
            else:
                await ctx.edit_original_response(content=f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
            return

        if self.musicQueue[id]:
            song = self.musicQueue[id][-1][0]
            remove_song_embed = self.generate_embed(ctx, song, 3)
            self.musicQueue[id].pop()
            if not self.musicQueue[id]:
                if self.vc[id] and self.is_playing[id]:
                    self.is_playing[id] = False
                    self.is_paused[id] = False
                    self.vc[id].stop()
                self.queueIndex[id] = 0
            elif self.queueIndex[id] == len(self.musicQueue[id]) and self.vc[id]:
                self.vc[id].pause()
                self.queueIndex[id] -= 1
                await self.play_music(ctx)
            await ctx.edit_original_response(embed=remove_song_embed)
        else:
            await ctx.edit_original_response(content="В очереди нет песен для удаления.")

    @commands.slash_command(name="pause", description="Приостановить воспроизведение")
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Вы должны быть подключены к голосовому каналу.")
            return
        
        if self.vc[id] and self.vc[id].is_connected() and self.is_playing[id]:
            if user_channel != self.vc[id].channel:
                await ctx.send(f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
                return

        if not self.vc[id]:
            await ctx.send("Сейчас нет аудио для остановки.")
        elif self.is_paused[id]:
            await ctx.send("Музыка уже на паузе.")
        elif self.is_playing[id]:
            await ctx.send("Аудио приостановлено!")
            self.is_playing[id] = False
            self.is_paused[id] = True
            self.vc[id].pause()

    @commands.slash_command(name="resume", description="Возобновить воспроизведение")
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Вы должны быть подключены к голосовому каналу.")
            return
        
        if self.vc[id] and self.vc[id].is_connected() and self.is_playing[id]:
            if user_channel != self.vc[id].channel:
                await ctx.send(f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
                return

        if not self.vc[id]:
            await ctx.send("Сейчас нет аудио для воспроизведения.")
        elif self.is_playing[id]:
            await ctx.send("Музыка уже воспроизводится.")
        elif self.is_paused[id]:
            await ctx.send("Аудио возобновлено!")
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()

    @commands.slash_command(name="previous", description="Воспроизвести предыдущую песню")
    async def previous(self, ctx):
        await ctx.response.defer()
        id = int(ctx.guild.id)
        user_channel = await self.check_user_channel(ctx)
        if user_channel is None:
            if not ctx.author.voice:
                await ctx.edit_original_response(content="Вы должны быть подключены к голосовому каналу.")
            else:
                await ctx.edit_original_response(content=f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
            return

        if not self.vc[id]:
            await ctx.edit_original_response(content="Вы должны быть в голосовом канале.")
        elif self.queueIndex[id] <= 0:
            await ctx.edit_original_response(content="Нет предыдущей песни. Повтор текущей.")
            self.vc[id].pause()
            await self.play_music(ctx)
        else:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
            await self.play_music(ctx)

    @commands.slash_command(name="skip", description="Пропустить текущую песню")
    async def skip(self, ctx):
        await ctx.response.defer()
        id = int(ctx.guild.id)
        user_channel = await self.check_user_channel(ctx)
        if user_channel is None:
            if not ctx.author.voice:
                await ctx.edit_original_response(content="Вы должны быть подключены к голосовому каналу.")
            else:
                await ctx.edit_original_response(content=f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
            return

        if not self.vc[id]:
            await ctx.edit_original_response(content="Вы должны быть в голосовом канале.")
        elif self.queueIndex[id] >= len(self.musicQueue[id]) - 1:
            await ctx.edit_original_response(content="Нет следующей песни. Повтор текущей.")
            self.vc[id].pause()
            await self.play_music(ctx)
        else:
            self.vc[id].pause()
            self.queueIndex[id] += 1
            await self.play_music(ctx)

    @commands.slash_command(name="queue", description="Показать текущую очередь")
    async def queue(self, ctx):
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Вы должны быть подключены к голосовому каналу.")
            return
        
        if self.vc[id] and self.vc[id].is_connected() and self.is_playing[id]:
            if user_channel != self.vc[id].channel:
                await ctx.send(f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
                return

        if not self.musicQueue[id]:
            await ctx.send("В очереди нет песен.")
            return
        if len(self.musicQueue[id]) <= self.queueIndex[id]:
            await ctx.send("Вы дошли до конца очереди.")
            return
        return_value = ""
        for i in range(self.queueIndex[id], min(self.queueIndex[id] + 5, len(self.musicQueue[id]))):
            song = self.musicQueue[id][i][0]
            duration = song.get('duration', 0)
            duration_str = f"{duration // 60}:{duration % 60:02d}"
            return_index = "Играет" if i == self.queueIndex[id] else "Следующая" if i == self.queueIndex[id] + 1 else str(i - self.queueIndex[id])
            return_value += f"{return_index} - [{song['title']}]({song['link']}) [{duration_str}]\n"
        queue = disnake.Embed(
            title="Текущая очередь",
            description=return_value,
            colour=self.embedGreen
        )
        await ctx.send(embed=queue)

    @commands.slash_command(name="clear", description="Очистить очередь")
    async def clear(self, ctx):
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Вы должны быть подключены к голосовому каналу.")
            return
        
        if self.vc[id] and self.vc[id].is_connected() and self.is_playing[id]:
            if user_channel != self.vc[id].channel:
                await ctx.send(f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
                return

        if self.musicQueue[id]:
            if self.vc[id] and self.is_playing[id]:
                self.is_playing[id] = False
                self.is_paused[id] = False
                self.vc[id].stop()
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            await ctx.send("Очередь очищена.")
        else:
            await ctx.send("Очередь уже пуста.")

    @commands.slash_command(name="join", description="Подключиться к голосовому каналу")
    async def join(self, ctx):
        id = int(ctx.guild.id)
        if not ctx.author.voice:
            await ctx.send("Вы должны быть подключены к голосовому каналу.")
            return
        
        user_channel = ctx.author.voice.channel
        if self.vc[id] and self.vc[id].is_connected():
            if self.is_playing[id] and user_channel != self.vc[id].channel:
                await ctx.send(f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
                return
            elif user_channel == self.vc[id].channel:
                await ctx.send(f"Я уже подключён к {self.vc[id].channel.name}.")
                return

        if await self.join_vc(ctx, user_channel):
            await ctx.send(f"{self.names[id]} подключился к {user_channel}!")

    @commands.slash_command(name="leave", description="Покинуть голосовой канал")
    async def leave(self, ctx):
        id = int(ctx.guild.id)
        try:
            user_channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Вы должны быть подключены к голосовому каналу.")
            return
        
        if self.vc[id] and self.vc[id].is_connected() and self.is_playing[id]:
            if user_channel != self.vc[id].channel:
                await ctx.send(f"Я уже играю в {self.vc[id].channel.name}. Присоединяйтесь туда, чтобы управлять музыкой.")
                return
        elif not self.vc[id] or not self.vc[id].is_connected():
            await ctx.send("Я уже не в голосовом канале.")
            return

        self.is_playing[id] = False
        self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex[id] = 0
        if self.vc[id]:
            await ctx.send(f"{self.names[id]} покинул здание! Очередь также очищена.")
            await self.vc[id].disconnect()
            if self.inactivity_tasks[id]:
                self.inactivity_tasks[id].cancel()
            self.inactivity_tasks[id] = None

def setup(bot):
    bot.add_cog(Music(bot))