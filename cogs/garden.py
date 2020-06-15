import discord
from discord.ext import commands
import random

class TinyGarden(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.filler = u'\U0001F331' # 🌱seedling
        self.flowers = [
                u'\U0001F33A', # 🌺 hibiscus
                u'\U0001F33B', # 🌻 sunflower
                u'\U0001F33C', # 🌼 daisy
                u'\U0001F337', # 🌷 tulip
                u'\U0001F335', # 🌵 cactus
                u'\U0001F339', # 🌹 rose
                u'\U0001F338'  # 🌸 cherry blossom
            ]
        self.plants = [
                u'\U0001F33F', # 🌿 herb
                u'\U00002618', # ☘️ shamrock
                u'\U0001F340', # 🍀 4-leaf clover
                u'\U0001F333', # 🌳 deciduous tree
                u'\U0001F332'  # 🌲 evergreen tree
            ]
        self.vegetables = [
                u'\U0001F344', # 🍄 musroom
                u'\U0001F955', # 🥕 carrot 
                u'\U0001F345', # 🍅 tomato
                u'\U0001F351', # 🍑 peach
                u'\U0001F352', # 🍒 cherries
                u'\U0001F353'  # 🍓 strawberry
            ]
        self.animals = [
                u'\U0001F41D', # 🐝 bee
                u'\U0001F41B', # 🐛 bug
                u'\U0001F99A', # 🦚 peacock
                u'\U0001F41E', # 🐞 ladybug
                u'\U0001F98B', # 🦋 butterfly
                u'\U0001F426', # 🐦 bird
                u'\U0001F40C'  # 🐌 snail
            ]

    # ping command
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='garden')
    async def make_tiny_garden(self, ctx):
        async with ctx.channel.typing():
            # 8x8 grid: 64 choices
            # 16-24 flowers
            # 1-3 animals
            # 3-5 vegetables
            # 5-15 plants
            # 
            # begin as single-dimension list, wrap when sending message
            garden = [ u'' for i in range(64) ]

            # add the planti bois
            idx = 0
            # flowers first
            for i in range(random.randint(16, 24)):
                garden[idx] = random.choice(self.flowers)
                idx += 1
            # then animals
            for i in range(random.randint(1, 3)):
                garden[idx] = random.choice(self.animals)
                idx += 1
            # vegertals
            for i in range(random.randint(5, 10)):
                garden[idx] = random.choice(self.vegetables)
                idx += 1
            # other green leafy things
            for i in range(random.randint(5, 15)):
                garden[idx] = random.choice(self.plants)
                idx += 1
            # fill remaining array with seedlings
            for i in range(idx, 64):
                garden[idx] = self.filler

            # shuffle and assemble garden
            random.shuffle(garden)
            for i in range(8):
                garden[i * 8 + 7] = garden[i * 8 + 7] + '\n'
            ctx.send(''.join(garden))

def setup(bot):
    bot.add_cog(TinyGarden(bot))

if __name__=='__main__':
    import doctest
    doctest.testmod()
