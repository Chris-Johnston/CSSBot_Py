import math
import json
from discord.ext import commands
import discord
import configparser
import random
import asyncio
import logging
import time
import datetime
import uuid
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# hardcoding files because I am lazy and I do not care
spooky_phrases_file = "spooky_phrases.txt"
spooky_state_file = "spooky_state.json"
spooky_nicknames = "spooky_names.txt"
lazy_admins = [163184946742034432, 234840886519791616]

# harcoded because lazy
spooky_roleid = 1158864060650106990

from dataclasses import dataclass
# this did not work well for this case, would not recommend
# from dataclasses_json import dataclass_json
from dataclass_wizard import JSONWizard

@dataclass
class User(JSONWizard):
    ghoultokens: int
    skelecoin: int

@dataclass
class State(JSONWizard):
    last_updated: int # timestamp
    # keyed by userid, value is User
    users: dict

    # def to_json_actual(self):
    #     return json.dumps({
    #         "last_updated": self.last_updated,
    #         # "users": self.users
    #         # why does python serialization suck so much
    #         "users": User.schema().dump(self.users, many=True)
    #     })
    
# def from_json_actual(jsonstr):
#     j = json.loads(jsonstr)
#     s = State(0, {})
#     s.last_updated = j['last_updated']
#     s.users = User.schema().load(j['users'], many=True)
#     return s

def is_user_spooky(user):
    for role in user.roles:
        if role.id == spooky_roleid:
            return True
    return False

def escape(text):
    zero_width_space = '​'
    text.replace('@', '@' + zero_width_space)
    return text

def get_sendoff():
    adjectives = [
        # lazy weight
        "SCARY",
        "SCARY",
        "SCARY",
        "SCARY",
        "SCARY",
        "SCARY",
        "CREEPY",
        "FRIGHTENING",
        "PUMPKIN",
        "DAY",
        "",
        "OCTOBER",
        "GHOULISH",
        "SKELETAL",
        "GHOST-LIKE",
        "ZOMBIE-TASTIC",
        "SPOOKY",
        "BONE-CHILLING",
        "TRANSACTIONAL",
        "${ADJECTIVE}"
    ]
    return f"Have a {random.choice(adjectives)} day!"

