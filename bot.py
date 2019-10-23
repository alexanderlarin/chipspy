import aiohttp
import aiogram
import argparse
import asyncio
import logging.config

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from box import Box

from dispatcher import Context, Dispatcher
from store import Store
from tasks import watch_publish_search_items

logger = logging.getLogger('bot')


def create_bot(token, proxy_url=None, proxy_auth=None):
    proxy_params = {}
    if proxy_url:
        logger.info(f'use proxy={proxy_url}')
        proxy_params['proxy'] = proxy_url

        if proxy_auth:
            logger.info(f'use proxy_auth={proxy_auth}')
            proxy_params['proxy_auth'] = aiohttp.BasicAuth(
                login=proxy_auth['username'], password=proxy_auth['password'])

    logger.info(f'init bot with token={token}')

    return aiogram.Bot(token, **proxy_params)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.json',
                        help='the path to JSON-formatted configuration file')

    args = parser.parse_args()

    config = Box.from_json(filename=args.config)
    logging.config.dictConfig(config['logging'])

    logger.info(f'create bot with config={config.bot}')
    bot = create_bot(**config.bot)

    logger.info(f'create store with config={config.store}')
    store = Store(**config.store)

    logger.info(f'create dispatcher with bounded context')
    context = Context(
        bot=bot,
        store=store
    )

    dispatcher = Dispatcher(context=context, state_storage=MemoryStorage())


    async def startup(_):
        logger.info('startup callbacks')
        asyncio.ensure_future(watch_publish_search_items(context, config.watch_timeout))


    async def shutdown(_):
        logger.info('shutdown callbacks')
        store.close()

    aiogram.executor.start_polling(dispatcher, skip_updates=True,
                                   on_startup=startup, on_shutdown=shutdown)
