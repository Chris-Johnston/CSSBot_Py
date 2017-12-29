# https://github.com/Chris-Johnston/CssBot-Py

# using the development version from the rewrite branch
# https://github.com/Rapptz/discord.py/tree/rewrite see the readme file for more information
# python3 -m pip install -U https://github.com/Rapptz/discord.py/archive/master.zip#egg=discord.py[voice]

# also may need to install libffi-dev, python-dev/python3.5-dev with apt-get
# or equivalent editor

import discord
from discord.ext import commands
import asyncio
# configuration files
import configparser

# load configuration to get around hard coded tokens
config = configparser.ConfigParser()
config.read_file(open('config.ini'))

# startup stuff
print('discordpy')
print(discord.__version__)

# use a commands bot instead of discord client because this offers utility functions
# that do work for the client
client = commands.Bot(command_prefix='_', description='This is a test or something.')

async def invalid_command():
    print('invalid command')

@client.event
async def on_ready():
    print('Logged in as', client.user.name)
    # set the current game
    # set the url to the repo. the url doesn't appear to do anything, meant for streamers
    await client.change_presence(
        game=discord.Game(name='test game', url='https://github.com/Chris-Johnston/CssBot-Py')
    )

@client.event
async def on_message(message):
    print('got a message')

# now actually connect the bot
client.run(config.get(section='Configuration', option='connection_token'))