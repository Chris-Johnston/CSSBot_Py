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

from dataclasses import dataclass, field

# this did not work well for this case, would not recommend
# from dataclasses_json import dataclass_json
from dataclass_wizard import JSONWizard

# Constants for game mechanics
MUMMY_PARTS_SEQUENCE = ["legs", "arms", "head", "torso", "foot"]
MUMMY_PART_COSTS = [50, 50, 200, 300, 500]
STRUCTURE_COSTS = {
    "command_center": 1000,
    "refinery": 500,
    "graveyard": 750,
    "watchtower": 300,
    "barracks": 800,  # Add the cost for barracks here
}

WATCHTOWER_POWER_BOOST = 0.01  # Boost percentage for army power level
SKELETON_STRUCTURE_COST_MULTIPLIER = 3  # 3x cost for skeleton structures
# Define units, including secret units, but make them inaccessible initially
GHOUL_UNITS = {
    "ghouls": {"power": 10, "cost": 20},
    "wraiths": {"power": 20, "cost": 50},
    "ghosts": {"power": 30, "cost": 75},
    "zombies": {"power": 40, "cost": 100},
    "giant ghoul": {"power": 100, "cost": 300},
    "zombie giant": {"power": 500, "cost": 1000},  # Secret unit, initially locked
    "beanglove": {"power": 5000, "cost": 3000},  # Secret unit, initially locked
}
SKELETON_UNITS = {
    "skeletons": {"power": 10, "cost": 20},
    "mummy_part": {"power": 0, "cost": MUMMY_PART_COSTS},
    "mummy": {"power": 1000, "cost": sum(MUMMY_PART_COSTS)},
    "brendan_fraser": {"power": 5000, "cost": 3000},  # Secret unit, initially locked
}


@dataclass
class User:
    ghoultokens: int = 0
    skelecoin: int = 0
    bonemeal: int = 0
    bones: int = 0
    ectoplasm: int = 0
    cursed_meat: int = 0
    side: str = ""
    structures: dict = field(
        default_factory=lambda: {
            "command_center": False,
            "refinery": False,
            "graveyard": 0,
            "watchtower": False,
            "barracks": 0,
        }
    )
    units: dict = field(default_factory=dict)
    unlocked_units: list = field(default_factory=list)  # Track unlocked special units
    mummy_parts: int = 0
    build_times: dict = field(default_factory=dict)
    last_interaction: float = field(default_factory=time.time)
    last_barracks_built: datetime.datetime = None

    def get_power_level(self):
        total_power = sum(
            details["power"] * details["quantity"] for details in self.units.values()
        )
        if self.structures.get("watchtower"):
            total_power *= 1 + WATCHTOWER_POWER_BOOST
        return int(total_power)

    def get_unit_count(self):
        return sum(details["quantity"] for details in self.units.values())


@dataclass
class State(JSONWizard):
    last_updated: int  # timestamp
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
    zero_width_space = "​"
    text.replace("@", "@" + zero_width_space)
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
        "${ADJECTIVE}",
    ]
    return f"Have a {random.choice(adjectives)} day!"


