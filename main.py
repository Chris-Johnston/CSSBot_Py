# https://github.com/Chris-Johnston/CSSBot_Py

# using the development version from the rewrite branch
# https://github.com/Rapptz/discord.py/tree/rewrite see the readme file for more information
# python3.6 -m pip install -r requirements.txt

# docs
# http://discordpy.readthedocs.io/en/rewrite/
# http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html

# also may need to install libffi-dev, python-dev/python3.6-dev with apt-get
# or equivalent editor

import discord
from discord.ext import commands
import asyncio
# configuration files
import configparser
import sys, traceback

# load configuration to get around hard coded tokens
config = configparser.ConfigParser()
with open('config.ini') as config_file:
    config.read_file(config_file)

# startup stuff
print('discordpy')
print(discord.__version__)

client = commands.Bot(command_prefix='__', description='https://github.com/Chris-Johnston/CssBot-Py')

# this is where extensions are added by default
default_extensions = ['cogs.basic',
                      'cogs.courseInfo',
                      'cogs.number_utils',
                      'cogs.hardware_utils',
                      'cogs.analytics']


if __name__ == '__main__':
    for extension in default_extensions:
        try:
            client.load_extension(extension)
            #client.add_cog(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()


@client.event
async def on_ready():
    # print some stuff when the bot goes online
    print(f'Logged in {client.user.name} - {client.user.id}\nVersion {discord.__version__}')
    await client.change_presence(game=discord.Game(name='Try __help'))

# now actually connect the bot
client.run(config.get(section='Configuration', option='connection_token'),
           bot=True, reconnect=True)
