import aiogram
import logging

from aiogram.dispatcher import filters
from aiogram.dispatcher.filters.state import State
from chipfind import ChipFind
from store import Store
from typing import NamedTuple

logger = logging.getLogger(__name__)

Context = NamedTuple('Context', [
    ('bot', aiogram.Bot),
    ('store', Store)
])

search_url_state = State('search_url')


class Dispatcher(aiogram.Dispatcher):
    HELP = '\n/addsearch - добавить ссылку на страницу поиска, за которой нужно присматривать' \
           '\n/cancel    - отменить текущую операцию'

    def __init__(self, context, state_storage):
        super().__init__(bot=context.bot, storage=state_storage)

        self.context = context

        self.register_message_handler(self.start, commands=['start'])
        self.register_message_handler(self.cancel, commands=['cancel'], state='*')
        self.register_message_handler(self.cancel, filters.Text(equals='cancel', ignore_case=True), state='*')

        self.register_message_handler(self.add_search, commands=['addsearch'])
        self.register_message_handler(self.process_search_url, state=search_url_state)
        # self.register_message_handler(self.remove_search, commands=['removesearch'])

        self.register_message_handler(self.echo)

    async def start(self, message: aiogram.types.Message):
        await self.bot.send_message(message.chat.id,
                                    text='Привет, Олег. Как сам?\n'
                                         'Вот тебе список команд:\n'
                                         '/add_search\n' + self.HELP)

    async def cancel(self, message: aiogram.types.Message, state: aiogram.dispatcher.FSMContext):
        pass

    async def add_search(self, message: aiogram.types.Message):
        await search_url_state.set()
        await self.bot.send_message(message.chat.id,
                                    text=f'Олег, поищи на {ChipFind.get_search_url()} то, что тебе нужно,\n'
                                         'скопируй адрес страницы в строке браузера и пошли мне!')

    async def process_search_url(self, message: aiogram.types.Message, state: aiogram.dispatcher.FSMContext):
        try:
            query = ChipFind.get_search_query(message.text)

            logger.info(f'subscribe chat_id={message.chat.id} on search page with query={query}')
            self.context.store.add_search_page(query, chat_id=message.chat.id)
            await state.finish()

            item_urls = await ChipFind.collect_search_item_urls(query)
            logger.info(f'parse search page query={query} item_urls count={len(item_urls)}')

            for item_url in item_urls:
                if self.context.store.publish_notice(item_url, chat_id=message.chat.id):
                    logger.info(f'item_url={item_url} is skipped for chat_id={message.chat.id}')

            await self.bot.send_message(message.chat.id,
                                        text=f'Ну норм, будем наблюдать за запросом: '
                                             f'{ChipFind.format_query_message(query)}')
        except Exception as ex:
            logger.error(f'trouble in message={message.text} processing')
            logger.exception(ex)
            await message.reply(text='Олег, ну что за ерунду ты прислал? Попробуй-ка еще разок...\n' + self.HELP)

    # async def remove_search(self, message: aiogram.types.Message):
    #     pass

    @classmethod
    async def echo(cls, message: aiogram.types.Message):
        await message.reply(text='Это что, Олег? Мы такое не умеем...\n' + cls.HELP)
