import asyncio
import discord
import os
import math
from discord.ext import commands
from modules.YTDL import YTDL
from modules.BotConfig import BotConfig

def main():
    intents = discord.Intents().all()
    client = discord.Client(intents=intents)
    bot = commands.Bot(command_prefix='!', intents=intents)

    #botConfig = BotConfig("config.config")
    audioCommands = BotConfig("audio_commands.config")

    blockedNames = ['add', 'help', 'list', 'play', 'remove']

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
      
    @bot.command(name='play', help='Solta o som dj')
    async def play(ctx, url):
        channel = ctx.message.author.voice.channel
        voice = await channel.connect()

        async with ctx.typing():
            filename = await YTDL.from_url(url, loop=client.loop)
            voice.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))

        while voice.is_playing():
            await asyncio.sleep(1)

        await voice.disconnect()
    
    @bot.command(name='add', help='Adiciona comando para tocar áudio do youtube')
    async def add(ctx, name, url):
        if name in blockedNames:
            await ctx.send("Você não pode criar um comando com esse nome.")
            return

        serverID = str(ctx.message.guild.id)

        async with ctx.typing():
            filename = await YTDL.from_url(url, loop=client.loop)
        
        if audioCommands.addCommand(serverID, name, filename):
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

        for key in audioCommands.m_config[serverID]:
            members.append(f"- {key} <https://youtu.be/{audioCommands.m_config[serverID][key][6:17]}>")

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
        
        serverID = str(message.guild.id)

        # arrumar essa tramoia aqui dando erro

        if message.content[0] == '!' and message.content[1:] in audioCommands.m_config[serverID]:
            channel = message.author.voice.channel
            voice = await channel.connect()

            voice.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=audioCommands.m_config[serverID][message.content[1:]]))

            while voice.is_playing():
                await asyncio.sleep(1)

            await voice.disconnect()

            return
        
        try:
            await bot.process_commands(message)
        except:
            await message.channel.send(f"Comando não encontrado. Digite !help para ver a lista de comandos disponíveis.")


    bot.run(os.environ['TOKEN'])
    #bot.run(botConfig.getConfig('TOKEN'))

if __name__ == '__main__':
    main()