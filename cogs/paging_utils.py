"""
discord bot cog that is used for calculating page addresses in CSS422
"""
import discord
from discord.ext import commands
from lib.src.page_address_calc import AddressParser

class PageUtilsCog:
    def __init__(self, bot):
        self.bot = bot

    # @commands.cooldown(3, 30, commands.BucketType.user)
    @commands.command()
    async def page(self, ctx, *, chip_page_info):
        '''
        '''
        await ctx.send(get_page_addresses(chip_page_info))

def setup(bot):
    """Sets up the cog"""
    bot.add_cog(PageUtilsCog(bot))

def get_page_addresses(exp):
    """Parses a boolean expression and creates a truth table"""
    info_list = exp.split()
    if len(info_list) != 4:
        message = 'Incorrect amount of operants for __page command\n'
        message += 'Correct syntax is "page_bits offset_bits bs_bits page_num"'
        return '```' + message + '```'
    for element in info_list:
        if not element.isdigit():
            return '```All parameters of __page command must be integers!```'
    page_finder= AddressParser(int(info_list[0]),
                               int(info_list[1]),
                               int(info_list[2]))
    result = "```"
    result += page_finder.get_formatted_page_results(int(info_list[3])) + "```"
    return result
