import discord
from discord.ext import commands

class GPACog(commands.Cog):
    """
    Utility commands for calculating GPA to and from a percentage.

    Uses the equation from http://depts.washington.edu/lingta/grade_conversion.pdf
    or:

    if > 95% GPA = 4
    if < 62% GPA = 0
    else % * 0.1 - 5.5

    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def to_points(self, ctx, score):
        """
        Converts the given percentage [0-100] to a GPA value.
        :param score:
        :return:
        """

        x = standardize_input(score)
        gpa = percentage_to_gpa(x)

        await ctx.send(f'{x}% ≈ {gpa:.2f} points')

    @commands.command()
    async def to_percent(self, ctx, score: float):
        """
        Converts the given score [0.0-4.0] to an estimated percentage.
        :param ctx:
        :param score:
        :return:
        """
        await ctx.send(f'{score:.2f} points ≈ {points_to_percent(score)}')

def points_to_percent(points) -> str:
    """
    Converts a point value to a percentage value.

    >>> points_to_percent(4.0)
    '≥95%'

    >>> points_to_percent(0.0)
    '≤65%'

    >>> points_to_percent(3.5)
    '90.0%'

    :param points:
    :return:
    """
    if points <= 0.0:
        return '≤65%'
    if points >= 4.0:
        return '≥95%'

    percent = points * 10 + 55
    return f'{percent:.1f}%'


def standardize_input(score):
    """
    Converts the score input of either a str, int, or float into the desired
    input for percentage_to_gpa.

    I don't care about some being int and some being float, still works all the same.

    >>> standardize_input('95%')
    95.0

    >>> standardize_input(95)
    95

    >>> standardize_input(0.95)
    95.0

    >>> standardize_input('0.60%')
    60.0

    >>> standardize_input(0.6)
    60.0

    >>> standardize_input(66)
    66

    :param score:
    :return:
    """
    # if the input was a str, remove any % and convert it into a float
    if isinstance(score, str):
        score = score.replace('%', '')
        score = float(score)

    # if the user used the wrong type of percentage
    if 0 <= score <= 1:
        # fix it for them
        score *= 100

    return score

def percentage_to_gpa(score: float) -> float:
    """
    Converts a float [0-100] percentage value into a GPA score [0-4]

    >>> percentage_to_gpa(100.0)
    4.0

    >>> percentage_to_gpa(95.01)
    4.0

    >>> percentage_to_gpa(65)
    0.0

    >>> percentage_to_gpa(90)
    3.5

    :param score:
    :return:
    """
    if score >= 95:
        return 4.0
    if score <= 65:
        return 0.0
    return (score * 0.1) - 5.5


def setup(bot):
    bot.add_cog(GPACog(bot))

# optional, but helpful for testing via the shell
if __name__ == '__main__':
    import doctest
    doctest.testmod()
