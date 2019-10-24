import aiohttp

from bs4 import BeautifulSoup
from furl import furl


# TODO: refactor with session and proxy settings
async def get_html(url, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, **kwargs) as response:
            response.raise_for_status()
            return await response.text()


class ChipFind:
    TYPE = {
        '': 'Куплю/Продам',
        'buy': 'Куплю',
        'sale': 'Продам'
    }
    @classmethod
    def get_item_url(cls, url):
        return furl(f'https://www.chipfind.ru/market/').join(url).url

    @classmethod
    def get_search_url(cls):
        return cls.get_item_url('search.htm')

    @classmethod
    def get_search_query(cls, url):
        if furl(url).remove(fragment=True, query=True).url != cls.get_search_url():
            raise ValueError(f'url={url} has not supported endpoint')
        query_params = furl(url).query.params
        return {key: query_params[key] for key in ('s', 'filter') if query_params.get(key)}

    @staticmethod
    def parse_item_urls(html):
        soup = BeautifulSoup(html, features='html.parser')
        item_elements = soup.select('table.post td.rr h3 a')
        next_items_element = soup.select_one('div.pages a#next')
        return ([element.attrs['href'] for element in item_elements],
                next_items_element and next_items_element.attrs['href'])

    @classmethod
    async def collect_search_item_urls(cls, query):
        html = await get_html(
            url=cls.get_item_url('search.htm'), params=query)
        items, next_items_url = cls.parse_item_urls(html)
        while next_items_url:
            html = await get_html(url=cls.get_item_url(next_items_url))
            next_items, next_items_url = cls.parse_item_urls(html)
            items.extend([item for item in next_items if item not in items])
        return items

    @classmethod
    def format_query_message(cls, query):
        return f'{query["s"]} ({cls.TYPE.get(query["filter"].lower())})'
