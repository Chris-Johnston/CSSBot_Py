# https://github.com/Chris-Johnston/CssBot-Py

# python3 -m pip install -U discord.py[voice]
# also may need to install libffi-dev, python-dev/python3.5-dev with apt-get
# or equivalent editor

import discord
import asyncio
# configuration files
import configparser

config = configparser.ConfigParser()
config.read_file(open('config.ini'))

print('discordpy')
print(discord.__version__)

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)

    # set the current game
    client.change_status(game=discord.Game(name='test game'))

@client.event
async def on_message(message):
    print('got message ', message.content)


# now actually connect the bot
client.run(config.get(section='Configuration', option='connection_token'))