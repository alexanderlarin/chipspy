import enum
import logging

from collections import namedtuple
from tinydb import TinyDB, where
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage

logger = logging.getLogger(__name__)


class Store:
    def __init__(self, path):
        # IMPORTANT: read cache behavior, store.close() is never called on sigterm and ctrl-c
        caching_middleware = CachingMiddleware(JSONStorage)
        caching_middleware.WRITE_CACHE_SIZE = 1
        self._db = TinyDB(path, storage=caching_middleware)

    def close(self):
        logger.info('flush and close')
        self._db.close()

    @property
    def search_pages(self):
        return self._db.table('search_pages')

    @property
    def board_notices(self):
        return self._db.table('board_notices')

    def get_search_pages(self):
        return self.search_pages.all()

    def add_search_page(self, query, chat_id):
        if not self.search_pages.contains((where('chat_id') == chat_id) & (where('query') == query)):
            return self.search_pages.insert({'chat_id': chat_id, 'query': query})

    def remove_search_page(self, query, chat_id):
        return self.search_pages.remove((where('chat_id') == chat_id) & (where('query') == query))

    def is_notice_published(self, item_url, chat_id):
        return self.board_notices.contains((where('chat_id') == chat_id) & (where('item_url') == item_url))

    def publish_notice(self, item_url, chat_id):
        if not self.board_notices.contains((where('chat_id') == chat_id) & (where('item_url') == item_url)):
            return self.board_notices.insert({'chat_id': chat_id, 'item_url': item_url})
