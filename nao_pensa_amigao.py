import discord, asyncio
from modules.YTDL import YTDL
from discord.ext import commands
from modules.BotConfig import BotConfig

from time import sleep

def main():
    intents = discord.Intents().all()
    client = discord.Client(intents=intents)
    bot = commands.Bot(command_prefix='!', intents=intents)

    botConfig = BotConfig("config.config")

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
      
    @bot.command(name='play', help='Play youtube song')
    async def play(ctx, url):
        channel = ctx.message.author.voice.channel
        voice = await channel.connect()

        async with ctx.typing():
            filename = await YTDL.from_url(url, loop=client.loop)
            sleep(1)
            voice.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))

        while voice.is_playing():
            await asyncio.sleep(1)

        await voice.disconnect()


    bot.run(botConfig.getConfig('TOKEN'))

if __name__ == '__main__':
    main()