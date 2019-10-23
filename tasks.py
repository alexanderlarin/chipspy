import asyncio
import logging

from types import SimpleNamespace

from chipfind import ChipFind
from dispatcher import Context

logger = logging.getLogger(__name__)


async def publish_search_items(context: Context):
    search_pages = [SimpleNamespace(**search_page) for search_page in context.store.get_search_pages()]
    logger.info(f'search_pages count={len(search_pages)}')

    async def publish_search_item(item_url, search_page):
        logger.info(f'publish item_url={item_url} to chat_id={search_page.chat_id}')
        await context.bot.send_message(search_page.chat_id,
                                       text=f'Олег, новое объявление по запросу: '
                                            f'{ChipFind.format_query_message(search_page.query)}\n'
                                            f'{ChipFind.get_item_url(item_url)}')
        context.store.publish_notice(item_url, chat_id=search_page.chat_id)

    for idx, search_page in enumerate(search_pages):
        item_urls = await ChipFind.collect_search_item_urls(search_page.query)
        publish_item_urls = [item_url for item_url in item_urls
                             if not context.store.is_notice_published(item_url, chat_id=search_page.chat_id)]
        logger.info(f'[{idx + 1}/{len(search_pages)}] count=[{len(publish_item_urls)}/{len(item_urls)}] '
                    f'publish search items with query={search_page.query} for chat_id={search_page.chat_id}')
        await asyncio.gather(*[publish_search_item(item_url, search_page)
                               for item_url in publish_item_urls])


async def watch_publish_search_items(context: Context, timeout):
    while True:
        try:
            logger.info('watch publish_search_items started')
            await publish_search_items(context)

        except Exception as ex:
            logger.error(f'watch publish_search_items failed with error {ex!r}')
            logger.exception(ex)

        logger.info(f'watch publish_search_items sleeps for {timeout}secs')
        await asyncio.sleep(timeout)
