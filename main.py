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
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter

log_format = "%(levelname)s %(filename)s:%(lineno)d %(funcName)s %(message)s"
logging.basicConfig(format=log_format)  # have to set log level for each logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# load configuration to get around hard coded tokens
config = configparser.ConfigParser()
with open('config.ini') as config_file:
    config.read_file(config_file)

if config.has_option('Configuration', 'azure_log'):
    logger.addHandler(AzureLogHandler(
        connection_string=config["Configuration"]["azure_log"]
    ))
    # the default metrics exporter will include
    # stats like memory, CPU, etc
    exporter = metrics_exporter.new_metrics_exporter(
        connection_string=config["Configuration"]["azure_log"]    
    )

# startup stuff
print('discordpy')
print(discord.__version__)

client = commands.Bot(command_prefix='>>', description='https://github.com/Chris-Johnston/CssBot-Py', case_insensitive=True)

# this is where extensions are added by default
default_extensions = ['cogs.basic',
                      'cogs.courseInfo',
                      'cogs.number_utils',
                      'cogs.hardware_utils',
                      'cogs.analytics',
                      'cogs.gpa',
                      'cogs.manpage',
                      'cogs.markov',
                      'cogs.hyphen',
                      'cogs.crob',
                      'cogs.starboard',
                      'cogs.advent',
                      'cogs.drinking_game',
                      'cogs.garden',
                      'cogs.aroundtheworld',
                      'cogs.fifth_glyph',
                      'cogs.cat',
                      'cogs.invite_checker',
                      'cogs.death_to_stickers']


if __name__ == '__main__':
    for extension in default_extensions:
        try:
            client.load_extension(extension)
        except Exception as e:
            logger.error(f"Failed to load extension {extension}.", exc_info=e)
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()


@client.event
async def on_ready():
    logger.warn("Ready event handler")
    # print some stuff when the bot goes online
    print(f'Logged in {client.user.name} - {client.user.id}\nVersion {discord.__version__}')
    await client.change_presence(activity=discord.Game(name='Try >>help'))

@client.event
async def on_connect():
    logger.info("Connected.")

@client.event
async def on_resumed():
    logger.warn("Session resumed.")

@client.event
async def on_disconnect():
    logger.warn("Disconnected.")

@client.event
async def on_error(event):
    logger.error(f"Event {event} errored.", exc_info=sys.exec_info())

@client.event
async def on_guild_available(guild):
    logger.info(f"Guild {guild.id} ({guild.name}) available.")

@client.event
async def on_guild_unavailable(guild):
    logger.info(f"Guild {guild.id} ({guild.name}) unavailable.")

# now actually connect the bot
client.run(config.get(section='Configuration', option='connection_token'),
           bot=True, reconnect=True)
