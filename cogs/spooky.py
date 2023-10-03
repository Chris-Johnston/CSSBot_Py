from discord.ext import commands
import discord
import configparser
import random
import asyncio
import logging
import time
import datetime
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# hardcoding files because I am lazy and I do not care
spooky_phrases_file = "spooky_phrases.txt"
spooky_state_file = "spooky_state.json"
lazy_admins = [163184946742034432, 234840886519791616]

from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class User:
    display_name: str
    ghoultokens: int
    skelecoin: int

@dataclass_json
@dataclass
class State:
    last_updated: int # timestamp
    # keyed by userid, value is User
    users: dict

class SpookyMonth(commands.Cog):
    """
    SpooOOOOooOOOoookyyyyyy!
    """

    def __init__(self, bot):

        now = datetime.datetime.now()
        allow_spooky = True

        if now.month != 10:
            # 3 day grace period
            if now.month == 11 and now.day < 3:
                # ok
                allow_spooky = True
                pass
            else:
                allow_spooky = False

        # I'm pretty sure I restart this bot daily so this should do
        if not(allow_spooky):
            logger.info("date is not in spooky month range, so not running")
            return
        
        # keyed by user Id, with a dict for the attributes for each user
        self.state_mutex = asyncio.Lock()
        # running an old version of python oh well

        loops = asyncio.get_event_loop()
        loops.run_until_complete(self.read_state())
        # asyncio.run(self.read_state())

        with open(spooky_phrases_file, 'rt') as s:
            target_phrases = s.readlines()
            self.target_phrases = [x.strip() for x in target_phrases]
        
        self.bonus_phrase = random.choice(target_phrases)
        logger.info("read the phrases from the spooky phrase file")
    
    # who needs a database, json is MY database
    async def read_state(self):
        logger.info("reading state from file at time")
        try:
            async with self.state_mutex:
                with open(spooky_state_file, 'rt') as s:
                    self.state = State.from_json(s.read())
            logger.info("done reading state file")
        except Exception as e:
            logger.warn(f"could not read state file, initializing empty one {e}")
            self.state = State(time.time(), {})
            await self.write_state()
    
    async def write_state(self):
        logger.info("updating state")
        try:
            async with self.state_mutex:
                with open(spooky_state_file, 'wt') as s:
                    json_text = self.state.to_json()
                    s.write(json_text)
        except Exception as e:
            logger.warn("failed to write state for some reason idk", e)
    
    # the good stuff
    async def update_user(self, user_id, delta_ghoultokens, delta_skelecoin):
        logger.info(f"update user_id {user_id} ghoul {delta_ghoultokens} skele {delta_skelecoin}")
        if user_id in self.state:
            # update existing
            if delta_ghoultokens is not None:
                self.state[user_id].ghoultokens += delta_ghoultokens
            if delta_skelecoin is not None:
                self.state[user_id].skelecoin += delta_skelecoin
        else:
            # new user
            logger.info(f"new user user_id {user_id}")
            self.state[user_id] = User(delta_ghoultokens or 0, delta_skelecoin or 0)
        
        await self.write_state()
    
    async def get_user(self, user_id):
        logger.info(f"get user {user_id}")
        if user_id in self.state:
            return self.state[user_id]
        else:
            return User(0, 0)

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Checks for the spooky stuff in a message
        """
        if message is not None and message is not None:
            content = message.content
            # increment once per phrase, not each time in a message
            increment = 0
            if self.bonus_phrase in content:
                increment += 5

            for x in self.target_phrases:
                if x in content:
                    increment += 1
            
            user_id = message.author.id
            # would all these writes cause slowdown, idk, idc
            await self.update_user(user_id, increment, None)
    
    # cheat commands
    @commands.command("cheat_ghoultokens")
    @commands.guild_only()
    async def cheat_ghoultokens(self, ctx, user: discord.User, delta_ghoultokens: int):
        """
        Cheat c0deZ to update the ghoultokens for a user
        """
        if ctx.author.id in lazy_admins:
            self.update_user(user.id, delta_ghoultokens=delta_ghoultokens)
    
    @commands.command("cheat_skelecoin")
    @commands.guild_only()
    async def cheat_skelecoin(self, ctx, user: discord.User, skelecoin: int):
        """
        Cheat c0deZ to update the skelecoin for a user
        """
        if ctx.author.id in lazy_admins:
            self.update_user(user.id, delta_skelecoin=skelecoin)

    @commands.command("spookyboard")
    @commands.guild_only()
    async def spookyboard(self, ctx):
        # ordered by ghoultokens
        values = list(enumerate(self.state.items()))
        # values are [ (index, (user_id, User))]
        # user id is x[1][0]
        # user class is x[1][1].ghoultokens
        spooky_ppl = sorted(values, key=lambda x: x[1][1].ghoultokens, reverse=True)[:10]

        leaderboard_embed = discord.Embed()
        leaderboard_embed.title = "Spookyboard"
        leaderboard_embed.color = discord.Color.orange()

        message = ""

        for person in spooky_ppl:
            person_id = person[1][0]
            person_ghoultokens = person[1][1].ghoultokens
            display_name = ctx.message.server.get_member(person_id).display_name

            # escape name
            zero_width_space = '​'
            display_name.replace('@', '@' + zero_width_space)

            # TODO different emoji if I feel like it
            message += f"**{person_ghoultokens}** - {display_name}\n"
        
        leaderboard_embed.description = message
        await ctx.send("", embed=leaderboard_embed)

    @commands.command("balance")
    @commands.guild_only()
    async def balance(self, ctx):
        author_id = ctx.author.id
        user = await self.get_user(author_id)

        if user.ghoultokens == 0 and user.skelecoin == 0:
            await ctx.send("you have nothing. truly, this is the spookiest fate.")
        else:
            msg = "Current balance:\n"
            if user.ghoultokens != 0:
                msg += f"{user.ghoultokens} GHOUL TOKENS\n"
            if user.skelecoin != 0:
                msg += f"{user.skelecoin} SKELE-COIN\n"
            
            if abs(user.ghoultokens) in [69, 420, 1337] or abs(user.skelecoin) in [69, 420, 1337]:
                msg += "nice."
            
            await ctx.send(msg)

    @commands.command("doot")
    @commands.guild_only()
    async def doot(self, ctx):
        author_id = ctx.author.id
        user = await self.get_user(author_id)
        if user.ghoultokens > 5:
            await self.update_user(author_id, delta_ghoultokens=-5)

            await ctx.message.add_reaction("💀")
            await ctx.message.add_reaction("🎺")

            await ctx.send("doot https://www.youtube.com/watch?v=eVrYbKBrI7o")
        else:
            await ctx.send(f"Insufficient funds. You have `{user.ghoultokens}` ghoul tokens.")
    
    @commands.command("send_ghoultokens")
    async def send_ghoultokens(self, ctx, recipient: discord.User, amount: int):
        """
        Send someone some ghoul tokens
        """
        if amount < 0:
            await ctx.send("heh, that would be pretty funny")
        elif amount == 0:
            await ctx.send("that's just mean")

            # let this go negative, i do not care
            await self.update_user(ctx.author.id, delta_ghoultokens=-1)
        elif ctx.author.id == recipient.id:
            await ctx.send("no.")
        else:
            author_id = ctx.author.id
            user = await self.get_user(author_id)
            if user.ghoultokens >= amount:
                await self.update_user(author_id, delta_ghoultokens=-amount)

                # fun :)
                if random.randint(0, 10000) == 123:
                    amount *= 100

                # sharing is very scary, so reward this behavior
                await self.update_user(recipient, delta_ghoultokens=(amount + 1))
                await ctx.sent(f"TRANSFER COMPLETE. HAVE A SPOOKY DAY.")

def setup(bot):
    bot.add_cog(SpookyMonth(bot))