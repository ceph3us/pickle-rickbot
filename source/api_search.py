import discord
from discord.ext import commands

# Hot reload search providers
from sys import modules

# Use list because otherwise we end up with a filtered comprehension
# which explodes when modules are destroyed
reload_mods = filter(lambda k: k.find('search_providers') != -1, list(modules.keys()))
for mod in reload_mods:
    del modules[mod]

from search_providers import MDNSearchProvider

MDN_COLOUR = 0x83d0f2


def format_defs(defs, indent_level=0):
    indents = ' ' * 8 * indent_level
    out_lines = []

    for name, item in defs.items():
        if item.get('values') is not None:
            item['text'] += '\n' + format_defs(item['values'], indent_level + 1)

        out_lines.append("{indent}`{name}`{opt} - {text}".format(
            indent=indents,
            name=name,
            text=item['text'],
            opt=' *(optional)*' if item.get('optional') else ''
        ))
    
    return '\n'.join(out_lines)


# ********************************************** #
# LANGUAGE API SEARCH COMMANDS ***************** #
# ********************************************** #


class APISearch:
    mdn = None

    def __init__(self, bot):
        self.bot = bot
        self.mdnsearch = MDNSearchProvider()

    @commands.command()
    async def mdn(self, *, search: str):
        search_result = await self.mdnsearch.search(search)
        if len(search_result) == 0:
            await self.bot.say("*buurp* I couldn't, er, find your dumb search results, Morty. Ain't there no more.")
        elif type(search_result) == dict:
            # await self.bot.say("*buurp* I couldn't, er, find your dumb search results, Morty. Ain't there no more.")
            docs = discord.Embed(
                type='rich',
                title=search_result['method'],
                url=search_result['url'],
                colour=MDN_COLOUR,
                author='MDN'
            )

            params = format_defs(search_result['params'])
            returns = format_defs(search_result['returns']) if type(search_result['returns']) == dict \
                else search_result['returns']

            docs.description = """
{summary}
            
***Parameters:***
{params}
            
***Returns:***
{returns}
            """.format(
                summary=search_result['description'],
                params=params if params else 'This function takes no parameters.',
                returns=returns if returns else 'This function does not return a value.')

            docs.set_author(name='MDN', url=self.mdnsearch.url_base)
            docs.set_footer(text='{} documentation on MDN'.format(search_result['type'].capitalize()),
                            icon_url="https://cdn.mdn.mozilla.net/static/img/favicon72.deefe20a0360.png")
            await self.bot.say('', embed=docs)


def setup(bot):
    bot.add_cog(APISearch(bot))
