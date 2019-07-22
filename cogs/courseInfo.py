import discord
from discord.ext import commands

import configparser
import json
import re
from pprint import pprint
from bs4 import BeautifulSoup # html parser
import pandas

# course info module

# this parses though the data that is returned from the endpoint
# https://myplan.uw.edu/course/api/courses
# this returned result is saved and parsed though

# this also parses through the course information page
# that is downloaded locally from
# http://www.washington.edu/students/crscatb/css.html

# course info related commands
class CourseInfo(commands.Cog):

    def __init__(self, bot):
        # open the config file in the parent directory
        config = configparser.ConfigParser()
        with open('config.ini') as config_file:
            config.read_file(config_file)

        # sets the reference to the bot
        self.bot = bot

        # set the course data to be empty by default
        self.course_data = {}

        # ensure that the course info was supplied
        if config.has_option(section='Configuration', option='course_data_file_path'):
            # also loads the contents of the file
            courseInfoFile = config.get(section='Configuration', option='course_data_file_path')
            with open(courseInfoFile) as course_info:
                self.course_data = json.load(course_info)
        else:
            print('no course data file was supplied')

        # set the course descriptions to be empty by default
        self.course_descriptions = {}

        if config.has_option(section='Configuration', option='course_description_file_path'):
            course_description_file_path = config.get(section='Configuration', option='course_description_file_path')
            with open(course_description_file_path) as course_description_file:
                self.course_descriptions = BeautifulSoup(course_description_file, 'html.parser')
        else:
            print('no course description file was supplied')

    # get course data commands
    # course codes must be in the format
    # CSS XXX
    # validation of this should come down the line
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.command()
    async def course(self, ctx, *, course_code='No course'):

        course_embed = discord.Embed()

        # search for a matching course
        match = list(filter(lambda c: c['code'] == course_code, self.course_data))

        if not match:
            await ctx.send(f'I couldn\'t find a class by the code "{course_code}". Try searching again'
                           + f'in the format `CSS 101`. ')
            return
        else:
            course_embed.title = f'{match[0]["code"]} Course Information'

            # setup the title field
            title_field = f'{match[0]["title"]} ({match[0]["credit"]}) '

            # add all genEduReq items
            for req in match[0]['genEduReqs']:
                title_field += f'{req} '
            course_embed.add_field(name='Title', value=title_field, inline=True)

            # set up the time field
            time_field = f'{_int_time_to_str(match[0]["startTime"])} - {_int_time_to_str(match[0]["endTime"])} '

            for day in match[0]['meetingDays']:
                time_field += f'{_meeting_day_to_day(day)} '

            course_embed.add_field(name='Time', value=time_field, inline=True)

            # set the color to the CSSBot Green
            course_embed.color = discord.Colour(0xbdcf46)

        # convert the input string to lower and remove spaces so we can parse html
        course_code_html = course_code.lower().replace(' ', '')

        # find the element for the course code
        collection = self.course_descriptions.select(f'a[name="{course_code_html}"] > p')

        # find the a tag with the name of the course code
        # that also contains data
        for element in collection:
            # check if element has contents
            if element.contents:
                # get the element that contains the description (hard coded)
                # and add the link to view course details in MyPlan
                description=f'{element.contents[2]}\n[{element.contents[4].string}]({element.contents[4].get("href")})'
                course_embed.add_field(name='Description', value=description)
        await ctx.send(embed=course_embed)


def _int_time_to_str(integer_time):
    """
    Converts an integer time supplied from the course info JSON into a
    cleaner looking string representation.

    >>> _int_time_to_str(845)
    '8:45 AM'

    >>> _int_time_to_str(1045)
    '10:45 AM'

    >>> _int_time_to_str(1245)
    '12:45 PM'

    >>> _int_time_to_str(1345)
    '1:45 PM'

    >>> _int_time_to_str(0)
    'N/A'

    :param integer_time:
    :return:
    """
    if integer_time == 0:
        return 'N/A'
    try:
        return pandas.to_datetime(integer_time, format='%H%M').strftime('%-I:%M %p')
    except ValueError:
        return 'N/A'


def _meeting_day_to_day(day):
    """
    Converts a string containing an integer number representing a day of the week
    into a string that contains the value for that day of the week

    Only does business weekdays

    DocTest

    >>> _meeting_day_to_day('-1')
    ''
    >>> _meeting_day_to_day('1')
    'M'
    >>> _meeting_day_to_day('2')
    'T'
    >>> _meeting_day_to_day('3')
    'W'
    >>> _meeting_day_to_day('4')
    'Th'
    >>> _meeting_day_to_day('5')
    'F'
    >>> _meeting_day_to_day('6')
    'Sat'
    >>> _meeting_day_to_day('7')
    ''

    :param day:
    :return:
    """
    if day == '1':
        return 'M'
    elif day == '2':
        return 'T'
    elif day == '3':
        return 'W'
    elif day == '4':
        return 'Th'
    elif day == '5':
        return 'F'
    elif day == '6':
        return 'Sat'
    return ''

def setup(bot):
    bot.add_cog(CourseInfo(bot))

if __name__ == '__main__':
    import doctest
    doctest.testmod()