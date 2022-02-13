import discord
from modules.BotConfig import BotConfig

def main():
    client = discord.Client()

    botConfig = BotConfig("config.config")

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        print(message.content)

    client.run(botConfig.getConfig('TOKEN'))

if __name__ == '__main__':
    main()