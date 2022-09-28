import asyncio
import discord
import os
import math
import sys
import youtube_dl
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
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        ydl = youtube_dl.YoutubeDL(YDL_OPTIONS)
        with ydl:
            info = ydl.extract_info(url, download=False)
            I_URL = info['formats'][0]['url']
            print(I_URL)
            source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
            voice.play(source)
            while voice.is_playing():
                await asyncio.sleep(1)

            await voice.disconnect()
    
    @bot.command(name='add', help='Adiciona comando para tocar áudio do youtube')
    async def add(ctx, name, url):
        if name in blockedNames:
            await ctx.send("Você não pode criar um comando com esse nome.")
            return

        serverID = str(ctx.message.guild.id)
        
        if audioCommands.addCommand(serverID, name, url):
            await ctx.send(f"{name} adicionado com sucesso!")
            return
        
        await ctx.send(f"Erro, comando {name} já existe no servidor!")

    @bot.command(name='remove', help='Remove um comando do servidor.')
    async def remove(ctx, name):
        serverID = str(ctx.message.guild.id)

        if audioCommands.removeCommand(serverID, name):
            await ctx.send(f"{name} removido com sucesso!")
            return
        
        await ctx.send(f"Erro, comando {name} não existe no servidor!")
    
    @bot.command(name='list', help='Mostra a lista de comandos existentes no servidor')
    async def list(ctx):
        members = []

        serverID = str(ctx.guild.id)

        if serverID not in audioCommands.m_config:
            await ctx.send('Nenhum comando adicionado até o momento. Utilize !add para adicionar comandos novos.')
            return

        for key in audioCommands.m_config[serverID]:
            members.append(f"- {key} {audioCommands.m_config[serverID][key]}")

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
    async def on_message(message):
        if message.author == client.user:
            return
        
        await bot.process_commands(message)

        serverID = str(message.guild.id)

        if serverID not in audioCommands.m_config:
            return

        if message.content[0] == '!' and message.content[1:] in audioCommands.m_config[serverID]:
            channel = message.author.voice.channel
            url = audioCommands.m_config[serverID][message.content[1:]]

            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

            YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}
            
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                voice = await channel.connect()
            ydl = youtube_dl.YoutubeDL(YDL_OPTIONS)
            with ydl:
                info = ydl.extract_info(url, download=False)
                I_URL = info['formats'][0]['url']
                print(I_URL)
                source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
                voice.play(source)
                while voice.is_playing():
                    await asyncio.sleep(1)

                await voice.disconnect()

            return

    s_TOKEN = botConfig.getConfig('TOKEN') if (len(sys.argv) > 1)  else os.environ['TOKEN']
    bot.run(s_TOKEN)

if __name__ == '__main__':
    main()
