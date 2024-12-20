from asyncio import run
import logging
import re
from datetime import timedelta, datetime

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatPermissions
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

TOKEN = None
TRACED_TOPIC = None
ADMIN_ID = None
ALLOWED_HASHTAGS = {"#продам", "#куплю", "#допомога"}

user_posts = dict()

bot = Bot(TOKEN)
dp = Dispatcher()


def return_link_to_user(user_data):
    if user_data.username is None:
        return f'[{user_data.full_name}](tg://user?id={user_data.id})'
    else:
        return f'@{user_data.username}'

async def check_time(message: Message, last_post_time):    
    time_difference = message.date - last_post_time
    print(time_difference)
   

    if time_difference < timedelta(hours=6) and message.from_user.id != ADMIN_ID:
        await message.delete()

        wait_more =  timedelta(hours=6) - time_difference
        hours, remainder = divmod(wait_more.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        link_to_user = return_link_to_user(message.from_user)

        await message.answer(
            f'{link_to_user} ваше объявление было удалено. Следующие объявление можно опубликовать через {hours} ч, {minutes} мин, {seconds} сек.',
            parse_mode=ParseMode.MARKDOWN)



async def check_allowed_hashtags(message: Message):
    hashtags_in_text = set(re.findall(r"#\w+", message.text.lower()))

    if not hashtags_in_text & ALLOWED_HASHTAGS and message.from_user.id != ADMIN_ID:
        try:
            await message.delete()

            permission = ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions=permission,
                until_date=datetime.now() + timedelta(minutes=1))

            link_to_user = return_link_to_user(message.from_user)
            await message.answer(
                f'{link_to_user} вам выдан мут на 1 минуту за нарушение правил',
                parse_mode=ParseMode.MARKDOWN)

        except TelegramBadRequest as e:
            logging.error(e)
    else:
        user_posts[message.from_user.id] = message.date


@dp.message(CommandStart())
async def start_message(message: Message):
    global TRACED_TOPIC
    global ADMIN_ID

    TRACED_TOPIC = message.message_thread_id
    ADMIN_ID = message.from_user.id

    await message.answer('Hi')


@dp.message(lambda message: message.message_thread_id == TRACED_TOPIC)
async def new_message(message: Message):
    last_post_time = user_posts.get(message.from_user.id)
    if last_post_time is not None:
        await check_time(message, last_post_time)
    
    await check_allowed_hashtags(message)
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run(dp.start_polling(bot))