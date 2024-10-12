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

primes_txt = "2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199,211,223,227,229,233,239,241,251,257,263,269,271,277,281,283,293,307,311,313,317,331,337,347,349,353,359,367,373,379,383,389,397,401,409,419,421,431,433,439,443,449,457,461,463,467,479,487,491,499,503,509,521,523,541,547,557,563,569,571,577,587,593,599,601,607,613,617,619,631,641,643,647,653,659,661,673,677,683,691,701,709,719,727,733,739,743,751,757,761,769,773,787,797,809,811,821,823,827,829,839,853,857,859,863,877,881,883,887,907,911,919,929,937,941,947,953,967,971,977,983,991,997,1009,1013,1019,1021,1031,1033,1039,1049,1051,1061,1063,1069,1087,1091,1093,1097,1103,1109,1117,1123,1129,1151,1153,1163,1171,1181,1187,1193,1201,1213,1217,1223,1229,1231,1237,1249,1259,1277,1279,1283,1289,1291,1297,1301,1303,1307,1319,1321,1327,1361,1367,1373,1381,1399,1409,1423,1427,1429,1433,1439,1447,1451,1453,1459,1471,1481,1483,1487,1489,1493,1499,1511,1523,1531,1543,1549,1553,1559,1567,1571,1579,1583,1597,1601,1607,1609,1613,1619,1621,1627,1637,1657,1663,1667,1669,1693,1697,1699,1709,1721,1723,1733,1741,1747,1753,1759,1777,1783,1787,1789,1801,1811,1823,1831,1847,1861,1867,1871,1873,1877,1879,1889,1901,1907,1913,1931,1933,1949,1951,1973,1979,1987,1993,1997,1999,2003,2011,2017,2027,2029,2039,2053,2063,2069,2081,2083,2087,2089,2099,2111,2113,2129,2131,2137,2141,2143,2153,2161,2179,2203,2207,2213,2221,2237,2239,2243,2251,2267,2269,2273,2281,2287,2293,2297,2309,2311,2333,2339,2341,2347,2351,2357,2371,2377,2381,2383,2389,2393,2399,2411,2417,2423,2437,2441,2447,2459,2467,2473,2477,2503,2521,2531,2539,2543,2549,2551,2557,2579,2591,2593,2609,2617,2621,2633,2647,2657,2659,2663,2671,2677,2683,2687,2689,2693,2699,2707,2711,2713,2719,2729,2731,2741,2749,2753,2767,2777,2789,2791,2797,2801,2803,2819,2833,2837,2843,2851,2857,2861,2879,2887,2897,2903,2909,2917,2927,2939,2953,2957,2963,2969,2971,2999,3001,3011,3019,3023,3037,3041,3049,3061,3067,3079,3083,3089,3109,3119,3121,3137,3163,3167,3169,3181,3187,3191,3203,3209,3217,3221,3229,3251,3253,3257,3259,3271,3299,3301,3307,3313,3319,3323,3329,3331,3343,3347,3359,3361,3371,3373,3389,3391,3407,3413,3433,3449,3457,3461,3463,3467,3469,3491,3499,3511,3517,3527,3529,3533,3539,3541,3547,3557,3559,3571,3581,3583,3593,3607,3613,3617,3623,3631,3637,3643,3659,3671,3673,3677,3691,3697,3701,3709,3719,3727,3733,3739,3761,3767,3769,3779,3793,3797,3803,3821,3823,3833,3847,3851,3853,3863,3877,3881,3889,3907,3911,3917,3919,3923,3929,3931,3943,3947,3967,3989,4001,4003,4007,4013,4019,4021,4027,4049,4051,4057,4073,4079,4091,4093,4099,4111,4127,4129,4133,4139,4153,4157,4159,4177,4201,4211,4217,4219,4229,4231,4241,4243,4253,4259,4261,4271,4273,4283,4289,4297,4327,4337,4339,4349,4357,4363,4373,4391,4397,4409,4421,4423,4441,4447,4451,4457,4463,4481,4483,4493,4507,4513,4517,4519,4523,4547,4549,4561,4567,4583,4591,4597,4603,4621,4637,4639,4643,4649,4651,4657,4663,4673,4679,4691,4703,4721,4723,4729,4733,4751,4759,4783,4787,4789,4793,4799,4801,4813,4817,4831,4861,4871,4877,4889,4903,4909,4919,4931,4933,4937,4943,4951,4957,4967,4969,4973,4987,4993,4999,5003,5009,5011,5021,5023,5039,5051,5059,5077,5081,5087,5099,5101,5107,5113,5119,5147,5153,5167,5171,5179,5189,5197,5209,5227,5231,5233,5237,5261,5273,5279,5281,5297,5303,5309,5323,5333,5347,5351,5381,5387,5393,5399,5407,5413,5417,5419,5431,5437,5441,5443,5449,5471,5477,5479,5483,5501,5503,5507,5519,5521,5527,5531,5557,5563,5569,5573,5581,5591,5623,5639,5641,5647,5651,5653,5657,5659,5669,5683,5689,5693,5701,5711,5717,5737,5741,5743,5749,5779,5783,5791,5801,5807,5813,5821,5827,5839,5843,5849,5851,5857,5861,5867,5869,5879,5881,5897,5903,5923,5927,5939,5953,5981,5987,6007,6011,6029,6037,6043,6047,6053,6067,6073,6079,6089,6091,6101,6113,6121,6131,6133,6143,6151,6163,6173,6197,6199,6203,6211,6217,6221,6229,6247,6257,6263,6269,6271,6277,6287,6299,6301,6311,6317,6323,6329,6337,6343,6353,6359,6361,6367,6373,6379,6389,6397,6421,6427,6449,6451,6469,6473,6481,6491,6521,6529,6547,6551,6553,6563,6569,6571,6577,6581,6599,6607,6619,6637,6653,6659,6661,6673,6679,6689,6691,6701,6703,6709,6719,6733,6737,6761,6763,6779,6781,6791,6793,6803,6823,6827,6829,6833,6841,6857,6863,6869,6871,6883,6899,6907,6911,6917,6947,6949,6959,6961,6967,6971,6977,6983,6991,6997,7001,7013,7019,7027,7039,7043,7057,7069,7079,7103,7109,7121,7127,7129,7151,7159,7177,7187,7193,7207,7211,7213,7219,7229,7237,7243,7247,7253,7283,7297,7307,7309,7321,7331,7333,7349,7351,7369,7393,7411,7417,7433,7451,7457,7459,7477,7481,7487,7489,7499,7507,7517,7523,7529,7537,7541,7547,7549,7559,7561,7573,7577,7583,7589,7591,7603,7607,7621,7639,7643,7649,7669,7673,7681,7687,7691,7699,7703,7717,7723,7727,7741,7753,7757,7759,7789,7793,7817,7823,7829,7841,7853,7867,7873,7877,7879,7883,7901,7907,7919".split(',')
primes = [int(x) for x in primes_txt]

