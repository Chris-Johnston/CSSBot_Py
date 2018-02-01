'''
discord bot cog that is used for automating tedious work in CSS422
'''
from discord.ext import commands
from lib.src.boolean_expr_parser import BooleanExpr
from lib.src.page_address_calc import AddressParser

class HardwareUtilsCog:
    '''
    Collection of discord commands to encapsulate other scripts
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(3, 30, commands.BucketType.user)
    @commands.command()
    async def page(self, ctx, *, chip_page_info):
        '''Calculates the beginning and end address for a page on a memory chip

        List the page bits, offset bits, and byte-selector bits for a memory
        chip, then the page number you want to calculate the addresses for.

        Example:
            For a chip with 2 paging bits, 5 offset bits, 2 byte-selector bits,
            to find the addresses for page number 3 use this command:

            >>> __page 2 5 2 3
        '''
        await ctx.send(get_page_addresses(chip_page_info))

    @commands.cooldown(3, 30, commands.BucketType.user)
    @commands.command()
    async def bool(self, ctx, *, exp):
        '''Creates truth table from expression using !,*,^,+

        Wrap expression in "quotes" to include spaces in your expression.
        If there are spaces in your expression and it is not properly wrapped,
        then it will not process correctly, if at all.

        Single chars are variables, more than one char in a row is invalid.
        More than one ! in a row is invalid... fight me.
        More than 5 variables is invalid, otherwise the messages would be long.
        '''
        await ctx.send(get_bool_table(exp))

def setup(bot):
    '''Sets up the cog'''
    bot.add_cog(HardwareUtilsCog(bot))

def get_page_addresses(exp):
    '''Gets the start and end address for a page on a chip'''
    info_list = exp.split()
    if len(info_list) != 4:
        message = 'Incorrect amount of operants for __page command\n'
        message += 'Correct syntax is "page_bits offset_bits bs_bits page_num"'
        return '```' + message + '```'
    for element in info_list:
        if not element.isdigit():
            return '```All parameters of __page command must be integers!```'
    page_finder = AddressParser(int(info_list[0]),
                                int(info_list[1]),
                                int(info_list[2]))
    result = "```"
    result += page_finder.get_formatted_page_results(int(info_list[3])) + "```"
    return result

def get_bool_table(exp):
    '''Parses a boolean expression and creates a truth table'''
    boolean_exp = BooleanExpr(exp)
    return "```" + boolean_exp.get_truth_table() + "```"
