import aiohttp
import urllib.parse


class Formatter:
    def bold(self, string: str) -> str:
        return string

    def underline(self, string: str) -> str:
        return string

    def italics(self, string: str) -> str:
        return string

    def strike(self, string: str) -> str:
        return string

    def inline_code(self, string: str) -> str:
        return string

    def code_block(self, string: str, highlighting=None) -> str:
        return string

    def escape(self, string: str) -> str:
        return string


class DiscordFormatter(Formatter):
    format_chars = ["\\", "`", "*", "_", "~"]

    def bold(self, string: str) -> str:
        return "**{}**".format(string)

    def underline(self, string: str) -> str:
        return "__{}__".format(string)

    def italics(self, string: str) -> str:
        return "_{}_".format(string)

    def strike(self, string: str) -> str:
        return "~~{}~~".format(string)

    def inline_code(self, string: str) -> str:
        return "`{}`".format(string)

    def code_block(self, string: str, highlighting=None) -> str:
        if highlighting is not None:
            return "```{}\n{}\n```".format(highlighting, string)
        else:
            return "```\n{}\n```".format(string)

    def escape(self, string: str) -> str:
        for char in self.format_chars:
            string = string.replace(char, '\\' + char)
        return string


def update_query_string(parsed_url, qs):
    url_parts = list(parsed_url)
    query = dict(urllib.parse.parse_qsl(url_parts[4]))
    query.update(qs)

    url_parts[4] = urllib.parse.urlencode(query)

    return urllib.parse.urlunparse(url_parts)


class SearchProvider:
    formatter = None

    def __init__(self, formatter: Formatter):
        self.formatter = formatter

    async def search(self, string: str):
        async with aiohttp.ClientSession() as session:
            return await self.do_search(string, session)

    async def do_search(self, string: str, session: aiohttp.ClientSession):
        pass