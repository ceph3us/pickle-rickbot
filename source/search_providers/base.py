import aiohttp
import urllib.parse


class SearchProvider:
    async def search(self, string: str):
        async with aiohttp.ClientSession() as session:
            return await self.do_search(string, session)

    async def do_search(self, string: str, session: aiohttp.ClientSession):
        pass


def update_query_string(parsed_url, qs):
    url_parts = list(parsed_url)
    query = dict(urllib.parse.parse_qsl(url_parts[4]))
    query.update(qs)

    url_parts[4] = urllib.parse.urlencode(query)

    return urllib.parse.urlunparse(url_parts)