def get_emoji_by_tokens(value: int):
    if value < 10:
        return ""
    if value < 100:
        return "💀"
    if value < 500:
        return "☠️"
    if value < 1000:
        return "🎃"
    if value < 2000:
        return "🕷️"
    if value < 5000:
        return "⚰️"
    if value < 10000:
        return "🐈‍⬛"
    if value < 1_000_000_000:
        return "💰"
    return ""


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

        # for cheaters trying to read the source, the stonk
        # algorithm is y = 1 + 0.15x + 0.5 * sin(A * x) + 0.8 sin(B * x) + 0.1 * sin(C * x) + 2 sin( x / D) + 2 cos (x / E)
        self.stonk_weight_a = random.randint(1, 10)
        self.stonk_weight_b = random.randint(1, 10)
        self.stonk_weight_c = random.randint(1, 10)
        self.stonk_weight_d = random.randint(1, 10)
        self.stonk_weight_e = random.randint(1, 10)
        self.stonk_weight_f = -random.randint(10, 20) / 100.0

        logger.info("reading names from file")
        with open(spooky_nicknames, 'rt') as n:
            self.nickname_fmt_strings = n.read().splitlines()

        logger.info("spooky module is up")
        
    
    def get_stonk_value(self):
        # the returned value is the conversion rate between the types of coins
        # or 1 ghoul token = value skele coins
        now = datetime.datetime.now()
        t = 0.0001 - now.day * 0.2 + now.hour + now.minute / 60.0
        value = 5.0 + self.stonk_weight_f * t + 0.5 * math.sin(self.stonk_weight_a * t) + 0.8 * math.sin(self.stonk_weight_b * t) + 0.1 * math.sin(self.stonk_weight_c * t) + 2 * math.sin(t / self.stonk_weight_d) + 2 * math.cos(t / self.stonk_weight_e)
        if value < -0.5:
            return value
        return max(0.001, value)
    
    # who needs a database, json is MY database
    async def read_state(self):
        logger.info("reading state from file")
        try:
            async with self.state_mutex:
                with open(spooky_state_file, 'rt') as s:
                    # self.state = from_json_actual(s.read())
                    self.state = State.from_json(s.read())

                    # hack to fix shortcomings in serialization
                    # why did I even bother with dataclasses
                    actual_state = {}
                    for k, v in self.state.users.items():
                        user_id = int(k)
                        actual_state[user_id] = User(v['ghoultokens'], v['skelecoin'])
                    self.state.users = actual_state
                    logger.info(f'state is: {self.state}')
            logger.info("done reading state file")
        except Exception as e:
            logger.error(e)
            logger.warn(f"could not read state file, initializing empty one {e}")
            self.state = State(time.time(), {})
            await self.write_state()

    async def write_state(self):
        logger.info("updating state")
        try:
            async with self.state_mutex:
                with open(spooky_state_file, 'wt') as s:
                    # json_text = self.state.to_json_actual()
                    json_text = self.state.to_json()
                    s.write(json_text)
        except Exception as e:
            logger.warn("failed to write state for some reason idk", e)
    
    # the good stuff
    async def update_user(self, user_id, delta_ghoultokens=None, delta_skelecoin=None):
        logger.info(f"update user_id {user_id} ghoul {delta_ghoultokens} skele {delta_skelecoin}")
        if user_id in self.state.users:
            # update existing
            if delta_ghoultokens is not None:
                self.state.users[user_id].ghoultokens += delta_ghoultokens
            if delta_skelecoin is not None:
                self.state.users[user_id].skelecoin += delta_skelecoin
        else:
            # new user
            logger.info(f"new user user_id {user_id}")
            self.state.users[user_id] = User(delta_ghoultokens or 0, delta_skelecoin or 0)
        
        await self.write_state()
    
    async def get_user(self, user_id):
        logger.info(f"get user {user_id}")
        if user_id in self.state.users:
            return self.state.users[user_id]
        else:
            return User(0, 0)

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Checks for the spooky stuff in a message
        """
        if message.guild is None:
            return

        if message is not None and message is not None:
            content = message.content.lower()
            # increment once per phrase, not each time in a message
            increment = 0
            if self.bonus_phrase in content:
                increment += 5

            for x in self.target_phrases:
                if x in content:
                    increment += 1

            has_role = is_user_spooky(message.author)
            # double points
            if has_role:
                increment = increment * 2

            user_id = message.author.id
            # would all these writes cause slowdown, idk, idc
            await self.update_user(user_id, increment, None)
    
    # cheat commands
    @commands.command("cheat_ghoultokens", hidden=True)
    @commands.guild_only()
    async def cheat_ghoultokens(self, ctx, user: discord.User, delta_ghoultokens: int):
        """
        Cheat c0deZ to update the ghoultokens for a user
        """
        if ctx.author.id in lazy_admins:
            await self.update_user(user.id, delta_ghoultokens=delta_ghoultokens)
    
    @commands.command("cheat_skelecoin", hidden=True)
    @commands.guild_only()
    async def cheat_skelecoin(self, ctx, user: discord.User, skelecoin: int):
        """
        Cheat c0deZ to update the skelecoin for a user
        """
        if ctx.author.id in lazy_admins:
            await self.update_user(user.id, delta_skelecoin=skelecoin)

    @commands.command("spookyboard")
    @commands.guild_only()
    async def spookyboard(self, ctx):
        # ordered by ghoultokens
        # values are [ (index, (user_id, User))]
        # user id is x[1][0]
        # user class is x[1][1].ghoultokens
        spooky_ppl = sorted(self.state.users.items(), key=lambda x: x[1].ghoultokens, reverse=True)[:10]

        leaderboard_embed = discord.Embed()
        leaderboard_embed.title = "Spookyboard"
        if random.randint(0, 100) == 1:
            leaderboard_embed.title = "S̸̡̡̛̟̝̮͙̈́̈́̌̏̍̈́́͝C̷̨̢̝̝̼̮̦̗̺̻̦̥͈͎̪̃͊́̇̚ͅÃ̴̡̳̠̥̯͎̭̱̼̣̉̎́̋̀ͅŘ̴̢̢̜͍̩͔̗͉̖̼͍̥͚̋̽͑̔̑̈́̐̋Ỷ̸͕̬͔̪͎̬̊̉̈́̈́̈́͛̋́̉̈́̓͝͠ͅB̵̢̟̩̳̰̦̙͔̭͍̫̝͓̹͒O̶͉̣̤̯̾̊̽͛̌̿̄͗̐̃̌̄̕Ȃ̴̢̰̬͔͉͙̲̹͙̱͈̆̍̕Ŗ̷̧̥̠͖̜̰̤͕̥͇̦̗̗͚͎̔͛͋͗̄̌̄̋̓̊̈́̒͆̊̚͘͜D̶̡̳͍͐̈́̊̑̕͘̚"
        leaderboard_embed.color = discord.Color.orange()

        message = ""

        for person_id, person_user in spooky_ppl:
            person_ghoultokens = person_user.ghoultokens
            # display_name = ctx.guild.get_member(person_id).display_name
            # no mentions in embed body?
            display_name = f"<@{person_id}>"

            # escape name
            # zero_width_space = '​'
            # display_name.replace('@', '@' + zero_width_space)

            # TODO different emoji if I feel like it
            emoji = get_emoji_by_tokens(person_ghoultokens)
            message += f"{emoji} **{person_ghoultokens}** - {display_name}\n"
        
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
        """
        Doot. (5 ghoul tokens)
        """
        author_id = ctx.author.id
        user = await self.get_user(author_id)
        if user.ghoultokens > 5:
            await self.update_user(author_id, delta_ghoultokens=-5)

            await ctx.message.add_reaction("💀")
            await ctx.message.add_reaction("🎺")

            await ctx.send("doot https://www.youtube.com/watch?v=eVrYbKBrI7o")
        else:
            await ctx.send(f"Insufficient funds. You have `{user.ghoultokens}` ghoul tokens. {get_sendoff()}")
    
    @commands.command(name="send_ghoultokens", aliases=["send_gt", "send_ghoultoken"])
    @commands.guild_only()
    async def send_ghoultokens(self, ctx, recipient: discord.User, amount: int):
        """
        Send someone some ghoul tokens
        """
        if amount < 0:
            await ctx.send("heh, that would be pretty funny")
        elif amount == 0:
            await ctx.send("that's just mean")

            # let this go negative, i do not care
            await self.update_user(ctx.author.id, delta_ghoultokens=-1, delta_skelecoin=None)
        elif ctx.author.id == recipient.id:
            await ctx.send("no.")
        else:
            author_id = ctx.author.id
            user = await self.get_user(author_id)
            if user.ghoultokens >= amount:
                await self.update_user(author_id, delta_ghoultokens=-amount, delta_skelecoin=None)

                # fun :)
                if random.randint(0, 10000) == 123:
                    amount *= 100

                # sharing is very scary, so reward this behavior
                await self.update_user(recipient.id, delta_ghoultokens=(amount + 1), delta_skelecoin=None)
                await ctx.send(f"TRANSFER COMPLETE. {get_sendoff()}")

    @commands.command(name="send_skelecoin", aliases=["send_sc", "send_skelecoins"])
    @commands.guild_only()
    async def send_skelecoins(self, ctx, recipient: discord.User, amount: int):
        """
        Send someone some skele coin
        """
        if amount < 0:
            await ctx.send("If you send me 5,000,001 skele coin I will let you do this. Once. I am serious.")
        elif amount == 0:
            await ctx.send(":)")
            await self.update_user(ctx.author.id, delta_skelecoin=-1)
        elif ctx.author.id == recipient.id:
            await ctx.send("no.")
        else:
            author_id = ctx.author.id
            user = await self.get_user(author_id)
            if user.ghoultokens >= amount:
                await self.update_user(author_id, delta_skelecoin=-amount)

                # fun :)
                if random.randint(0, 10000) == 123:
                    amount *= 100000

                # sharing is very scary, so reward this behavior
                await self.update_user(recipient.id, delta_skelecoin=(amount))
                await ctx.send(f"TRANSFER COMPLETE. {get_sendoff()}")

    @commands.command("stonks")
    @commands.guild_only()
    async def stonks(self, ctx):
        """
        View the conversion rate between Ghoul Tokens and Skele Coin.
        """
        if random.randint(0, 1000) == 10:
            await ctx.send("# BOO!")
            return

        conversion_rate = self.get_stonk_value()
        msg = f"The current market conversion rate is:\n1 GHOUL TOKEN = {conversion_rate} SKELE COIN(S)\n1 SKELE COIN = {1 / conversion_rate} GHOUL TOKEN(S)"
        await ctx.send(msg)

    @commands.command("stonks", hidden=True)
    @commands.guild_only()
    async def stonkcharts(self, ctx):
        """
        (COSTS 50 SKELE COIN) View Ghoul Token / Skele-Coin conversion rate as a graph.
        """

        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if user.skelecoin < 50:
            await ctx.send("You do not have enough SKELE COIN.")
            return
        
        await self.update_user(user_id, delta_skelecoin=-50)

        f = discord.File(open('spookychart.png', 'rb'))

        await ctx.send("hey so this code was really annoying to write and it's still not good so I'm charging you 50 SKELE COIN. No refunds.", file=f)

    def get_value(self, time: datetime.datetime):
        # the returned value is the conversion rate between the types of coins
        # or 1 ghoul token = value skele coins
        now = time
        t = 0.0001 - now.day * 0.2 + now.hour + now.minute / 60.0
        value = 5.0 + self.stonk_weight_f * t + 0.5 * math.sin(self.stonk_weight_a * t) + 0.8 * math.sin(self.stonk_weight_b * t) + 0.1 * math.sin(self.stonk_weight_c * t) + 2 * math.sin(t / self.stonk_weight_d) + 2 * math.cos(t / self.stonk_weight_e)
        if value < -0.5:
            return value
        return max(0.001, value)
    
    def make_data(self):
        deltatime = datetime.timedelta(hours=24)
        increment = datetime.timedelta(minutes=5)
        now = datetime.datetime.now()
        start_time = now - deltatime

        # data = []
        data_x = []
        data_y = []

        current_time = start_time
        current = 0

        for iter in range(int(deltatime / increment)):
            current_time += increment
            x = current_time
            y = self.get_value(x)
            # print(x, y)
            # data.append((x, y))
            data_x.append(x)
            data_y.append(y)
            current = y
        # current is the last known value
        return (data_x, data_y, start_time, now, current)


    def generate_image(self):
        import numpy as np
        import random
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        sayings = [
            "1 $GHOUL = Y $SKELE"
            "WE LIKE THE STONK",
            "SPOOOOOOOOOOOOOOKY",
            "SPOOKYHANDS",
            "BUY SPOOKY, SELL EVEN SPOOKIER"
            "DOOT DOOT"
        ]

        data_x, data_y, start_time, end_time, current = self.make_data()

        plt.title(f"1 $GHOUL = {current:.3f} $SKELE")
        plt.ylabel(random.choice(sayings))
        plt.xlabel("Previous 24 hours")
        # plt.legend()
        plt.grid(True)
        # plt.plot(data_np, label="MONEEEYYYY")
        plt.plot(data_x, data_y, "g", label="MONNNEEYYYY")
        plt.xlim(left=start_time)
        # plt.xaxis.
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%l:%M %P'))
        plt.xticks(rotation=10,ha='right')
        plt.ylim(bottom=0)
        # plt.show()
        plt.savefig("spookystonks.png", dpi=240)


    @commands.command("trade_gt")
    @commands.guild_only()
    async def trade_gt(self, ctx, amount: int):
        """
        Sell an amount of Ghoul Tokens to buy Skele Coin at the current rate.
        """
        if amount < -2:
            return

        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if amount > user.ghoultokens:
            await ctx.send("You do not have enough GHOUL TOKENS.")
        else:
            skelecoin = math.floor(amount * self.get_stonk_value())
            await self.update_user(user_id, delta_ghoultokens=-amount, delta_skelecoin=skelecoin)
            await ctx.send(f"You sold {amount} GHOUL TOKEN for {skelecoin} SKELE COIN. Have a SPOOKY day.")

    @commands.command("trade_sc")
    @commands.guild_only()
    async def trade_sc(self, ctx, amount: int):
        """
        Sell an amount of Skele Coin to buy Ghoul Token at the current rate.
        """
        if amount < -2:
            return

        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if amount > user.skelecoin:
            await ctx.send("You do not have enough SKELE COIN.")
        else:
            ghoultoken = math.floor(amount * (1 / self.get_stonk_value()))
            await self.update_user(user_id, delta_ghoultokens=ghoultoken, delta_skelecoin=-amount)
            await ctx.send(f"You sold {amount} SKELE COIN for {ghoultoken} GHOUL TOKEN. {get_sendoff()}")

    @commands.command("secret", hidden=True)
    @commands.guild_only()
    async def secret(self, ctx):
        """
        Sell 30 Skele Coin to reveal the secret word.
        """
        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if 30 > user.skelecoin:
            await ctx.send("You do not have enough SKELE COIN.")
        else:
            await self.update_user(user_id, delta_ghoultokens=None, delta_skelecoin=-30)
            await ctx.send(f"The secret word is `{self.bonus_phrase}`. {get_sendoff()}")

    @commands.command("buy_art", hidden=True)
    @commands.guild_only()
    async def buy_art(self, ctx):
        """
        Exchange 5,000 Ghoul Tokens for one-of-a-kind art.
        """
        user_id = ctx.author.id
        user = await self.get_user(user_id)

        amount = 5000
        if amount > user.ghoultokens:
            await ctx.send(f"You do not have enough GHOUL TOKEN. Come back when you have more. {get_sendoff()}")
        else:
            await ctx.send(f"Wow. I can truly see that you appreciate only the finest of art. I am generating your new one-of-a-kind piece now. {get_sendoff()}")
            await self.update_user(user_id, delta_ghoultokens=-5000, delta_skelecoin=None)

            nft = str(uuid.uuid4())
            await ctx.send(f"<@{user_id}>, here is your exclusive and one-of-a-kind art:\n`{nft}`\nYou are now the sole owner of this string of characters forever. Good job. {get_sendoff()}")

    @commands.command("millionaire")
    @commands.guild_only()
    async def millionaire(self, ctx):
        user_id = ctx.author.id
        user = await self.get_user(user_id)
        if user.ghoultokens > 1_000_000:
            await ctx.send("Wow good job ur a millionaire. Have some FREE +50 SKELE COIN")
            await self.update_user(user_id, delta_ghoultokens=None, delta_skelecoin=50)

    @commands.command("billionaire")
    @commands.guild_only()
    async def billionaire(self, ctx):
        user_id = ctx.author.id
        user = await self.get_user(user_id)
        if user.skelecoin > 1_000_000_000:
            await ctx.send("cool, now start over.")
            await self.update_user(user_id, delta_ghoultokens=-user.ghoultokens, delta_skelecoin=-user.skelecoin)
        else:
            await ctx.send("😤😤😤 The 👀 grind 🎯💰 never 😎 stops 💪 😤😤. Keep up the grind!")

    @commands.command("spook")
    @commands.guild_only()
    async def spook_user(self, ctx, target_user: discord.User):
        """
        Scare a user! Ahh! (Costs a random number of SKELE COIN)
        """
        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if user_id == target_user.id:
            await ctx.send("You can't spook yourself")
            return

        if user.skelecoin > 0:
            cost = random.randint(0, 200)
            await ctx.send(f"SpooOOOooOOooky... You have been charged {cost} SKELE COIN\n<@{target_user.id}> has been spooked by <@{user_id}>!")
            await self.update_user(user_id, delta_ghoultokens=None, delta_skelecoin=-cost)

            # if they already have the role too bad should have noticed
            spooky_role = ctx.guild.get_role(spooky_roleid)
            await target_user.add_roles(spooky_role)
        else:
            await ctx.send(f"Come back again when you have some SKELE COIN. {get_sendoff()}")

    @commands.command("market_manipulation", hidden=True)
    @commands.guild_only()
    async def market_manipulation(self, ctx):
        """
        Manipulates the market. (Costs 50000 SKELE COIN, Spooky users only)
        """
        user_id = ctx.author.id
        is_spooky = is_user_spooky(ctx.author)

        if not(is_spooky):
            await ctx.send(f"Nah, not spooky enough 4 me")
            return
        
        user = await self.get_user(user_id)
        
        if user.skelecoin >= 50000:
            await self.update_user(user_id, delta_skelecoin=-50000)

            self.stonk_weight_a = random.randint(1, 10)
            self.stonk_weight_b = random.randint(1, 10)
            self.stonk_weight_c = random.randint(1, 10)
            self.stonk_weight_d = random.randint(1, 10)
            self.stonk_weight_e = random.randint(1, 10)
            self.stonk_weight_f = -random.randint(10, 20) / 100.0

            await ctx.send("The market variables have been randomized for now. This may or may not have done anything. Good job?")
        else:
            await ctx.send("You don't have enough SKELE COIN for this.")
    
    @commands.command("this_does_nothing", hidden=True)
    @commands.guild_only()
    async def this_does_nothing(self, ctx):
        """
        This command does nothing, but can only be used by spooky people.
        """
        is_spooky = is_user_spooky(ctx.author)
        if not is_spooky:
            await self.update_user(ctx.author.id, delta_skelecoin=-1)
            await ctx.send(f"This command only does nothing if you are spooky. Since you aren't spooky, I'm subtracting a single SKELE COIN. {get_sendoff()}")

    @commands.command(name="trade_gc", aliases=["trade_st"])
    @commands.guild_only()
    async def you_fool(self, ctx):
        await self.update_user(ctx.author.id, delta_skelecoin=-1)
        await ctx.send(f"You fool, it's GHOUL TOKEN and SKELE COIN, not SKELE TOKEN and GHOUL COIN. I have subtracted 1 SKELE COIN from your account. {get_sendoff()}")

    @commands.command(name="helphelphelphelphelphelphelphelphelphelphelp")
    @commands.guild_only()
    async def helphelphelphelphelphelphelphelphelphelphelp(self, ctx):
        is_spooky = is_user_spooky(ctx.author)
        if is_spooky:
            await ctx.send("N̶̛͚̹̣͔̾̂̒̋̋̈́̇́̓̓͜͠͝ͅǪ̴̛̭̬͙̫̀̓̄̃̉̓́̿̏̐̋̅̌̑B̵̲̈̉͛̕͝O̵͙̰̮̼͍̫͑̄̄̀D̸̢͈̤̜̺͎͕̤̭̰̻͗̏̽̓͗͂͐̋̀̓͆̚͝ͅỲ̶͉̾̿͋́́̽͘ ̷̛̛͎̝̂̿̓̉̾́̆́̇C̸͚͕͕͑Ą̵̧̛̳̮͈̯̹̙͌̈́̈́̇͒̎̀͂͜N̷̨̨͔͍̖̯͍̫͖̦̝̽̾̐ ̸̨̢̛͍̲̟̠̬̮̞͕̭͐́̈́͒͆̈́̏͛͘H̵̛̬͓̲͙̾̍̏̿̎̆͋̽̕͘͜͠͝É̵̗̖̫̆̆̃̎̅̾͑̓̈́͊̅̀̕ͅL̴̝͈̾̿̔͒̔̅̆̈͊͐P̷̡̡̬͎̠̻͙̦̗̗̞͗́̽̓̉̃͑̀͒̈́͗ͅ ̷̢̯̝̞͉̹̬̎̐Ý̴̡̡̹̬̯̹̣̗̪̳̪̾̈͜Ọ̴̣͕͚̰͚̀̀͊̿̓͆̅̆̾͛͆͘͠U̸͖̽̊ ̸̛̞͍̺͕̱̯̜̠̺͓͆͛̔͋͋̓͋̿͆͛̉̍͜͠ͅN̸͙̜̆̓Ơ̸̬͕̮̹̝͕̤̻̯̩̣̜̏̿͗̀̔̀͜͝ͅW̷̖̱̻̻̮̬̤͈̰̜̌̓̅͘ͅ" + " " + get_sendoff())
        else:
            await ctx.send("Oops! Looks like you made a typo. You meant `>>help`.")

    @commands.command("nickname")
    @commands.guild_only()
    async def nickname(self, ctx):
        """
        Transmogrifies your nickname into something SCARY. (Spooky users only.)
        """
        user_id = ctx.author.id
        is_spooky = is_user_spooky(ctx.author)
        if not is_spooky:
            await ctx.send(f"Spooky users only. Come back when you are SPOOKY. {get_sendoff()}")
            return

        user = await self.get_user(user_id)
        if user.skelecoin > 1000:
            await ctx.send(f"You actually have too much SKELE COIN to use this command. Come back when you have less SKELE COIN. {get_sendoff()}")
            return
        
        if user.ghoultokens % 3 == 0:
            await ctx.send(f"This command only works if your number of GHOUL TOKEN is not a multiple of THREE. {get_sendoff()}")
            return
        
        if abs(user.skelecoin) >= 100:
            await self.update_user(user_id, delta_skelecoin=-10)

            current_nickname = ctx.author.display_name
            fmt_str = random.choice(self.nickname_fmt_strings)
            new_nickname = fmt_str.format(current_nickname)
            new_nickname = escape(new_nickname)
            await ctx.author.edit(nick=new_nickname)
            await ctx.send(f"Prest-o! Change-o! Here's your new nickname. In case it got truncated it was: `{new_nickname}` {get_sendoff()}")
        else:
            await ctx.send(f"So here's the thing. This command only costs 10 SKELE COIN, but you do need an absolute balance greater than 100 SKELE COIN to use it. {get_sendoff()}")


def setup(bot):
    bot.add_cog(SpookyMonth(bot))