class SpookyMonth(commands.Cog):
    """
    SpooOOOOooOOOoookyyyyyy!
    """

    def __init__(self, bot):

        now = datetime.datetime.now()
        allow_spooky = True

        # Game addition
        self.bot = bot
        self.state = {"users": {}}
        # Load battle outcome messages for skeleton and ghoul victories
        self.battle_outcomes_skeleton = self.load_battle_outcomes(
            "battle_outcomes_skeleton.txt"
        )
        self.battle_outcomes_ghoul = self.load_battle_outcomes(
            "battle_outcomes_ghoul.txt"
        )

        if now.month != 10:
            # 3 day grace period
            if now.month == 11 and now.day < 3:
                # ok
                allow_spooky = True
                pass
            else:
                allow_spooky = False

        # I'm pretty sure I restart this bot daily so this should do
        if not (allow_spooky):
            logger.info("date is not in spooky month range, so not running")
            return

        # keyed by user Id, with a dict for the attributes for each user
        self.state_mutex = asyncio.Lock()
        # running an old version of python oh well

        asyncio.create_task(self.read_state())
        # asyncio.run(self.read_state())

        with open(spooky_phrases_file, "rt") as s:
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
        with open(spooky_nicknames, "rt") as n:
            self.nickname_fmt_strings = n.read().splitlines()

    def get_stonk_value(self):
        # the returned value is the conversion rate between the types of coins
        # or 1 ghoul token = value skele coins
        now = datetime.datetime.now()
        t = 0.0001 - now.day * 0.2 + now.hour + now.minute / 60.0
        value = (
            5.0
            + self.stonk_weight_f * t
            + 0.5 * math.sin(self.stonk_weight_a * t)
            + 0.8 * math.sin(self.stonk_weight_b * t)
            + 0.1 * math.sin(self.stonk_weight_c * t)
            + 2 * math.sin(t / self.stonk_weight_d)
            + 2 * math.cos(t / self.stonk_weight_e)
        )
        if value < -0.5:
            return value
        return max(0.001, value)

    # Game addition
    def load_battle_outcomes(self, filename, keyword=None):
        """
        Loads battle outcome messages from a specified text file, optionally filtered by a keyword.

        Args:
            filename (str): The name of the text file to load battle outcomes from.
            keyword (str, optional): If provided, only lines containing this keyword will be loaded.

        Returns:
            list: A list of strings representing filtered battle outcome messages.
        """
        try:
            with open(filename, "r") as file:
                lines = [line.strip() for line in file.readlines()]
                if keyword:
                    lines = [line for line in lines if keyword in line.lower()]
                return lines
        except FileNotFoundError:
            return []

    async def join_side(self, ctx, side):
        user = await self.get_user(ctx.author.id)

        # Check if the user has already joined a side
        if user.side:
            await ctx.send(
                f"You have already joined the {user.side.capitalize()}! You cannot switch sides."
            )
            return

        # Assign the side if not already joined
        user.side = side
        self.state.users[ctx.author.id] = user
        await ctx.send(
            f"Welcome to the {side.capitalize()}! Use `>>base` to see your structures and `>>units` to manage your army."
        )

    async def update_resources_since_last_interaction(self, user_id):
        """
        Calculates and updates resources for a user based on the time elapsed since their last interaction.

        This function calculates how many resources a user has gathered based on the number of hours that have
        passed since their last recorded interaction. Resources such as bonemeal and ectoplasm are generated
        depending on the user's side (skeletons or ghouls) and the number of graveyards owned. Refineries convert
        bonemeal to bones or ectoplasm to cursed meat at an increased rate based on the number of graveyards.

        Args:
            user_id (int): Unique identifier for the user.

        Returns:
            None
        """
        user = self.state.users.get(user_id)
        if not user:
            return

        # Calculate time difference in hours using Unix timestamp
        now = time.time()
        time_elapsed = (now - user.last_interaction) / 3600  # Convert seconds to hours

        # Calculate resources gained based on elapsed time and number of graveyards/refinery
        if user.structures["graveyard"] > 0:
            if user.side == "skeletons":
                bonemeal_gained = int(5 * user.structures["graveyard"] * time_elapsed)
                await self.update_user(user_id, delta_bonemeal=bonemeal_gained)
            else:
                ectoplasm_gained = int(5 * user.structures["graveyard"] * time_elapsed)
                await self.update_user(user_id, delta_ectoplasm=ectoplasm_gained)

        # Refinery processing based on elapsed time and number of graveyards
        if user.structures["refinery"]:
            if user.side == "skeletons":
                # Convert bonemeal to bones
                converted_bonemeal = int(
                    min(user.bonemeal, 3 * user.structures["graveyard"] * time_elapsed)
                )
                await self.update_user(
                    user_id,
                    delta_bonemeal=-converted_bonemeal,
                    delta_bones=converted_bonemeal,
                )
            else:
                # Convert ectoplasm to cursed meat
                converted_ecto = int(
                    min(user.ectoplasm, 3 * user.structures["graveyard"] * time_elapsed)
                )
                await self.update_user(
                    user_id,
                    delta_ectoplasm=-converted_ecto,
                    delta_cursed_meat=converted_ecto,
                )

        # Update last interaction time to the current Unix time
        user.last_interaction = now
        await self.write_state()

    # who needs a database, json is MY database
    async def read_state(self):
        logger.info("reading state from file")
        try:
            async with self.state_mutex:
                with open(spooky_state_file, "rt") as s:
                    # self.state = from_json_actual(s.read())
                    self.state = State.from_json(s.read())

                    # hack to fix shortcomings in serialization
                    # why did I even bother with dataclasses
                    actual_state = {}
                    for k, v in self.state.users.items():
                        user_id = int(k)
                        actual_state[user_id] = User(v["ghoultokens"], v["skelecoin"])
                    self.state.users = actual_state
                    logger.info(f"state is: {self.state}")
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
                with open(spooky_state_file, "wt") as s:
                    # json_text = self.state.to_json_actual()
                    json_text = self.state.to_json()
                    s.write(json_text)
        except Exception as e:
            logger.warn("failed to write state for some reason idk", e)

    async def update_user(
        self,
        user_id,
        delta_ghoultokens=None,
        delta_skelecoin=None,
        delta_bonemeal=0,
        delta_bones=0,
        delta_ectoplasm=0,
        delta_cursed_meat=0,
    ):
        logger.info(
            f"update user_id {user_id} ghoul {delta_ghoultokens} skele {delta_skelecoin}"
        )

        # Access self.state.users as the dictionary
        if user_id in self.state.users:
            user = self.state.users[user_id]
            if delta_ghoultokens is not None:
                user.ghoultokens += delta_ghoultokens
            if delta_skelecoin is not None:
                user.skelecoin += delta_skelecoin
            if delta_bonemeal != 0:
                user.bonemeal += delta_bonemeal
            if delta_bones != 0:
                user.bones += delta_bones
            if delta_ectoplasm != 0:
                user.ectoplasm += delta_ectoplasm
            if delta_cursed_meat != 0:
                user.cursed_meat += delta_cursed_meat
        else:
            logger.info(f"new user user_id {user_id}")
            self.state.users[user_id] = User(
                delta_ghoultokens or 0, delta_skelecoin or 0
            )
            self.state.users[user_id].bonemeal += delta_bonemeal
            self.state.users[user_id].bones += delta_bones
            self.state.users[user_id].ectoplasm += delta_ectoplasm
            self.state.users[user_id].cursed_meat += delta_cursed_meat

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
    @commands.command("cheat_ghoultokens")
    @commands.guild_only()
    async def cheat_ghoultokens(self, ctx, user: discord.User, delta_ghoultokens: int):
        """
        Cheat c0deZ to update the ghoultokens for a user
        """
        if ctx.author.id in lazy_admins:
            await self.update_user(user.id, delta_ghoultokens=delta_ghoultokens)

    @commands.command("cheat_skelecoin")
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
        spooky_ppl = sorted(
            self.state.users.items(), key=lambda x: x[1].ghoultokens, reverse=True
        )[:10]

        leaderboard_embed = discord.Embed()
        leaderboard_embed.title = "Spookyboard"
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

            if abs(user.ghoultokens) in [69, 420, 1337] or abs(user.skelecoin) in [
                69,
                420,
                1337,
            ]:
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
            await ctx.send(
                f"Insufficient funds. You have `{user.ghoultokens}` ghoul tokens. {get_sendoff()}"
            )

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
            await self.update_user(
                ctx.author.id, delta_ghoultokens=-1, delta_skelecoin=None
            )
        elif ctx.author.id == recipient.id:
            await ctx.send("no.")
        else:
            author_id = ctx.author.id
            user = await self.get_user(author_id)
            if user.ghoultokens >= amount:
                await self.update_user(
                    author_id, delta_ghoultokens=-amount, delta_skelecoin=None
                )

                # fun :)
                if random.randint(0, 10000) == 123:
                    amount *= 100

                # sharing is very scary, so reward this behavior
                await self.update_user(
                    recipient.id, delta_ghoultokens=(amount + 1), delta_skelecoin=None
                )
                await ctx.send(f"TRANSFER COMPLETE. {get_sendoff()}")

    @commands.command(name="send_skelecoin", aliases=["send_sc", "send_skelecoins"])
    @commands.guild_only()
    async def send_skelecoins(self, ctx, recipient: discord.User, amount: int):
        """
        Send someone some skele coin
        """
        if amount < 0:
            await ctx.send(
                "If you send me 5,000,001 skele coin I will let you do this. Once. I am serious."
            )
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
            await self.update_user(
                user_id, delta_ghoultokens=-amount, delta_skelecoin=skelecoin
            )
            await ctx.send(
                f"You sold {amount} GHOUL TOKEN for {skelecoin} SKELE COIN. Have a SPOOKY day."
            )

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
            await self.update_user(
                user_id, delta_ghoultokens=ghoultoken, delta_skelecoin=-amount
            )
            await ctx.send(
                f"You sold {amount} SKELE COIN for {ghoultoken} GHOUL TOKEN. {get_sendoff()}"
            )

    @commands.command("secret")
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

    @commands.command("buy_art")
    @commands.guild_only()
    async def buy_art(self, ctx):
        """
        Exchange 5,000 Ghoul Tokens for one-of-a-kind art.
        """
        user_id = ctx.author.id
        user = await self.get_user(user_id)

        amount = 5000
        if amount > user.ghoultokens:
            await ctx.send(
                f"You do not have enough GHOUL TOKEN. Come back when you have more. {get_sendoff()}"
            )
        else:
            await ctx.send(
                f"Wow. I can truly see that you appreciate only the finest of art. I am generating your new one-of-a-kind piece now. {get_sendoff()}"
            )
            await self.update_user(
                user_id, delta_ghoultokens=-5000, delta_skelecoin=None
            )

            nft = str(uuid.uuid4())
            await ctx.send(
                f"<@{user_id}>, here is your exclusive and one-of-a-kind art:\n`{nft}`\nYou are now the sole owner of this string of characters forever. Good job. {get_sendoff()}"
            )

    @commands.command("millionaire")
    @commands.guild_only()
    async def millionaire(self, ctx):
        user_id = ctx.author.id
        user = await self.get_user(user_id)
        if user.ghoultokens > 1_000_000:
            await ctx.send(
                "Wow good job ur a millionaire. Have some FREE +50 SKELE COIN"
            )
            await self.update_user(user_id, delta_ghoultokens=None, delta_skelecoin=50)

    @commands.command("billionaire")
    @commands.guild_only()
    async def billionaire(self, ctx):
        user_id = ctx.author.id
        user = await self.get_user(user_id)
        if user.skelecoin > 1_000_000_000:
            await ctx.send("cool, now start over.")
            await self.update_user(
                user_id,
                delta_ghoultokens=-user.ghoultokens,
                delta_skelecoin=-user.skelecoin,
            )
        else:
            await ctx.send(
                "😤😤😤 The 👀 grind 🎯💰 never 😎 stops 💪 😤😤. Keep up the grind!"
            )

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
            await ctx.send(
                f"SpooOOOooOOooky... You have been charged {cost} SKELE COIN\n<@{target_user.id}> has been spooked by <@{user_id}>!"
            )
            await self.update_user(
                user_id, delta_ghoultokens=None, delta_skelecoin=-cost
            )

            # if they already have the role too bad should have noticed
            spooky_role = ctx.guild.get_role(spooky_roleid)
            await target_user.add_roles(spooky_role)
        else:
            await ctx.send(
                f"Come back again when you have some SKELE COIN. {get_sendoff()}"
            )

    @commands.command("market_manipulation")
    @commands.guild_only()
    async def market_manipulation(self, ctx):
        """
        Manipulates the market. (Costs 50 SKELE COIN, Spooky users only)
        """
        user_id = ctx.author.id
        is_spooky = is_user_spooky(ctx.author)

        if not (is_spooky):
            await ctx.send(
                f"YOU. {get_sendoff()} MUST. {get_sendoff()} BE. {get_sendoff()} SPOOKY. {get_sendoff()}"
            )
            return

        user = await self.get_user(user_id)

        if user.skelecoin >= 50:
            await self.update_user(user_id, delta_skelecoin=-50)

            self.stonk_weight_a = random.randint(1, 10)
            self.stonk_weight_b = random.randint(1, 10)
            self.stonk_weight_c = random.randint(1, 10)
            self.stonk_weight_d = random.randint(1, 10)
            self.stonk_weight_e = random.randint(1, 10)
            self.stonk_weight_f = -random.randint(10, 20) / 100.0

            await ctx.send(
                "The market variables have been randomized for now. This may or may not have done anything. Good job?"
            )
        else:
            await ctx.send("You don't have enough SKELE COIN for this.")

    @commands.command("this_does_nothing")
    @commands.guild_only()
    async def this_does_nothing(self, ctx):
        """
        This command does nothing, but can only be used by spooky people.
        """
        is_spooky = is_user_spooky(ctx.author)
        if not is_spooky:
            await self.update_user(ctx.author.id, delta_skelecoin=-1)
            await ctx.send(
                f"This command only does nothing if you are spooky. Since you aren't spooky, I'm subtracting a single SKELE COIN. {get_sendoff()}"
            )

    @commands.command(name="trade_gc", aliases=["trade_st"])
    @commands.guild_only()
    async def you_fool(self, ctx):
        await self.update_user(ctx.author.id, delta_skelecoin=-1)
        await ctx.send(
            f"You fool, it's GHOUL TOKEN and SKELE COIN, not SKELE TOKEN and GHOUL COIN. I have subtracted 1 SKELE COIN from your account. {get_sendoff()}"
        )

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
            await ctx.send(
                f"Spooky users only. Come back when you are SPOOKY. {get_sendoff()}"
            )
            return

        user = await self.get_user(user_id)
        if user.skelecoin > 1000:
            await ctx.send(
                f"You actually have too much SKELE COIN to use this command. Come back when you have less SKELE COIN. {get_sendoff()}"
            )
            return

        if user.ghoultokens % 3 == 0:
            await ctx.send(
                f"This command only works if your number of GHOUL TOKEN is not a multiple of THREE. {get_sendoff()}"
            )
            return

        if abs(user.skelecoin) >= 100:
            await self.update_user(user_id, delta_skelecoin=-10)

            current_nickname = ctx.author.display_name
            fmt_str = random.choice(self.nickname_fmt_strings)
            new_nickname = fmt_str.format(current_nickname)
            new_nickname = escape(new_nickname)
            await ctx.author.edit(nick=new_nickname)
            await ctx.send(
                f"Prest-o! Change-o! Here's your new nickname. In case it got truncated it was: `{new_nickname}` {get_sendoff()}"
            )
        else:
            await ctx.send(
                f"So here's the thing. This command only costs 10 SKELE COIN, but you do need an absolute balance greater than 100 SKELE COIN to use it. {get_sendoff()}"
            )

    """
    Spooky game addition
    :)))
    """
    battle_log = []  # to store the battle history

    async def record_battle(self, attacker, defender, outcome):
        """
        Records the outcome of a battle for history tracking.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"{timestamp}: {attacker} vs {defender} - Outcome: {outcome}"
        self.battle_log.append(record)

    # --- Game Commands ---

    @commands.command("battle_history")
    async def battle_history(self, ctx):
        """
        Shows the past 10 battles and their outcomes.
        """
        if not self.battle_log:
            await ctx.send("No battles have been recorded recently.")
            return

        history = "\n".join(self.battle_log[-10:])  # Show last 10 battles
        await ctx.send(f"**Battle History:**\n{history}")

    @commands.command("spooky_bases")
    async def spooky_bases(self, ctx):
        """
        Shows a list of all available player bases, with 'danger level' for both allies and enemies.
        Enemy bases are clearly marked.
        """
        user_side = self.state.users[ctx.author.id].side  # Get the command user's side
        base_list = "**Available Bases:**\n"

        for user_id, user in self.state.users.items():
            danger_level = user.get_power_level()
            # Mark enemy bases with a warning symbol and distinguish them from allies
            if user.side == user_side:
                base_list += f"🛡️ Ally: <@{user_id}> - Danger Level: {danger_level}\n"
            else:
                base_list += f"⚔️ Enemy: <@{user_id}> - Danger Level: {danger_level}\n"

        if base_list:
            await ctx.send(base_list)
        else:
            await ctx.send("No bases available.")

    @commands.command("join_skeletons")
    async def join_skeletons(self, ctx):
        await self.join_side(ctx, "skeletons")

    @commands.command("join_ghouls")
    async def join_ghouls(self, ctx):
        await self.join_side(ctx, "ghouls")

    @commands.command("base")
    async def base(self, ctx):
        """
        Displays the player's base structures and current resource levels.

        This command shows a player's current base structures, their completion status, and costs. It also
        provides an overview of the player's current resources, including bonemeal and bones for skeletons
        or ectoplasm and cursed meat for ghouls. The function first updates resources based on elapsed time
        since the last interaction before showing the updated values.

        Args:
            ctx (Context): Discord command context for the player requesting the base information.

        Returns:
            None
        """
        user = self.state.users.get(ctx.author.id)
        if not user:
            await ctx.send(
                "You have not joined a side yet! Use `>>join_ghouls` or `>>join_skeletons` to get started."
            )
            return

        # Determine currency name based on side
        currency = "ghoul tokens" if user.side == "ghouls" else "skelecoin"

        base_info = f"**Your Base Structures**:\n"
        base_info += "\n".join(
            f"{name.capitalize()}: {'Built' if built else 'Not Built'} (Cost: {STRUCTURE_COSTS.get(name, 'Unknown')} {currency})"
            for name, built in user.structures.items()
            if name != "graveyard"
        )
        base_info += f"\nGraveyard: {user.structures.get('graveyard', 0)} (Cost: {STRUCTURE_COSTS.get('graveyard', 'Unknown')} {currency})\n"

        # Display current resources
        base_info += f"\n\n**Resources**:"
        if user.side == "skeletons":
            base_info += f"\nBonemeal: {user.bonemeal}\nBones: {user.bones}"
        else:
            base_info += (
                f"\nEctoplasm: {user.ectoplasm}\nCursed Meat: {user.cursed_meat}"
            )

        await ctx.send(base_info)

    @commands.command("units")
    async def units(self, ctx):
        user = self.get_user(ctx.author.id)
        units_info = f"{ctx.author.display_name}'s Units:\n"
        for unit, details in user.units.items():
            units_info += f"{unit.capitalize()} - Power: {details['power']}, Quantity: {details['quantity']}\n"
        units_info += f"Total Power Level: {user.get_power_level()}"

        if user.side == "skeletons":
            mummy_info = f"\nMummy Parts Collected: {user.mummy_parts}/{len(MUMMY_PARTS_SEQUENCE)}"
            units_info += mummy_info

        await ctx.send(units_info)

    @commands.command("buy")
    async def buy(self, ctx, item_name: str):
        """
        Handles purchasing of base structures or units for the player.

        This command enables players to buy structures (e.g., refinery, graveyard) or units (e.g., skeletons,
        ghouls) using resources they have accumulated. It first updates resources based on the time elapsed
        since the player's last interaction, then checks if the requested item is available and deducts the
        necessary resources if the player can afford it.

        Args:
            ctx (Context): Discord command context for the player initiating the purchase.
            item_name (str): Name of the item to be purchased (structure or unit).

        Returns:
            None
        """
        user = self.state.users.get(ctx.author.id)
        if not user:
            await ctx.send(
                "Please join a side first using `>>join_skeletons` or `>>join_ghouls`."
            )
            return

        if item_name in STRUCTURE_COSTS:
            await self.buy_structure(ctx, ctx.author.id, item_name)
        elif item_name in (SKELETON_UNITS if user.side == "skeletons" else GHOUL_UNITS):
            await self.buy_unit(ctx, ctx.author.id, item_name)
        else:
            await ctx.send(f"{item_name.capitalize()} is not available for your side.")

    async def buy_structure(self, ctx, user_id, structure_name):
        """
        Handles purchasing of a base structure for a player.
        """
        user = self.state.users[user_id]

        # Check if the structure is a barracks and apply the daily build limit
        if structure_name == "barracks":
            if (
                user.last_barracks_built
                and (datetime.datetime.now() - user.last_barracks_built).days < 1
            ):
                await ctx.send("You can only build one barracks per day.")
                return

            user.last_barracks_built = datetime.datetime.now()

        # Calculate cost (skeletons have a cost multiplier)
        cost = STRUCTURE_COSTS[structure_name] * (
            SKELETON_STRUCTURE_COST_MULTIPLIER if user.side == "skeletons" else 1
        )

        if (user.skelecoin if user.side == "skeletons" else user.ghoultokens) >= cost:
            await self.update_user(
                user_id,
                delta_skelecoin=-cost if user.side == "skeletons" else 0,
                delta_ghoultokens=-cost if user.side != "skeletons" else 0,
            )

            user.build_times[structure_name] = (
                datetime.datetime.now() + datetime.timedelta(hours=1)
            )
            if structure_name == "barracks":
                user.structures["barracks"] += 1

            # Unlock special units based on specific structures
            if structure_name == "remote_meat_possessor" and user.side == "ghouls":
                user.unlocked_units.extend(["zombie giant", "beanglove"])
                await ctx.send(
                    "Remote Meat Possessor built! You can now create Zombie Giants and the legendary Beanglove."
                )

            elif structure_name == "treasure_tomb" and user.side == "skeletons":
                user.unlocked_units.append("brendan_fraser")
                await ctx.send(
                    "Treasure Tomb built! Brendan Fraser has joined your ranks with immense power. His aura can be felt for miles."
                )

            await ctx.send(f"{structure_name.capitalize()} will be built in 1 hour.")
        else:
            await ctx.send(f"Not enough coins to build {structure_name}.")

    async def buy_unit(self, ctx, user_id, unit_name):
        """
        Handles purchasing of units for a player, allowing only unlocked units.
        """
        user = self.state.users[user_id]
        side_units = SKELETON_UNITS if user.side == "skeletons" else GHOUL_UNITS
        resource = "bones" if user.side == "skeletons" else "cursed_meat"
        unit_cost = side_units[unit_name]["cost"]

        # Check if the unit is unlocked
        if unit_name not in user.unlocked_units:
            await ctx.send(
                f"{unit_name.capitalize()} is not available for purchase yet."
            )
            return

        max_units = user.structures["barracks"] * 10
        if user.get_unit_count() >= max_units:
            await ctx.send("You need more barracks to purchase additional units.")
            return

        if getattr(user, resource) >= unit_cost:
            await self.update_user(
                user_id,
                delta_bones=-unit_cost if resource == "bones" else 0,
                delta_cursed_meat=-unit_cost if resource == "cursed_meat" else 0,
            )

            if unit_name in user.units:
                user.units[unit_name]["quantity"] += 1
            else:
                user.units[unit_name] = {
                    "power": side_units[unit_name]["power"],
                    "quantity": 1,
                }
            await ctx.send(
                f"{unit_name.capitalize()} purchased! Remaining {resource}: {getattr(user, resource)}"
            )
        else:
            await ctx.send(
                f"Not enough {resource}. {unit_name.capitalize()} costs {unit_cost}."
            )

    @commands.command("battle")
    async def battle(self, ctx, target: discord.User):
        """
        Initiates a battle between the command issuer (attacker) and the target user (defender).
        """
        # Check if the target user is valid
        if target is None or not isinstance(target, discord.User):
            await ctx.send("Invalid target user!")
            return

        # Retrieve the attacker and defender user data from the state
        attacker = self.get_user(ctx.author.id)
        defender = self.get_user(target.id)

        # Ensure the attacker and defender are on opposing sides
        if attacker.side == defender.side:
            await ctx.send("You cannot battle your own side!")
            return

        # Determine if any special units are involved
        special_units = ["beanglove", "brendan fraser"]
        has_special_unit = any(
            unit in attacker.units or unit in defender.units for unit in special_units
        )

        # Load the appropriate outcome file based on the attacker's side
        outcome_file = (
            "battle_outcomes_skeleton.txt"
            if attacker.side == "skeletons"
            else "battle_outcomes_ghoul.txt"
        )
        outcome_messages = self.load_battle_outcomes(outcome_file)

        # Filter out messages containing special unit names if special units are present
        if has_special_unit:
            special_keywords = [
                unit.split()[0] for unit in special_units
            ]  # E.g., "bean" for "beanglove"
            outcome_messages = [
                msg
                for msg in outcome_messages
                if not any(keyword in msg.lower() for keyword in special_keywords)
            ]

        # If no suitable outcome messages are left, fall back to all messages
        if not outcome_messages:
            outcome_messages = self.load_battle_outcomes(outcome_file)

        # Perform battle calculations
        attack_roll = attacker.get_power_level() * random.uniform(0.8, 1.2)
        defend_roll = defender.get_power_level() * random.uniform(0.8, 1.2)
        outcome_message = random.choice(outcome_messages)

        # Send outcome message and determine winner
        if attack_roll > defend_roll:
            await self.battle_victory(ctx, attacker, defender, outcome_message)
        else:
            await self.battle_loss(ctx, attacker, defender, outcome_message)

    async def battle_victory(self, ctx, winner, loser, outcome_message):
        winnings = int(
            0.2 * (loser.ghoultokens if winner.side == "ghouls" else loser.skelecoin)
        )
        if winner.side == "ghouls":
            winner.ghoultokens += winnings
            loser.ghoultokens -= winnings
        else:
            winner.skelecoin += winnings
            loser.skelecoin -= winnings

        loser.structures[
            random.choice([k for k, v in loser.structures.items() if v])
        ] = False
        await ctx.send(
            f"{outcome_message} {winner.side.capitalize()} wins! Looted {winnings} from {loser.side.capitalize()}."
        )
        await self.record_battle(winner.side, loser.side, "Victory")

    async def battle_loss(self, ctx, loser, winner, outcome_message):
        """
        When the player loses an attack, 50% of their currency is transferred to the defender.
        """
        loss = int(
            0.5 * (loser.ghoultokens if loser.side == "ghouls" else loser.skelecoin)
        )
        if loser.side == "ghouls":
            loser.ghoultokens -= loss
            winner.ghoultokens += loss  # Add loss to the winner
        else:
            loser.skelecoin -= loss
            winner.skelecoin += loss  # Add loss to the winner
        await ctx.send(
            f"{outcome_message} {loser.side.capitalize()} loses the battle and forfeits {loss} currency to {winner.side.capitalize()}."
        )
        await self.record_battle(loser.side, winner.side, "Loss")


async def setup(bot):
    await bot.add_cog(SpookyMonth(bot))