def is_market_closed():
    n = datetime.datetime.now()
    current_minute = n.hour * 60 + n.minute
    if current_minute in primes:
        return True
    return False

def get_market_closed_message():
    n = datetime.datetime.now()
    current_minute = n.hour * 60 + n.minute

    try:
        prime_index = primes.index(current_minute)
        n = prime_index + 1
        msg = f"Sorry, but the markets are closed when the current time in total minutes is a prime number. The current time in minutes is {current_minute} (out of 1440), which is the {n}(nt/st/nd/rd) prime. The server is using eastern time, for reasons. Try again on the next minute that isn't a prime. "
        msg += get_sendoff()
        return msg
    except ValueError as e:
        msg = f"Wow. So normally the markets are closed when the current in total minutes is a prime number. But in the time between when I checked the time once and then checked again (lazy code), the current minute ({current_minute}) is no longer a prime number. Try again now. "
        msg += get_sendoff()
        return msg

scary_cash_total_supply = 5000

# features that can be purchased from the store
store = {
    # key is feature name, value is tuple of price, currency, and description text
    "primetrading": (12500, "skelecoin", "Enables trading during prime minutes."),

    "spookysaturday": (1000, "ghoultokens", "All GHOUL TOKENS earned on Saturdays are multiplied 5x. Does not apply to the STONK market."),

    "friendship": (999, "skelecoin", "Unlocks friendship."),

    "gambling2": (2500, "ghoultokens", "Unlocks GAMBLING 2."),

    "cheaper_stonkchart": (1337, "ghoultokens", "Reduces the cost of `>>stonkchart` to 5 SKELE COIN.")
}

@dataclass
class User(JSONWizard):
    #
    # THESE MUST BE ONE WORD WITHOUT ANY DELIMITERS BECAUSE JSONWIZARD IS TRYING TO BE CLEVER
    # AND TURNS FOO_BAR INTO fooBar
    #
    ghoultokens: int
    skelecoin: int
    # +1 for social behavior
    friendshippoints: int
    scarycash: int

