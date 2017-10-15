from urllib.parse import urlparse
import json
import re

import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString

from .base import SearchProvider, update_query_string


class MDNPageParseException(Exception):
    pass


def upperfirst(x):
    return x[0].upper() + x[1:] if len(x) > 0 else x

def lowerfirst(x):
    return x[0].lower() + x[1:] if len(x) > 0 else x


def _is_same_method(string: str):
    has_paren = string.endswith('()')
    matches = []

    # Normalize parens
    if not has_paren:
        string += '()'

    # Search also for method calls ('.prototype.') if not specified
    parts = string.split('.')
    if len(parts) == 2:
        alt_parts = [parts[0], 'prototype', parts[1]]
        final = ".".join(alt_parts)
        matches.append(lowerfirst(final))
        matches.append(upperfirst(final))

    matches.append(lowerfirst(string))
    matches.append(upperfirst(string))

    return lambda result: result['title'] in matches \
                          and 'Reference' in result['tags'] \
                          and 'Method' in result['tags']


def match_method(string: str, results: dict):
    return list(filter(_is_same_method(string), results['documents']))


def parse_section_recursive(element):
    # Maintain list of section changes
    remove = []
    update = {}
    values = dict(zip(
        map(lambda dt: dt.find('code').string, element.find_all('dt', recursive=False)),
        element.find_all('dd', recursive=False)))
    for k, v in values.items():
        sub_list = v.find('dl')
        if sub_list is not None:
            values[k] = {
                'text': ' '.join([s for s in v.children if type(s) == NavigableString]).strip(),
                'values': parse_section_recursive(sub_list)
            }
        else:
            values[k] = {'text': ''.join([str(s) for s in v.children])}

        values[k]['text'] = replace_mdn_formatting(values[k]['text'])

        if k.find('{{Optional_inline}}') != -1:
            values[k]['optional'] = True
            new_k = k.replace('{{Optional_inline}}', '').strip()
            update[new_k] = values[k]
            remove.append(k)

    for k in remove:
        del values[k]

    for k, v in update.items():
        values[k] = v

    return values


def replace_mdn_formatting(string):
    string = re.sub(r"<code>(<strong>)?(.+?)(</strong>)?</code>", r"`\2`", string)
    string = re.sub(r"<code>(<strong>)?(.+?)(</strong>)?</code>", r"`\2`", string)
    string = re.sub(r"<a(.*?)>(.*?)</a>", r"\2", string)
    string = re.sub(r"({{)?\W*?(.+)xref\(\"(.+?)\"\)\W*?(}})?", r"`\3`", string)
    string = re.sub(r"({{)?\W*?Glossary\(\"(.+?)\"\)\W*?(}})?", r"*\2*", string)

    return string


class MDNSearchProvider(SearchProvider):
    url_base = 'https://developer.mozilla.org/en-US/'

    _search_suffix = 'search.json'
    _count = 5

    search_url = None

    def __init__(self, base_url_override=''):
        if base_url_override != '':
            self.url_base = base_url_override

        self.search_url = urlparse(self.url_base + self._search_suffix)

    @staticmethod
    def parse_method_info(document):
        method_info = {}
        dom = BeautifulSoup(document, 'html.parser')

        params = dom.select('#Parameters')
        if len(params) > 0:
            section_content = None
            for elem in params[0].next_siblings:
                if type(elem) == Tag:
                    section_content = elem
                    break

            if section_content is None:
                raise MDNPageParseException("Invalid parameters format")

            if section_content.name == 'dl':
                method_info['params'] = parse_section_recursive(section_content)
            else:
                raise MDNPageParseException("Invalid parameters format")
        else:
            method_info['params'] = {}

        returns = dom.select('#Return_values') \
                  or dom.select('#Return_Values') \
                  or dom.select('#Return_value') \
                  or dom.select('#Return_Value')

        if len(returns) > 0:
            section_content = None
            for elem in returns[0].next_siblings:
                if type(elem) == Tag:
                    section_content = elem
                    break

            if section_content is None:
                raise MDNPageParseException("Invalid return values format")

            if section_content.name == 'dl':
                method_info['returns'] = parse_section_recursive(section_content)
            else:
                method_info['returns'] = replace_mdn_formatting(
                    ''.join([str(s) for s in section_content.children]))
        else:
            method_info['returns'] = {}

        return method_info

    async def do_search(self, string: str, session: aiohttp.ClientSession):
        search_url = update_query_string(self.search_url, {"q": string, "count": self._count})

        with async_timeout.timeout(10):
            async with session.get(search_url) as response:
                results = json.loads(await response.text())

        if results['count'] < 1:
            return []

        matched_method = match_method(string, results)

        if len(matched_method) > 0:
            method_to_use = matched_method[0]
            base_path = urlparse(method_to_use['url'])

            with async_timeout.timeout(10):
                async with session.get(update_query_string(base_path,
                                                           {"raw": 1, "section": 'Syntax'})
                                       ) as response:
                    info = self.parse_method_info(await response.text())
                    info['method'] = method_to_use['title']
                    info['description'] = method_to_use['excerpt']
                    info['url'] = method_to_use['url']
                    info['type'] = 'method'

            return info
        else:
            return results['documents']
