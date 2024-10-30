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
BASE_POWER_CAP = 1000  # Starting power cap
BARRACKS_POWER_INCREMENT = 500  # Additional cap per barracks
STRUCTURE_COSTS = {
    "command_center": 1000,
    "refinery": 500,
    "graveyard": 750,
    "watchtower": 300,
    "barracks": 800,
    "remote_flesh_possessor": 10000,  # High cost for ghouls
}
SKELETON_STRUCTURE_COSTS = {
    "command_center": 3000,  # 1000 * 3
    "refinery": 1500,  # 500 * 3
    "graveyard": 2250,  # 750 * 3
    "watchtower": 900,  # 300 * 3
    "barracks": 2400,  # 800 * 3
    "legendary_tomb": 100000,  # High cost for skeletons
}

WATCHTOWER_POWER_BOOST = 0.01  # Boost percentage for army power level

# Define units, including secret units, but make them inaccessible initially
GHOUL_UNITS = {
    "ghouls": {"power": 10, "cost": 20},
    "wraiths": {"power": 20, "cost": 50},
    "ghosts": {"power": 30, "cost": 75},
    "zombies": {"power": 40, "cost": 100},
    "giant_ghoul": {"power": 100, "cost": 300},
    "zombie_giant": {"power": 500, "cost": 1000},  # Secret unit, initially locked
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
            "command_center": True,
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

    def get_power_level(self):
        total_power = sum(
            details["power"] * details["quantity"] for details in self.units.values()
        )

        # Calculate the current power cap based on barracks count
        power_cap = (
            BASE_POWER_CAP
            + self.structures.get("barracks", 0) * BARRACKS_POWER_INCREMENT
        )

        # Apply the power cap
        effective_power = min(total_power, power_cap)

        # Apply watchtower boost if available
        if self.structures.get("watchtower"):
            effective_power *= 1 + WATCHTOWER_POWER_BOOST

        return int(effective_power)

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
        user = self.state.users.get(user_id)
        if not user:
            return

        graveyard_count = user.structures.get("graveyard", 0)
        refinery_count = user.structures.get(
            "refinery", 0
        )  # Track the number of refineries
        now = time.time()
        time_elapsed_minutes = (
            now - user.last_interaction
        ) / 60  # Convert seconds to minutes

        # Graveyard output calculation
        if graveyard_count > 0:
            base_output_rate = 2  # Increased base output rate
            if user.side == "skeletons":
                bonemeal_gained = round(
                    graveyard_count * base_output_rate * time_elapsed_minutes, 3
                )
                await self.update_user(user_id, delta_bonemeal=bonemeal_gained)
            else:
                ectoplasm_gained = round(
                    graveyard_count * base_output_rate * time_elapsed_minutes, 3
                )
                await self.update_user(user_id, delta_ectoplasm=ectoplasm_gained)

        # Refinery processing rate with multiple refineries
        if refinery_count > 0:
            base_refinery_rate = 10  # Base rate for each refinery (adjust as needed)
            total_refining_rate = refinery_count * base_refinery_rate

            if user.side == "skeletons":
                converted_bonemeal = int(
                    min(user.bonemeal, total_refining_rate * time_elapsed_minutes)
                )
                await self.update_user(
                    user_id,
                    delta_bonemeal=-converted_bonemeal,
                    delta_bones=converted_bonemeal,
                )
            else:
                converted_ecto = int(
                    min(user.ectoplasm, total_refining_rate * time_elapsed_minutes)
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
                    self.state = State.from_json(s.read())
                    actual_state = {}
                    for k, v in self.state.users.items():
                        user_id = int(k)
                        # Initialize User with all attributes from the loaded data
                        actual_state[user_id] = User(
                            ghoultokens=v.get("ghoultokens", 0),
                            skelecoin=v.get("skelecoin", 0),
                            bonemeal=v.get("bonemeal", 0),
                            bones=v.get("bones", 0),
                            ectoplasm=v.get("ectoplasm", 0),
                            cursed_meat=v.get("cursed_meat", 0),
                            side=v.get("side", ""),  # Ensure 'side' is restored
                            structures=v.get("structures", {}),
                            units=v.get("units", {}),
                            unlocked_units=v.get("unlocked_units", []),
                            mummy_parts=v.get("mummy_parts", 0),
                            build_times=v.get("build_times", {}),
                            last_interaction=v.get("last_interaction", time.time()),
                            last_barracks_built=v.get("last_barracks_built", None),
                        )
                    self.state.users = actual_state
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
        this piece of sh***
        """
        if message.guild is None or message.author.bot:
            return

        if message.content.startswith(">>"):  ## incrementing for no reason
            return

        if message.content.startswith(self.bot.command_prefix):
            return

        # Ignore messages sent by bots
        if message.author.bot:
            return

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
        # print("Incrementing ghoul tokens!" + str(increment))
        await self.update_user(user_id, delta_ghoultokens=increment)

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

    async def handle_loss(self, user_id):
        """Handles player loss by resetting their stats and notifying them."""
        user = self.state.users.get(user_id)
        if not user:
            return

        # Reset all stats
        user.skelecoin = 0
        user.ghoultokens = 0
        user.bonemeal = 0
        user.bones = 0
        user.ectoplasm = 0
        user.cursed_flesh = 0
        user.structures = {  # Reset structures
            "command_center": False,
            "refinery": 0,
            "graveyard": 0,
            "watchtower": False,
            "barracks": 0,
        }
        user.units = {}  # Clear units
        user.unlocked_units = []
        user.mummy_parts = 0

        await self.write_state()  # Save the reset state

        # Send a loss message
        await self.bot.get_user(user_id).send(
            "You've lost your command center and thus the game! All your stats have been reset, and you need to restart to continue."
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
        Shows a list of all available player bases, with a dynamic 'danger level' based on the user's own power level.
        """
        # Get the command issuer's power level and side
        user_id = ctx.author.id
        user = self.state.users.get(user_id)

        if not user:
            await ctx.send(
                "Please join a side first by using `>>join_skeletons` or `>>join_ghouls`."
            )
            return

        user_power_level = user.get_power_level()
        user_side = user.side  # Get the command user's side

        base_list = "**Available Bases:**\n"

        for other_user_id, other_user in self.state.users.items():
            if other_user_id == user_id:
                continue  # Skip the user's own base

            other_power_level = other_user.get_power_level()
            power_difference = other_power_level - user_power_level
            member = ctx.guild.get_member(other_user_id)
            display_name = member.display_name if member else "Unknown User"

            # Define dynamic danger level based on power difference
            if power_difference > 500:
                danger_level = "High"
            elif power_difference > 0:
                danger_level = "Medium"
            else:
                danger_level = "Low"

            # Mark enemy bases with a warning symbol and distinguish them from allies
            if other_user.side == user_side:
                base_list += (
                    f"🛡️ Ally: `{display_name}` - Danger Level: {danger_level}\n"
                )
            else:
                base_list += (
                    f"⚔️ Enemy: `{display_name}` - Danger Level: {danger_level}\n"
                )

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

        This command shows a player's current base structures, separating built structures from
        those available for construction. It provides an overview of the player's resources,
        current currency levels, and resource generation rates if graveyards and refineries are built.
        """
        user_id = ctx.author.id
        user = self.state.users.get(user_id)

        await self.update_resources_since_last_interaction(
            user_id
        )  # update user resource state
        if not user:
            await ctx.send(
                "You have not joined a side yet! Use `>>join_ghouls` or `>>join_skeletons` to get started."
            )
            return

        # Check if the user has joined a side
        if not user.side:
            await ctx.send(
                "Please join a side first by using `>>join_skeletons` or `>>join_ghouls`."
            )
            return

        # Determine currency and costs based on side
        currency = "ghoul tokens" if user.side == "ghouls" else "skelecoin"
        currency_amount = user.ghoultokens if user.side == "ghouls" else user.skelecoin
        structure_costs = (
            SKELETON_STRUCTURE_COSTS if user.side == "skeletons" else STRUCTURE_COSTS
        )

        # Prepare display sections
        built_structures = "**Built:**\n"
        available_structures = "\n**Available to build:**\n"

        # Get the special structure name based on side
        special_structure = (
            "legendary_tomb" if user.side == "skeletons" else "remote_flesh_possessor"
        )

        # Process all structures including special structures
        for name, cost in structure_costs.items():
            built = user.structures.get(name, False)

            # Add to built structures if it exists
            if built:
                if isinstance(built, bool):
                    built_structures += f"{name} x1\n"
                else:
                    built_structures += f"{name} x{built}\n"

            # Skip structures that can only be built once if already built
            if name in ["command_center", "refinery"] and built:
                continue

            # Add to available structures if not built or can build multiple
            if not built or isinstance(built, int):
                available_structures += f"{name}: "
                available_structures += "Built" if built else "Not built"
                cost_text = f" (Cost: {cost} {currency}"
                cost_text += " each)" if isinstance(built, int) else ")"
                available_structures += cost_text + "\n"

        # Calculate resource generation rates if structures are built
        graveyard_count = user.structures.get("graveyard", 0)
        refinery_built = user.structures.get("refinery", False)

        # Display current resources with generation rates
        resources_info = f"\n**Resources:**"
        if user.side == "skeletons":
            bonemeal_rate = round(
                graveyard_count / 60, 3
            )  # Rate for bonemeal generation per second
            bones_rate = (
                round((graveyard_count * 0.5) / 60, 3) if refinery_built else 0
            )  # Rate if refinery is built
            resources_info += (
                f"\nBonemeal: {user.bonemeal:.3f} (+{bonemeal_rate:.3f}/s)"
                f"\nBones: {user.bones:.3f} (+{bones_rate:.3f}/s)"
            )
        else:
            ectoplasm_rate = round(
                graveyard_count / 60, 3
            )  # Rate for ectoplasm generation per second
            cursed_meat_rate = (
                round((graveyard_count * 0.5) / 60, 3) if refinery_built else 0
            )  # Rate if refinery is built
            resources_info += (
                f"\nEctoplasm: {user.ectoplasm:.3f} (+{ectoplasm_rate:.3f}/s)"
                f"\nCursed Meat: {user.cursed_meat:.3f} (+{cursed_meat_rate:.3f}/s)"
            )

        # Display current currency at the bottom in bold
        currency_info = (
            f"\n\n**Your current {currency.capitalize()}: {currency_amount}**"
        )

        # Construct and send the full message
        full_message = (
            "_Use the `>>build` command to buy a structure_\n\n"
            + built_structures
            + available_structures
            + resources_info
            + currency_info
        )

        await ctx.send(full_message)

    @commands.command("build")
    async def build(self, ctx, structure_name: str = None, quantity: int = 1):
        """
        Build one or more instances of a structure for your base.
        Specify the structure name and the quantity (default is 1).
        """
        if not structure_name:
            await ctx.send("Please specify a structure to build.")
            return

        # Ensure quantity is a positive number
        if quantity <= 0:
            await ctx.send("You need to buy at least one of a structure!")
            return

        user_id = ctx.author.id
        user = self.state.users.get(user_id)

        await self.update_resources_since_last_interaction(user_id)  # Update resources

        if not user or not user.side:
            await ctx.send("You need to join a side first!")
            return

        structure_costs = (
            SKELETON_STRUCTURE_COSTS if user.side == "skeletons" else STRUCTURE_COSTS
        )
        structure_name = structure_name.lower().replace(" ", "_")

        if structure_name not in structure_costs:
            await ctx.send(f"{structure_name} is not a valid structure.")
            return

        cost_per_structure = structure_costs[structure_name]
        total_cost = cost_per_structure * quantity
        currency = "skelecoin" if user.side == "skeletons" else "ghoul tokens"
        user_currency = user.skelecoin if user.side == "skeletons" else user.ghoultokens

        # Check if the player has enough currency
        if user_currency < total_cost:
            await ctx.send(
                f"You don't have enough {currency} to build {quantity} {structure_name}(s)!"
            )
            return

        # Check for single-instance structures and restrict to one purchase
        if structure_name in [
            "command_center",
            "legendary_tomb",
            "remote_flesh_possessor",
        ]:
            if user.structures.get(structure_name, False):
                await ctx.send(
                    f"You have already built a {structure_name} and can only have one!"
                )
                return
            quantity = 1  # Override to a single purchase for unique structures

        # Deduct the total cost and update the currency
        if user.side == "skeletons":
            user.skelecoin -= total_cost
        else:
            user.ghoultokens -= total_cost

        # Update the structure count for buildings that can have multiple instances
        if structure_name == "barracks":
            # Increase the barracks count and power cap by the specified quantity
            current_barracks = user.structures.get("barracks", 0)
            user.structures["barracks"] = current_barracks + quantity
        elif structure_name in ["refinery", "graveyard", "watchtower"]:
            # Update count for other multi-instance buildings
            current_count = user.structures.get(structure_name, 0)
            if isinstance(current_count, bool):
                current_count = 1 if current_count else 0
            user.structures[structure_name] = current_count + quantity
        else:
            # Single-instance structures are just marked as True
            user.structures[structure_name] = True

        await ctx.send(
            f"Successfully built {quantity} {structure_name}(s) for {total_cost} {currency}."
        )
        await self.write_state()  # Save the updated state

    @commands.command("units")
    async def units(self, ctx):
        user = await self.get_user(ctx.author.id)
        if not user or not user.side:
            await ctx.send(
                "Please join a side first using `>>join_skeletons` or `>>join_ghouls`."
            )
            return

        side_units = SKELETON_UNITS if user.side == "skeletons" else GHOUL_UNITS
        units_info = f"**{ctx.author.display_name}'s Units:**\n"

        # List current units
        for unit, details in user.units.items():
            units_info += f"`{unit.capitalize()} - Power: {details['power']}, Quantity: {details['quantity']}`\n"

        total_power = user.get_power_level()
        power_cap = (
            BASE_POWER_CAP
            + user.structures.get("barracks", 0) * BARRACKS_POWER_INCREMENT
        )

        # Scaled watchtower multiplier based on count
        watchtower_count = user.structures.get("watchtower", 0)
        watchtower_multiplier = (
            (1 + WATCHTOWER_POWER_BOOST) ** watchtower_count
            if watchtower_count > 0
            else 1
        )
        additional_power_bonus = int(total_power * (watchtower_multiplier - 1))

        # Display power level, cap, and watchtower effect
        units_info += f"```\nTotal Power Level: {total_power}/{power_cap} (Power Cap)\n"
        if watchtower_count > 0:
            units_info += f"Watchtower Multiplier (x{watchtower_count}): x{watchtower_multiplier:.2f}\n"
            units_info += f"Additional Power Bonus from Watchtowers: +{additional_power_bonus}\n\n```"

        # List available units for purchase with Remote Flesh Possessor requirement
        units_info += "\n**Available Units for Purchase:**\n"
        for unit, details in side_units.items():
            if unit == "mummy" and user.mummy_parts < len(MUMMY_PARTS_SEQUENCE):
                continue
            if unit in [
                "beanglove",
                "giant ghoul",
                "zombie giant",
            ] and not user.structures.get("remote_flesh_possessor", False):
                continue

            units_info += f"{unit.capitalize()} - Power: {details['power']}, Cost: {details['cost']}\n"

        if user.side == "skeletons":
            mummy_info = f"\nMummy Parts Collected: {user.mummy_parts}/{len(MUMMY_PARTS_SEQUENCE)}"
            units_info += mummy_info

        await ctx.send(units_info)

    # Define methods to check secret conditions
    def brendan_fraser_conditions_met(self, user):
        # Check for the Legendary Tomb, mummy presence, and sufficient funds for Brendan Fraser
        has_legendary_tomb = user.structures.get("legendary_tomb", False)
        has_mummy = user.units.get("mummy", {}).get("quantity", 0) >= 1
        return has_legendary_tomb and has_mummy

    def beanglove_conditions_met(self, user):
        # Check for the Remote Flesh Possessor and power level requirement for Beanglove
        has_remote_flesh_possessor = user.structures.get(
            "remote_flesh_possessor", False
        )
        sufficient_power_level = user.get_power_level() >= 1500
        return has_remote_flesh_possessor and sufficient_power_level

    @commands.command("buy")
    async def buy(self, ctx, unit_name: str = None, quantity: int = 1):
        """Allows users to buy units or parts for their side, with power cap enforcement and special messages cycling."""
        if not unit_name:
            await ctx.send("Please specify a unit to buy.")
            return

        user_id = ctx.author.id
        user = self.state.users.get(user_id)

        await self.update_resources_since_last_interaction(
            user_id
        )  # Update resource state

        if not user or not user.side:
            await ctx.send("Please join a side first!")
            return

        # Determine available units and currency based on the user's side
        side_units = SKELETON_UNITS if user.side == "skeletons" else GHOUL_UNITS
        currency = "bones" if user.side == "skeletons" else "cursed_meat"
        user_currency = getattr(user, currency)

        # Restrict special units based on structures
        if unit_name in [
            "beanglove",
            "giant ghoul",
            "zombie giant",
        ] and not user.structures.get("remote_flesh_possessor", False):
            await ctx.send(
                "You need to build the Remote Flesh Possessor to purchase this unit."
            )
            return

        # Special messages for Brendan Fraser and Beanglove, cycle through the list
        special_messages = {
            "beanglove": [
                "The beans flow, coating every surface in sight, from the nightmare rises a glove, satin white and filled with horrors beyond description.",
                "The beans are now oceans. The skies are brown, and the ghouls gorge upon the unearthly blight.",
                "Beans are the beginning.",
                "We won't need eyes where we're going...",
            ],
            "brendan_fraser": [
                "A true adventurer can't resist a tomb filled with mummies. The man, the myth, the 1999 cinematic masterpiece, *The Mummy*, with Brendan Fraser and Rachel Weisz.",
                "The 1999 cinematic masterpiece, *The Mummy*, with Brendan Fraser and Rachel Weisz. The 1999 cinematic masterpiece, *The Mummy*, with Brendan Fraser and Rachel Weisz. Oh no OH NO.",
                "WHY ARE THERE SO MANY BRENDAN FRASERS!",
                "They come running across the hills, countless of them. All identical. All Brendan Fraser.",
            ],
        }

        # Handle special cases for Brendan Fraser and Beanglove purchases
        if unit_name in ["beanglove", "brendan_fraser"]:
            if unit_name == "beanglove" and not self.beanglove_conditions_met(user):
                await ctx.send("You haven't met the conditions to purchase Beanglove.")
                return
            elif (
                unit_name == "brendan_fraser"
                and not self.brendan_fraser_conditions_met(user)
            ):
                await ctx.send(
                    "You haven't met the conditions to purchase Brendan Fraser."
                )
                return

            # Check power cap enforcement for special units
            additional_power = side_units[unit_name]["power"] * quantity
            power_cap = (
                BASE_POWER_CAP
                + user.structures.get("barracks", 0) * BARRACKS_POWER_INCREMENT
            )
            current_power = user.get_power_level()

            if current_power + additional_power > power_cap:
                await ctx.send(
                    f"Purchase exceeds your current power cap of {power_cap}. Build more barracks to increase your cap."
                )
                return

            # Deduct the cost and update user units
            total_cost = side_units[unit_name]["cost"] * quantity
            if user_currency < total_cost:
                await ctx.send(
                    f"You don't have enough {currency} to buy {quantity} {unit_name}(s)."
                )
                return

            setattr(user, currency, user_currency - total_cost)
            if unit_name in user.units:
                user.units[unit_name]["quantity"] += quantity
                message_index = user.units[unit_name]["quantity"] % len(
                    special_messages[unit_name]
                )
            else:
                user.units[unit_name] = {
                    "power": side_units[unit_name]["power"],
                    "quantity": quantity,
                }
                message_index = 0

            await ctx.send(special_messages[unit_name][message_index])
            await self.write_state()
            return

        # Standard unit purchase logic with power cap check
        unit_name = unit_name.lower()
        unit_details = side_units.get(unit_name)
        if not unit_details:
            await ctx.send(
                f"{unit_name.capitalize()} is not a valid unit for your side."
            )
            return

        total_cost = unit_details["cost"] * quantity
        additional_power = unit_details["power"] * quantity
        power_cap = (
            BASE_POWER_CAP
            + user.structures.get("barracks", 0) * BARRACKS_POWER_INCREMENT
        )
        current_power = user.get_power_level()

        # Check if the purchase would exceed the player's power cap
        if current_power + additional_power > power_cap:
            await ctx.send(
                f"Purchase exceeds your current power cap of {power_cap}. Build more barracks to increase your cap."
            )
            return

        # Check if the player has enough currency
        if user_currency < total_cost:
            await ctx.send(
                f"You don't have enough {currency} to buy {quantity} {unit_name}(s)!"
            )
            return

        # Deduct the cost and update the user's units
        setattr(user, currency, user_currency - total_cost)
        if unit_name in user.units:
            user.units[unit_name]["quantity"] += quantity
        else:
            user.units[unit_name] = {
                "power": unit_details["power"],
                "quantity": quantity,
            }

        await ctx.send(
            f"Successfully bought {quantity} {unit_name}(s) for {total_cost} {currency}."
        )
        await self.write_state()

    async def battle(self, ctx, target: discord.User):
        """
        Initiates a battle between the command issuer (attacker) and the target user (defender).
        Displays power levels, calculates losses based on power difference, and shows what units and buildings were lost.
        """
        if target is None or not isinstance(target, discord.User):
            await ctx.send("Invalid target user!")
            return

        # Retrieve attacker and defender
        attacker = await self.get_user(ctx.author.id)
        defender = await self.get_user(target.id)

        # Ensure they are on opposing sides
        if attacker.side == defender.side:
            await ctx.send("You cannot battle your own side!")
            return

        # Display initial power levels
        attacker_power = attacker.get_power_level()
        defender_power = defender.get_power_level()
        await ctx.send(
            f"**Battle Initiated!**\n{ctx.author.display_name} (Power: {attacker_power}) vs. {target.display_name} (Power: {defender_power})"
        )

        # Determine the power level difference
        power_diff = abs(attacker_power - defender_power)
        loss_multiplier = 1 + (power_diff / max(attacker_power, defender_power))

        # Determine units lost based on power difference, prioritizing weaker units
        async def calculate_losses(user, loss_multiplier):
            lost_units = {}
            remaining_units = {}

            sorted_units = sorted(
                user.units.items(), key=lambda x: x[1]["power"]
            )  # Sort units by power, weakest first

            for unit, details in sorted_units:
                quantity = details["quantity"]
                loss_count = min(
                    quantity, int(quantity * loss_multiplier / 2)
                )  # Scale losses by power difference
                remaining_quantity = quantity - loss_count

                if loss_count > 0:
                    lost_units[unit] = loss_count
                if remaining_quantity > 0:
                    remaining_units[unit] = {
                        "power": details["power"],
                        "quantity": remaining_quantity,
                    }

            return lost_units, remaining_units

        # Calculate and apply losses for both players
        attacker_lost_units, attacker.remaining_units = await calculate_losses(
            attacker, loss_multiplier if attacker_power < defender_power else 1
        )
        defender_lost_units, defender.remaining_units = await calculate_losses(
            defender, loss_multiplier if defender_power < attacker_power else 1
        )

        # Select a building to be lost if applicable
        def calculate_building_loss(user):
            damaged_building = None
            if any(user.structures.values()):
                damaged_building = random.choice(
                    [k for k, v in user.structures.items() if v]
                )
                if (
                    isinstance(user.structures[damaged_building], int)
                    and user.structures[damaged_building] > 1
                ):
                    user.structures[damaged_building] -= 1
                else:
                    user.structures[damaged_building] = False
            return damaged_building

        attacker_building_lost = calculate_building_loss(attacker)
        defender_building_lost = calculate_building_loss(defender)

        # Display losses
        def format_losses(lost_units, building_lost):
            loss_message = ""
            if lost_units:
                unit_losses = ", ".join(
                    [f"{unit} x{count}" for unit, count in lost_units.items()]
                )
                loss_message += f"Units Lost: {unit_losses}\n"
            if building_lost:
                loss_message += f"Building Lost: {building_lost}"
            return loss_message or "No significant losses."

        await ctx.send(
            f"**Battle Outcome:**\n"
            f"{ctx.author.display_name}:\n{format_losses(attacker_lost_units, attacker_building_lost)}\n"
            f"{target.display_name}:\n{format_losses(defender_lost_units, defender_building_lost)}"
        )

        # Update the state with remaining units
        attacker.units = attacker.remaining_units
        defender.units = defender.remaining_units
        await self.write_state()

    async def battle_victory(self, ctx, winner, loser, outcome_message):
        winnings = int(
            0.2 * (loser.ghoultokens if winner.side == "ghouls" else loser.skelecoin)
        )
        currency_name = "ghoul tokens" if winner.side == "ghouls" else "skelecoin"

        # Update winner and loser currency
        if winner.side == "ghouls":
            winner.ghoultokens += winnings
            loser.ghoultokens -= winnings
        else:
            winner.skelecoin += winnings
            loser.skelecoin -= winnings

        # Select a random structure to "damage"
        structure_to_damage = random.choice(
            [k for k, v in loser.structures.items() if v]
        )
        if (
            isinstance(loser.structures[structure_to_damage], int)
            and loser.structures[structure_to_damage] > 1
        ):
            # Calculate a multiplier-based removal
            max_removal = max(1, loser.structures[structure_to_damage] // 2)
            removal_count = random.randint(1, max_removal)

            # Ensure the count doesn’t go below zero
            loser.structures[structure_to_damage] = max(
                0, loser.structures[structure_to_damage] - removal_count
            )

            # If structure count drops to zero, reset to `False`
            if loser.structures[structure_to_damage] == 0:
                loser.structures[structure_to_damage] = False
        else:
            # Set to False for single-instance structures
            loser.structures[structure_to_damage] = False

        # Send the victory message with the correct currency label
        await ctx.send(
            f"{outcome_message} {winner.side.capitalize()} wins! Looted {winnings} {currency_name} from {loser.side.capitalize()}."
        )
        await self.record_battle(winner.side, loser.side, "Victory")

    async def battle_loss(self, ctx, loser, winner, outcome_message):
        user_id = ctx.author.id
        await self.update_resources_since_last_interaction(user_id)  # update resources
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