@dataclass
class State(JSONWizard):
    last_updated: int # timestamp
    # keyed by userid, value is User
    users: dict
    # key by feature, value is user id who purchased its
    unlockedfeatures: dict

    # additions to this state should be made to the json first, otherwise will result in
    # serialization breaking everything

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
        "SCARIER",
        "SCARIEST",
        "SKELETON",
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
    
    def is_feature_unlocked(self, feature: str) -> bool:
        return feature in self.state.unlockedfeatures

    async def unlock_feature_async(self, feature: str, user_id) -> bool:
        self.state.unlockedfeatures[feature] = user_id

        await self.write_state()

    def get_stonk_value(self):
        # # the returned value is the conversion rate between the types of coins
        # # or 1 ghoul token = value skele coins
        # now = datetime.datetime.now()
        # t = 0.0001 - now.day * 0.2 + now.hour + now.minute / 60.0
        # value = 5.0 + self.stonk_weight_f * t + 0.5 * math.sin(self.stonk_weight_a * t) + 0.8 * math.sin(self.stonk_weight_b * t) + 0.1 * math.sin(self.stonk_weight_c * t) + 2 * math.sin(t / self.stonk_weight_d) + 2 * math.cos(t / self.stonk_weight_e)
        # if value < -0.5:
        #     return value
        # return max(0.39, value)
        return self.get_value(datetime.datetime.now())
    
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

                        friendship_points = v.get('friendshippoints', 0)
                        scary_cash = v.get('scarycash', 0)

                        actual_state[user_id] = User(v['ghoultokens'], v['skelecoin'], friendship_points, scary_cash)
                    self.state.users = actual_state
                    logger.info(f'state is: {self.state}')
            logger.info("done reading state file")
        except Exception as e:
            logger.error(e)
            logger.warn(f"could not read state file, initializing empty one {e}")
            # only should do this if the file doesn't exist, otherwise RIP everything
            #self.state = State(time.time(), {}, {})
            #await self.write_state()

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
    async def update_user(self, user_id, delta_ghoultokens=None, delta_skelecoin=None, delta_friendship_points=None, delta_scary_cash=None):
        logger.info(f"update user_id {user_id} ghoul {delta_ghoultokens} skele {delta_skelecoin} friendship {delta_friendship_points} scary cash {delta_scary_cash}")
        if user_id in self.state.users:
            # update existing
            if delta_ghoultokens is not None:
                self.state.users[user_id].ghoultokens += delta_ghoultokens
            if delta_skelecoin is not None:
                self.state.users[user_id].skelecoin += delta_skelecoin
            if delta_friendship_points is not None:
                self.state.users[user_id].friendshippoints += delta_friendship_points
            if delta_scary_cash is not None:
                self.state.users[user_id].scarycash += delta_scary_cash
        else:
            # new user
            logger.info(f"new user user_id {user_id}")
            self.state.users[user_id] = User(delta_ghoultokens or 0, delta_skelecoin or 0, delta_friendship_points or 0, delta_scary_cash or 0)
        
        await self.write_state()
    
    async def get_user(self, user_id):
        logger.info(f"get user {user_id}")
        if user_id in self.state.users:
            return self.state.users[user_id]
        else:
            return User(0, 0)

    def determine_remaining_scary_cash_supply(self):
        """
        There is a limited supply of scary cash in circulation. It can only be bought, traded, or gambled.
        """
        # probably should have done this better but whatever
        consumed_supply = 0
        for user_key in self.state.users:
            user = self.state.users[user_key]
            consumed_supply += user.scarycash

        # overconsumption
        if consumed_supply > scary_cash_total_supply:
            return 0

        return scary_cash_total_supply - consumed_supply

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
            
            if random.randint(0, 100) > 90:
                increment += 1

            has_role = is_user_spooky(message.author)
            # double points
            if has_role:
                increment = increment * 2

            if self.is_feature_unlocked("spookysaturday"):
                # spooky saturday
                if datetime.datetime.today().weekday() == 5:
                    increment = increment * 5

            user_id = message.author.id
            # would all these writes cause slowdown, idk, idc
            await self.update_user(user_id, increment, None)
    
    # cheat commands
    @commands.command("cheat_checkfeatures", hidden=True)
    @commands.guild_only()
    async def cheat_checkfeatures(self, ctx):
        """
        Check features unlocked
        """
        if ctx.author.id in lazy_admins:
            msg = ""
            for feature in self.get_shop_items():
                msg += f"{feature} - {self.is_feature_unlocked(feature)}\n"
            await ctx.send(msg)

    # @commands.command("cheat_checkmilestones", hidden=True)
    # @commands.guild_only()
    # async def cheat_checkfeatures(self, ctx):
    #     """
    #     Check milestones
    #     """
    #     if ctx.author.id in lazy_admins:
    #         msg = ""
    #         for feature in self.get_shop_items():
    #             msg += f"{feature} - {self.is_feature_unlocked(feature)}\n"
    #         await ctx.send(msg)

    @commands.command("cheat_ghoultokens", hidden=True)
    @commands.guild_only()
    async def cheat_ghoultokens(self, ctx, user: discord.User, delta_ghoultokens: int):
        """
        Cheat c0deZ to update the ghoultokens for a user
        """
        if ctx.author.id in lazy_admins:
            await self.update_user(user.id, delta_ghoultokens=delta_ghoultokens)

    @commands.command("cheat_friendship", hidden=True)
    @commands.guild_only()
    async def cheat_friendship(self, ctx, user: discord.User, delta_friendship: int):
        """
        Cheat c0deZ to update the friendship points for a user
        """
        if ctx.author.id in lazy_admins:
            await self.update_user(user.id, delta_friendship_points=delta_friendship)

    @commands.command("cheat_scary_cash", hidden=True)
    @commands.guild_only()
    async def cheat_scary_cash(self, ctx, user: discord.User, delta_scary_cash: int):
        """
        Cheat c0deZ to update the scary cash for a user
        """
        if ctx.author.id in lazy_admins:
            await self.update_user(user.id, delta_scary_cash=delta_scary_cash)
    
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
    @commands.cooldown(5, 60, commands.BucketType.guild)
    async def spookyboard(self, ctx):
        """
        View server rankings ordered by GHOUL TOKENS.
        """

        # if random.randint(0, 30) == 2:
        #     await self.friendlyboard(ctx)
        #     return

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
        leaderboard_embed.set_footer(text=f"The top users ordered by GHOUL TOKENS")

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

    @commands.command("friendlyboard", hidden=True)
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.guild)
    async def friendlyboard(self, ctx):
        """
        spookyboard but for friendship points
        """
        if not self.is_feature_unlocked("friendship"):
            return

        spooky_ppl = sorted(self.state.users.items(), key=lambda x: x[1].friendshippoints, reverse=True)[:10]

        leaderboard_embed = discord.Embed()
        leaderboard_embed.title = "Friendlyboard"
        
        leaderboard_embed.color = discord.Color.gold()
        leaderboard_embed.set_footer(text=f"The top users ordered by FRIENDSHIP POINTS")

        message = ""

        for person_id, person_user in spooky_ppl:
            friendship_points = person_user.friendshippoints
            # display_name = ctx.guild.get_member(person_id).display_name
            # no mentions in embed body?
            display_name = f"<@{person_id}>"

            # escape name
            # zero_width_space = '​'
            # display_name.replace('@', '@' + zero_width_space)

            # TODO different emoji if I feel like it
            # emoji = get_emoji_by_tokens(person_ghoultokens)
            emoji = ""
            if friendship_points > 0:
                emoji = "🙂"
            message += f"{emoji} **{friendship_points}** - {display_name}\n"
        
        leaderboard_embed.description = message
        await ctx.send("Maybe the real horrors were the friends we made along the way 🙂", embed=leaderboard_embed)

    @commands.command("balance")
    @commands.guild_only()
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def balance(self, ctx):
        """
        Views your current balance.
        """
        author_id = ctx.author.id
        user = await self.get_user(author_id)
        is_spooky = is_user_spooky(ctx.author)

        if user.ghoultokens == 0 and user.skelecoin == 0:
            if is_spooky:
                await ctx.send("you have nothing. truly, this is the spookiest fate.")
            else:
                await ctx.send("You got nothing and you aren't even Spooky yet.")
        else:
            msg = "Current balance:\n"
            if is_spooky:
                msg = "SPOOKY balance: (this means that you are SPOOKY)\n"
            if user.ghoultokens != 0:
                msg += f"{user.ghoultokens:.3f} GHOUL TOKENS\n"
            if user.skelecoin != 0:
                msg += f"{user.skelecoin:.3f} SKELE-COIN\n"
            
            if user.scarycash != 0:
                msg += f"{user.scarycash} SCARY CASH\n"
            if user.scarycash == scary_cash_total_supply:
                msg += "You own the entire supply of SCARY CASH."
            
            if abs(user.ghoultokens) in [69, 420, 1337] or abs(user.skelecoin) in [69, 420, 1337]:
                msg += "heh."
            
            await ctx.send(msg)

    @commands.command("doot")
    @commands.guild_only()
    @commands.cooldown(3, 60, commands.BucketType.user)
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

    @commands.command("skeleton?")
    @commands.guild_only()
    @commands.cooldown(3, 60, commands.BucketType.user)
    async def skeleton(self, ctx):
        """
        Skeleton?
        """
        is_spooky = is_user_spooky(ctx.author)
        if is_spooky:
            msg = "https://www.youtube.com/watch?v=BgFxeAq126g"
            await ctx.send(msg)

    @commands.command("unspooky")
    @commands.guild_only()
    @commands.cooldown(3, 60, commands.BucketType.user)
    async def skeleton(self, ctx):
        """
        This only works if you aren't spooky.
        """
        is_spooky = is_user_spooky(ctx.author)
        if is_spooky:
            return
        await ctx.send("🙂")
    
    @commands.command(name="send_ghoultokens", aliases=["send_gt", "send_ghoultoken"])
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def send_ghoultokens(self, ctx, recipient: discord.Member, amount: int):
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
                await self.update_user(recipient.id, delta_ghoultokens=(amount + 1), delta_skelecoin=None, delta_friendship_points=1)
                await ctx.send(f"TRANSFER COMPLETE. {get_sendoff()}")

    @commands.command(name="send_skelecoin", aliases=["send_sc", "send_skelecoins"])
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def send_skelecoins(self, ctx, recipient: discord.Member, amount: int):
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
                await self.update_user(recipient.id, delta_skelecoin=(amount), delta_friendship_points=1)
                await ctx.send(f"TRANSFER COMPLETE. {get_sendoff()}")

    @commands.command(name="free_skelecoin")
    @commands.guild_only()
    @commands.cooldown(1, 6000, commands.BucketType.user)
    async def send_skelecoin(self, ctx, recipient: discord.Member):
        """
        Send someone else free SKELE COIN!!! (Once every 6000 seconds)
        """

        if not self.is_feature_unlocked(">>free_skelecoin"):
            await ctx.send("You haven't unlocked this feature yet.")
            return

        if ctx.author.id == recipient.id:
            await ctx.send("no.")
            return

        amount = random.randint(1, 256)

        await self.update_user(ctx.author.id, delta_friendship_points=1)
        await self.update_user(recipient.id, delta_skelecoin=(amount))

        exclaim = random.randint(1, 20) * '!'

        await ctx.send(f"<@{ctx.author.id}> sent <@{recipient.id}> {amount} FREE SKELE COIN{exclaim}")

    @commands.command(name="send_scary_cash")
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def send_ghoultokens(self, ctx, recipient: discord.Member, amount_scary_cash: int):
        """
        Send someone some SCARY CASH.
        """
        if amount_scary_cash <= 0:
            await ctx.send("Nope")
        elif ctx.author.id == recipient.id:
            await ctx.send("no.")
        else:
            author_id = ctx.author.id
            user = await self.get_user(author_id)
            if user.scarycash >= amount_scary_cash:
                await self.update_user(author_id, delta_scary_cash=-amount_scary_cash)

                # sharing is very scary, so reward this behavior
                await self.update_user(recipient.id, delta_scary_cash=amount_scary_cash, delta_friendship_points=1)
                await ctx.send(f"TRANSFER COMPLETE. {get_sendoff()}")
            else:
                await ctx.send("You don't have enough SCARY CASH.")

    @commands.command(name="gambling!", hidden=True)
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def gambling_v1(self, ctx, lucky_number: int, wager_scary_cash: int):
        """
        Gambling!
        """
        remaining_supply = self.determine_remaining_scary_cash_supply()

        if remaining_supply == 0:
            await ctx.send("There isn't any SCARY CASH remaining in the bank, so you can't win anything.")
            return

        author_id = ctx.author.id
        user = await self.get_user(author_id)

        if wager_scary_cash <= 0:
            await ctx.send("you know I almost let this bug in, but not anymore")
            return

        if wager_scary_cash > user.scarycash:
            await ctx.send("You don't have that much SCARY CASH to wager.")
            return

        if random.randint(0, 1000) == lucky_number:
            payout = min(math.ceil(wager_scary_cash * 4.2), remaining_supply)
            await self.update_user(author_id, delta_scary_cash=payout)
            await ctx.send(f"Wow, you won ${payout} SCARY CASH.")
        else:
            await self.update_user(author_id, delta_scary_cash=-wager_scary_cash)
            await ctx.send("You lost.")

    @commands.command(name="gambling!!", hidden=True)
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def gambling_v2(self, ctx, lucky_number: int):
        """
        Gambling!!
        """
        if not self.is_feature_unlocked("gambling2"):
            return

        wager_scary_cash = 5
        remaining_supply = self.determine_remaining_scary_cash_supply()

        if remaining_supply == 0:
            await ctx.send("There isn't any SCARY CASH remaining in the bank, so you can't win anything.")
            return

        author_id = ctx.author.id
        user = await self.get_user(author_id)

        if wager_scary_cash <= 0:
            await ctx.send("you know I almost let this bug in, but not anymore")
            return

        if wager_scary_cash > user.scarycash:
            await ctx.send("You don't have that much SCARY CASH to wager.")
            return

        if random.randint(0, 10) == lucky_number:
            payout = min(math.ceil(wager_scary_cash * 2), remaining_supply)
            await self.update_user(author_id, delta_scary_cash=payout)
            await ctx.send(f"Wow, you won ${payout} SCARY CASH.")
        else:
            await self.update_user(author_id, delta_scary_cash=-wager_scary_cash)
            await ctx.send("You lost.")

    @commands.command("stonks")
    @commands.guild_only()
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def stonks(self, ctx):
        """
        View the conversion rate between Ghoul Tokens and Skele Coin.
        """
        if random.randint(0, 1000) == 10:
            await ctx.send("# BOO!")
            return

        author_id = ctx.author.id
        user = await self.get_user(author_id)
        is_spooky = is_user_spooky(ctx.author)

        user_balance = ""

        if user.ghoultokens > 0 or user.skelecoin > 0:
            user_balance = f"You have {user.ghoultokens:.3f} GHOUL TOKEN and {user.skelecoin:.3f} SKELE COIN available to trade."

        conversion_rate = self.get_stonk_value()
        msg = f"The current market conversion rate is:\n1 GHOUL TOKEN = {conversion_rate:.4f} SKELE COIN(S)\n1 SKELE COIN = {1 / conversion_rate:.4f} GHOUL TOKEN(S)"
        if user_balance:
            msg += f"\n{user_balance}"
        await ctx.send(msg)

    @commands.command("stonkchart", hidden=True)
    @commands.cooldown(3, 60, commands.BucketType.guild)
    @commands.guild_only()
    async def stonkcharts(self, ctx):
        """
        (COSTS 500 SKELE COIN) View Ghoul Token / Skele-Coin conversion rate as a graph.
        """

        user_id = ctx.author.id
        user = await self.get_user(user_id)

        price = 500

        if self.is_feature_unlocked("cheaper_stonkchart"):
            price = 5

        if user.skelecoin < price:
            await ctx.send("You do not have enough SKELE COIN.")
            return
        
        await self.update_user(user_id, delta_skelecoin=-price, delta_friendship_points=1)

        self.generate_image(False, 24)

        f = discord.File(open('spookystonks.png', 'rb'))

        if self.is_feature_unlocked("cheaper_stonkchart"):
            await ctx.send("Because `cheaper_stonkchart` was unlocked, this only costs 5 SKELE COIN now.", file=f)

        else:
            await ctx.send("hey so this code was really annoying to write and it's still not good so I'm charging you 500 SKELE COIN. No refunds.", file=f)

    @commands.command("insider_trading", hidden=True)
    @commands.cooldown(1, 600, commands.BucketType.guild)
    @commands.guild_only()
    async def insider_trading(self, ctx):
        """
        (Costs 10,000 SKELE COIN and a random amount of GHOUL TOKENS.)
        """

        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if user.skelecoin < 10_000:
            await ctx.send("You do not have enough SKELE COIN.")
            return
        
        gt = random.randint(1, 5000)

        await self.update_user(user_id, delta_skelecoin=-10_000, delta_ghoultokens=-gt)

        self.generate_image(True, 72)

        f = discord.File(open('spookystonks.png', 'rb'))

        await ctx.send(f"server time is {datetime.datetime.now()} btw", file=f)

    def get_value(self, time: datetime.datetime):

        if not self.is_feature_unlocked("grindsetneverends"):
            if time.day in [5, 11, 16, 21, 24, 29]:
                # maybe take the day off?
                return 4

        # the returned value is the conversion rate between the types of coins
        # or 1 ghoul token = value skele coins
        now = time
        t = 0.0001 - now.day * 0.5 - now.hour + now.minute / 60.0
        value = 5.0 + self.stonk_weight_f * t + 0.5 * math.sin(self.stonk_weight_a * t) + 0.8 * math.sin(self.stonk_weight_b * t) + 0.1 * math.sin(self.stonk_weight_c * t) + 2 * math.sin(t / self.stonk_weight_d) + 2 * math.cos(t / self.stonk_weight_e)
        if value < -0.5:
            return value

        value += (0.0001 * random.randint(0, 100))

        if time.hour % 7 == 0:
            value = math.floor(value)

        if time.hour % 8 == 0:
            value = math.ceil(value)

        return max(0.39, value)
    
    def make_data(self, future, hours=24):
        deltatime = datetime.timedelta(hours=hours)
        increment = datetime.timedelta(minutes=5)
        now = datetime.datetime.now()
        if future:
            # 48 hours ahead, 72 behind
            now = now + datetime.timedelta(hours=48)
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


    def generate_image(self, future, hours=24):
        import numpy as np
        import random
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        sayings = [
            "1 $GHOUL = Y $SKELE",
            "WE LIKE THE STONK",
            "SPOOOOOOOOOOOOOOKY",
            "SPOOKYHANDS",
            "BUY SPOOKY, SELL EVEN SPOOKIER",
            "DOOT DOOT"
        ]

        data_x, data_y, start_time, end_time, current = self.make_data(future, hours)

        plt.close()
        plt.cla()
        plt.title(f"1 $GHOUL = {current:.3f} $SKELE")
        plt.ylabel(random.choice(sayings))
        plt.xlabel(f"Previous {hours} hours")
        # plt.legend()
        plt.grid(True)
        # plt.plot(data_np, label="MONEEEYYYY")
        plt.plot(data_x, data_y, "g", label="MONNNEEYYYY")
        plt.xlim(left=start_time)
        # plt.xaxis.
        if future:
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%x %l:%M %P'))
        else:
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%l:%M %P'))
        plt.xticks(rotation=10,ha='right')
        plt.ylim(bottom=0)
        # show the current time
        plt.axvline(datetime.datetime.now(), label = "server time", color = "b")
        # plt.show()
        plt.savefig("spookystonks.png", dpi=240)


    @commands.command("trade_gt")
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def trade_gt(self, ctx, amount: int):
        """
        Sell an amount of Ghoul Tokens to buy Skele Coin at the current rate.
        """

        if not self.is_feature_unlocked("primetrading"):
            if is_market_closed():
                await ctx.send(get_market_closed_message())
                return

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
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def trade_sc(self, ctx, amount: int):
        """
        Sell an amount of Skele Coin to buy Ghoul Token at the current rate.
        """
        if is_market_closed():
            await ctx.send(get_market_closed_message())
            return

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

    # # y\ =500\ +\ 500\ \frac{5000}{x\ -\ 10}

    @commands.command("scary_cash", hidden=True)
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def check_scary_cash_exchange_rate(self, ctx):
        """
        Checks the current exchange rate of SCARY CASH to GHOUL TOKENs.
        """
        remaining_supply = self.determine_remaining_scary_cash_supply()
        exchange_rate = self.get_scary_cash_exchange_rate()

        msg = ""
        if remaining_supply == 0:
            msg += "There is no remaining supply of SCARY CASH in the bank. "
            # could show the distribution at this point
        else:
            msg += f"The bank has {remaining_supply / scary_cash_total_supply:.0%} of the SCARY CASH supply remaining. "
        
        msg += f"The exchange rate is $1 SCARY CASH = {exchange_rate:.2f} GHOUL TOKENs. "
        msg += get_sendoff()

        await ctx.send(msg)

    @commands.command("buy_scary_cash", hidden=True)
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def buy_scary_cash(self, ctx, amount_ghoul_token: int):
        """
        Exchanges an amount of GHOUL TOKENs to by SCARY CASH at the current exchange rate.
        """
        remaining_supply = self.determine_remaining_scary_cash_supply()
        if remaining_supply == 0:
            await ctx.send("There is no remaining supply of SCARY CASH available for purchase. Consider trading with others.")
            return

        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if amount_ghoul_token > user.ghoultokens:
            await ctx.send("You don't have that many GHOUL TOKENS")
            return
        # else:
        #     ghoultoken = math.floor(amount * (1 / self.get_stonk_value()))
        #     await self.update_user(user_id, delta_ghoultokens=ghoultoken, delta_skelecoin=-amount)
        #     await ctx.send(f"You sold {amount} SKELE COIN for {ghoultoken} GHOUL TOKEN. {get_sendoff()}")

        remaining_ghoul_token = amount_ghoul_token
        amount_purchased = 0

        while remaining_ghoul_token > 0 and remaining_supply > 0:
            # purchase one by one because supply is limited
            current_rate = self.get_scary_cash_rate(remaining_supply - amount_purchased)

            if current_rate > remaining_ghoul_token:
                # cost is too high to buy any more
                break
            
            amount_purchased += 1
            remaining_ghoul_token -= current_rate

        spent_ghoul_token = amount_ghoul_token - remaining_ghoul_token
        await self.update_user(user_id, delta_ghoultokens=-spent_ghoul_token, delta_scary_cash=amount_purchased)
        
        msg = f"Exchanged {spent_ghoul_token} GHOUL TOKEN for ${amount_purchased} SCARY CASH. There is {(remaining_supply - amount_purchased) / scary_cash_total_supply:.0%}% SCARY CASH remaining in the bank."
        await ctx.send(msg)
    
    def get_scary_cash_exchange_rate(self):
        remaining_supply = self.determine_remaining_scary_cash_supply()
        if remaining_supply == 0:
            return "∞"
        # y\ =500\ +\ 500\ \frac{5000}{x\ -\ 10}
        y = 500 + ((500 * scary_cash_total_supply) / (remaining_supply - 10))
        return y

    def get_scary_cash_rate(self, remaining_supply):
        # y\ =500\ +\ 500\ \frac{5000}{x\ -\ 10}
        y = 500 + ((500 * scary_cash_total_supply) / (remaining_supply - 10))
        return y

    @commands.command("secret", hidden=True)
    @commands.guild_only()
    @commands.cooldown(2, 60, commands.BucketType.user)
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
    @commands.cooldown(2, 60, commands.BucketType.user)
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

    @commands.command("millionaire", hidden=True)
    @commands.guild_only()
    async def millionaire(self, ctx):
        user_id = ctx.author.id
        user = await self.get_user(user_id)
        if user.ghoultokens > 1_000_000:
            await ctx.send("Wow good job ur a millionaire. Have some FREE +50 SKELE COIN")
            await self.update_user(user_id, delta_ghoultokens=None, delta_skelecoin=50)

    @commands.command("billionaire", hidden=True)
    @commands.guild_only()
    async def billionaire(self, ctx):
        """
        Exclusive to users with over a billion SKELE COIN.
        """
        user_id = ctx.author.id
        user = await self.get_user(user_id)
        if user.skelecoin > 1_000_000_000:
            await ctx.send("cool, now start over.")
            await self.update_user(user_id, delta_ghoultokens=-user.ghoultokens, delta_skelecoin=-user.skelecoin)
        else:
            richer = ""
            if random.randint(0, 50) == 1:
                richer = " [Come back when you're a little more... richer.](<https://www.youtube.com/watch?v=rfBtu0iyZFw>)"
            await ctx.send(f"Insufficient SKELE COIN.{richer}")

    def is_member_spooky(self, user: discord.Member) -> bool:
        """
        Check if member has a spooky role
        """
        if user is None:
            return False
        for r in user.roles:
            if r.id == spooky_roleid:
                return True
        return False

    @commands.command("spook")
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def spook_user(self, ctx, target_user: discord.Member):
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

            if not self.is_member_spooky(target_user):
                # first time spook deserves friendship
                await self.update_user(user_id, delta_friendship_points=100)

            # if they already have the role too bad should have noticed
            spooky_role = ctx.guild.get_role(spooky_roleid)
            await target_user.add_roles(spooky_role)
        else:
            await ctx.send(f"Come back again when you have some SKELE COIN. {get_sendoff()}")

    @commands.command("market_manipulation", hidden=True)
    @commands.guild_only()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def market_manipulation(self, ctx):
        """
        Manipulates the market. (Costs 50000 SKELE COIN, Spooky users only)
        """

        user_id = ctx.author.id
        is_spooky = is_user_spooky(ctx.author)

        if not(is_spooky):
            await ctx.send(f"Nah, not spooky enough 4 me")
            return

        if not self.is_feature_unlocked("primetrading"):
            if not is_market_closed():
                await ctx.send("The market is open right now, so you can't do that currently.")
                return
        
        user = await self.get_user(user_id)
        
        if user.skelecoin >= 50000:
            await self.update_user(user_id, delta_skelecoin=-50000, delta_friendship_points=1)

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
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def this_does_nothing(self, ctx):
        """
        This command does nothing, but can only be used by spooky people.
        """
        is_spooky = is_user_spooky(ctx.author)
        if not is_spooky:
            await self.update_user(ctx.author.id, delta_skelecoin=-1)
            await ctx.send(f"This command only does nothing if you are spooky. Since you aren't spooky, I'm subtracting a single SKELE COIN. {get_sendoff()}")

    @commands.command(name="trade_gc", aliases=["trade_st"], hidden=True)
    @commands.guild_only()
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def you_fool(self, ctx):
        await self.update_user(ctx.author.id, delta_skelecoin=-1)
        await ctx.send(f"You fool, it's GHOUL TOKEN and SKELE COIN, not SKELE TOKEN and GHOUL COIN. I have subtracted 1 SKELE COIN from your account. {get_sendoff()}")

    @commands.command(name="helphelphelphelphelphelphelphelphelphelphelp", hidden=True)
    @commands.guild_only()
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def helphelphelphelphelphelphelphelphelphelphelp(self, ctx):
        is_spooky = is_user_spooky(ctx.author)
        if is_spooky:
            await ctx.send("N̶̛͚̹̣͔̾̂̒̋̋̈́̇́̓̓͜͠͝ͅǪ̴̛̭̬͙̫̀̓̄̃̉̓́̿̏̐̋̅̌̑B̵̲̈̉͛̕͝O̵͙̰̮̼͍̫͑̄̄̀D̸̢͈̤̜̺͎͕̤̭̰̻͗̏̽̓͗͂͐̋̀̓͆̚͝ͅỲ̶͉̾̿͋́́̽͘ ̷̛̛͎̝̂̿̓̉̾́̆́̇C̸͚͕͕͑Ą̵̧̛̳̮͈̯̹̙͌̈́̈́̇͒̎̀͂͜N̷̨̨͔͍̖̯͍̫͖̦̝̽̾̐ ̸̨̢̛͍̲̟̠̬̮̞͕̭͐́̈́͒͆̈́̏͛͘H̵̛̬͓̲͙̾̍̏̿̎̆͋̽̕͘͜͠͝É̵̗̖̫̆̆̃̎̅̾͑̓̈́͊̅̀̕ͅL̴̝͈̾̿̔͒̔̅̆̈͊͐P̷̡̡̬͎̠̻͙̦̗̗̞͗́̽̓̉̃͑̀͒̈́͗ͅ ̷̢̯̝̞͉̹̬̎̐Ý̴̡̡̹̬̯̹̣̗̪̳̪̾̈͜Ọ̴̣͕͚̰͚̀̀͊̿̓͆̅̆̾͛͆͘͠U̸͖̽̊ ̸̛̞͍̺͕̱̯̜̠̺͓͆͛̔͋͋̓͋̿͆͛̉̍͜͠ͅN̸͙̜̆̓Ơ̸̬͕̮̹̝͕̤̻̯̩̣̜̏̿͗̀̔̀͜͝ͅW̷̖̱̻̻̮̬̤͈̰̜̌̓̅͘ͅ" + " " + get_sendoff())
        else:
            await ctx.send("Oops! Looks like you made a typo. You meant `>>help`.")

    @commands.command("nickname")
    @commands.guild_only()
    @commands.cooldown(3, 60, commands.BucketType.user)
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

    def get_shop_items(self):
        """
        """

        # key is the feature which unlocks the items, value is a list of the items added
        # where each index is (feature_name, (feature attributes list))

        #         store = {
        #     # key is feature name, value is tuple of price, currency, and description text
        #     "primetrading": (12500, "skelecoin", "Enables trading during prime minutes."),

        #     "spookysaturday": (1000, "ghoultokens", "All GHOUL TOKENS earned on Saturdays are multiplied 5x. Does not apply to the STONK market."),

        #     "friendship": (999, "skelecoin", "Unlocks friendship."),

        #     "gambling2": (2500, "ghoultokens", "Unlocks GAMBLING 2."),

        #     "cheaper_stonkchart": (1337, "ghoultokens", "Reduces the cost of `>>stonkchart` to 5 SKELE COIN.")
        # }
        additional_items = {
            "friendship": {
                "scopecreep": (100, "skelecoin", "scopecreep"),

                ">>free_skelecoin": (419, "ghoultokens", "Enables `>>free_skelecoin`.")
            },

            "scopecreep" : {
                "scopecreep2": (1000, "skelecoin", "Scope creep 2."),
            },

            "scopecreep2" : {
                "scopecreep3": (10000, "skelecoin", "Scope creep 3."),

                "grindsetneverends": (5000, "ghoultokens", "don't freeze the stonk market on certain days")
            },

            "scopecreep3" : {
                "scopecreepN": (100000, "skelecoin", "Scope creep N."),
            },

            "scopecreepN" : {
                "scopecreepN+1": (100001, "skelecoin", "Scope creep N+1."),
            },

            "scopecreepN+1" : {
                "hasthisjokeoverstayeditswelcomeyet": (1, "skelecoin", "because I'm starting to think so"),
            },

            "hasthisjokeoverstayeditswelcomeyet" : {
                "orshouldIkeepgoing": (2, "skelecoin", "?"),
            },

            "orshouldIkeepgoing" : {
                "hmm": (3, "skelecoin", ""),
            },

            "hmm" : {
                "scopecreep∞": (99999999999999, "skelecoin", "you'll get there eventually"),
            },
        }

        # for every feature unlocked, add the keys and values from the sub directories to the shop
        combined_shop = store

        for feature in self.state.unlockedfeatures:
            if feature in additional_items:
                additional_shop_items = additional_items[feature]
                combined_shop.update(additional_shop_items)
            #combined_shop.update(additional_items[])

        return combined_shop

    @commands.command("feature_store", hidden=True)
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def feature_store(self, ctx):
        """
        Lists the features available for purchase via the >>buy_feature command.
        """
        # too lazy for an embed
        msg = "**Feature Store**\n"

        for feature_name in self.get_shop_items():
            value = self.get_shop_items()[feature_name]
            (price, currency, description) = value
            if self.is_feature_unlocked(feature_name):
                msg += "**Unlocked** "
            msg += f"`{feature_name}` **{price} {currency}**: {description}\n"

        msg += "\nYou can buy these using `>>buy_feature`"
        
        await ctx.send(msg)

    @commands.command("buy_feature", hidden=True)
    @commands.guild_only()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def buy_feature(self, ctx, feature_name: str):
        """
        Buys a feature.
        """
        user_id = ctx.author.id

        feature_name = feature_name.lower()

        if self.is_feature_unlocked(feature_name):
            await ctx.send("This feature is already unlocked.")
            return

        (feature_price, feature_currency, feature_description) = self.get_shop_items()[feature_name]

        result = False

        if feature_currency == "skelecoin":
            result = await self.try_transact(user_id=user_id, skelecoin=feature_price)
        
        if feature_currency == "ghoultokens":
            result = await self.try_transact(user_id=user_id, ghoultoken=feature_price)

        if result:
            await ctx.send(f"You spent {feature_price} {feature_currency} to unlock the feature `{feature_name}`: {feature_description}.")
            await self.unlock_feature_async(feature_name, user_id)

            await self.update_user(user_id, delta_friendship_points=750)
        else:
            await ctx.send("Insufficient funds.")
    
    async def try_transact(self, user_id, ghoultoken=None, skelecoin=None):
        """
        Returns TRUE if the transaction went through, otherwise FALSE.
        Charges the user and updates balance.
        """
        user = await self.get_user(user_id)

        # check balance

        if ghoultoken is not None:
            if user.ghoultokens < ghoultoken:
                return False
        else:
            ghoultoken = 0

        if skelecoin is not None:
            if user.skelecoin < skelecoin:
                return False
        else:
            skelecoin = 0

        await self.update_user(user_id, delta_ghoultokens=-ghoultoken, delta_skelecoin=-skelecoin)
        return True

    @commands.command("scary_garden", hidden=True)
    @commands.guild_only()
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def scary_garden(self, ctx):
        """
        Garden, but scary. (Requires being spooky, and costs 62 ghoul tokens)
        """

        # dunno how much effort it takes to customize the help command to show commands only to users who are spooky
        # not sure if I care that much

        is_spooky = is_user_spooky(ctx.author)
        if not is_spooky:
            await ctx.send(f"🌲 Spooky users only. 🍄 {get_sendoff()}")
            return

        user_id = ctx.author.id
        user = await self.get_user(user_id)

        if 62 >= user.ghoultokens:
            await ctx.send("You do not have enough GHOUL TOKENS.")
            return
        else:
            await self.update_user(user_id, delta_ghoultokens=-62, delta_skelecoin=None)

        # 🕷️🕸️🪳🪱🐛🐀🐈‍⬛🥀🍂🍁🎃👻🧛

        filler = '🪦'
        flowers = [
                '🥀',
                '🪦',
                '🕯️',
                '🕸️',
                '🏚️',
            ]
        plants = [
                '🥀',
                '🍂',
                '🍁'
            ]
        ghouls = [
               '🎃','👻','🧛','😱','💀','🧛',
            ]
        animals = [
                '🕷️','🪳','🪱','🐛','🐈‍⬛','🦇','🦉','🪲'
        ]

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
            for i in range(random.randint(8, 16)):
                garden[idx] = random.choice(flowers)
                idx += 1
            # then animals
            for i in range(random.randint(1, 3)):
                garden[idx] = random.choice(animals)
                idx += 1
            # vegertals
            for i in range(random.randint(5, 10)):
                garden[idx] = random.choice(ghouls)
                idx += 1
            # other green leafy things
            for i in range(random.randint(5, 8)):
                garden[idx] = random.choice(plants)
                idx += 1
            # fill remaining array with seedlings
            for i in range(idx, 64):
                garden[i] = filler

            # shuffle and assemble garden
            random.shuffle(garden)
            for i in range(8):
                garden[i * 8 + 7] = garden[i * 8 + 7] + '\n'
            await ctx.send(''.join(garden))

    # @commands.command("buy_scary_cash", hidden=True)
    # @commands.guild_only()
    # @commands.cooldown(2, 60, commands.BucketType.user)
    # async def buy_scary_cash(ctx, amount):
    #     """
    #     Exchanges an amount of GHOUL TOKEN for SCARY CASH.
    #     (1 SCARY CASH == 500,000 GHOUL TOKEN)

    #     There is a limited amount of SCARY CASH in rotation.
    #     """

    #     if not amount in primes:
    #         ctx.send("You can't trade ")


def setup(bot):
    bot.add_cog(SpookyMonth(bot))