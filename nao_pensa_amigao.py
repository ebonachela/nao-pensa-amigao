import asyncio
import discord
import os
import math
import sys
import youtube_dl
import psycopg2
from discord.ext import commands
from modules.YTDL import YTDL
from modules.BotConfig import BotConfig

from youtube_dl import YoutubeDL
from requests import get

def search(arg):
    with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
        try: get(arg)
        except: info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else: info = ydl.extract_info(arg, download=False)
    return (info, info['formats'][0]['url'])

def main():
    intents = discord.Intents().all()
    client = discord.Client(intents=intents)
    bot = commands.Bot(command_prefix='!', intents=intents)

    botConfig = BotConfig("config.config")
    audioCommands = BotConfig("audio_commands.config")

    DATABASE_URL = botConfig.getConfig('DATABASE_URL') if (len(sys.argv) > 1) else os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    # check if table exists
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 from commands')     
        ver = cursor.fetchone()
    except:
        # table not exists yet, so we need to create table
        cursor.execute("ROLLBACK")
        conn.commit()
        cursor.execute('CREATE TABLE commands (serverID varchar(255), command varchar(255), url varchar(255))')  
        conn.commit()
        print('Table commands created in database!')

    cursor.close()
    
    blockedNames = ['add', 'help', 'list', 'play', 'remove']

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')

    @bot.command(name='play', help='Solta o som dj')
    async def play(ctx,*,arg):
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}

        url1 = arg.split(" ")
        url2 = url1[0].replace("[","")
        url = url2.replace("]","")
        
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice is not None:
            if voice.channel != channel:
                await voice.disconnect()
                voice = await channel.connect()
        else:
            voice = await channel.connect()
        ydl = youtube_dl.YoutubeDL(YDL_OPTIONS)
        with ydl:
            info = ydl.extract_info(url, download=False)
            I_URL = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
            voice.play(source)
            voice.is_playing()
    
    @bot.command(name='add', help='Adiciona comando para tocar áudio do youtube')
    async def add(ctx, name, url):
        if name in blockedNames:
            await ctx.send("Você não pode criar um comando com esse nome.")
            return

        serverID = str(ctx.message.guild.id)

        # check if command already exists in database
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT serverid, command, url from commands WHERE serverid = '{serverID}' AND command = '{name}' AND url = '{url}'")  
            ver = cursor.fetchone()
            if(ver is None):
                # add command to database
                cursor.execute("ROLLBACK")
                conn.commit()
                cursor.execute(f"INSERT INTO commands VALUES ('{serverID}', '{name}', '{url}')")
                conn.commit()
                await ctx.send(f"{name} adicionado com sucesso!")
                cursor.close()
                return
        except:
            cursor.close()
            return
        
        cursor.close()

        await ctx.send(f"Erro, comando {name} já existe no servidor!")

    @bot.command(name='remove', help='Remove um comando do servidor.')
    async def remove(ctx, name):
        serverID = str(ctx.message.guild.id)

        # check if command already exists in database
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT serverid, command, url from commands WHERE serverid = '{serverID}' AND command = '{name}'")  
            ver = cursor.fetchone()
            # add command to database
            if(ver is not None):
                cursor.execute("ROLLBACK")
                conn.commit()
                cursor.execute(f"DELETE FROM commands WHERE serverid = '{serverID}' AND command = '{name}'")
                conn.commit()
                await ctx.send(f"{name} removido com sucesso!")
        except:
            cursor.close()
            return

        cursor.close()
        await ctx.send(f"Erro, comando {name} não existe no servidor!")
        
    
    @bot.command(name='list', help='Mostra a lista de comandos existentes no servidor')
    async def list(ctx):
        members = []

        serverID = str(ctx.guild.id)

        # check if command already exists in database
        cursor = conn.cursor()
        arr = []
        try:
            cursor.execute(f"SELECT command, url from commands")  
            arr = cursor.fetchall()
        except:
            await ctx.send('Nenhum comando adicionado até o momento. Utilize !add para adicionar comandos novos.')
            return
        
        cursor.close()

        for element in arr:
            command, url = element
            members.append(f"- {command} <https://youtu.be/{url.split('=')[1]}>")

        if len(members) == 0:
            await ctx.send('Nenhum comando adicionado até o momento. Utilize !add para adicionar comandos novos.')
            return

        members.sort()

        per_page = 10
        pages = math.ceil(len(members) / per_page)
        cur_page = 1
        chunk = members[:per_page]
        linebreak = "\n"
        message = await ctx.send(f"Página {cur_page}/{pages}:\n{linebreak.join(chunk)}")
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        active = True

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

        while active:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
            
                if str(reaction.emoji) == "▶️" and cur_page != pages:
                    cur_page += 1
                    if cur_page != pages:
                        chunk = members[(cur_page-1)*per_page:cur_page*per_page]
                    else:
                        chunk = members[(cur_page-1)*per_page:]
                    await message.edit(content=f"Página {cur_page}/{pages}:\n{linebreak.join(chunk)}")
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "◀️" and cur_page > 1:
                    cur_page -= 1
                    chunk = members[(cur_page-1)*per_page:cur_page*per_page]
                    await message.edit(content=f"Página {cur_page}/{pages}:\n{linebreak.join(chunk)}")
                    await message.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                await message.delete()
                active = False

    @bot.event
    async def on_voice_state_update(member, before, after):
        
        if not member.id == bot.user.id:
            return
        elif before.channel is None:
            voice = after.channel.guild.voice_client
            time = 0
            while True:
                await asyncio.sleep(1)
                time = time + 1
                if voice.is_playing() and not voice.is_paused():
                    time = 0
                if time == 1800:
                    await voice.disconnect()
                if not voice.is_connected():
                    break

    @bot.event
    async def on_message(message):
        if message.author == client.user:
            return
        
        await bot.process_commands(message)

        serverID = str(message.guild.id)
        url = ""

        # check if command already exists in database
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT url from commands WHERE serverid = '{serverID}' AND command = '{message.content[1:]}'")  
            url = cursor.fetchone()[0]
            # command not exists in database
            if(url is None):
                cursor.close()
                return
        except:
            # command not exists in database
            cursor.close()
            return
        
        cursor.close()

        channel = message.author.voice.channel

        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}
        
        voice = discord.utils.get(bot.voice_clients, guild=message.guild)
        if voice is not None:
            if voice.channel != channel or not voice.is_connected():
                await voice.disconnect()
                voice = await channel.connect()
        else:
            voice = await channel.connect()
        ydl = youtube_dl.YoutubeDL(YDL_OPTIONS)
        with ydl:
            info = ydl.extract_info(url, download=False)
            I_URL = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
            voice.play(source)
            voice.is_playing()

        return

    s_TOKEN = botConfig.getConfig('TOKEN') if (len(sys.argv) > 1) else os.environ['TOKEN']
    bot.run(s_TOKEN)

if __name__ == '__main__':
    main()
