import asyncio
import discord
from discord.ext import commands
from modules.YTDL import YTDL
from modules.BotConfig import BotConfig

def main():
    intents = discord.Intents().all()
    client = discord.Client(intents=intents)
    bot = commands.Bot(command_prefix='!', intents=intents)

    botConfig = BotConfig("config.config")
    audioCommands = BotConfig("audio_commands.config")

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
        serverID = ctx.message.guild.id

        async with ctx.typing():
            filename = await YTDL.from_url(url, loop=client.loop)
        
        audioCommands.addCommand(serverID, name, url)
        await ctx.send(f"{name} adicionado com sucesso!")

    @bot.event
    async def on_message(message):
        if message.author == client.user:
            return
        
        await bot.process_commands(message)


    bot.run(botConfig.getConfig('TOKEN'))

if __name__ == '__main__':
    main()