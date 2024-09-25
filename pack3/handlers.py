import asyncio
from turtledemo.penrose import start

from aiogram import Router
from aiogram.client.session import aiohttp
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from pack3.map_trip_api import map_trip_api
from pack3.weather_api import weather, Weather
from states import SendLocation

router = Router()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    kb = [
        [KeyboardButton(text="отправить геолокацию", request_location=True)]
    ]
    builder = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("отправь геолокацию", reply_markup=builder)


async def weather_func(message: Message, session: aiohttp.ClientSession):
    latitude, longitude = message.location.latitude, message.location.longitude
    try:
        weather_res: Weather = await weather.get_weather(latitude, longitude, session)
        await message.answer(f'погода:\n{weather_res}')
    except Exception as e:
        print(e)
        await message.answer("api погоды не отвечает")


async def places_func(message: Message, session: aiohttp.ClientSession):
    latitude, longitude = message.location.latitude, message.location.longitude
    nearby_places = await map_trip_api.get_nearby_places(latitude, longitude, 10000, session)
    if nearby_places is None:
        await message.answer("поблизости нет объектов")
    else:
        formated = '\n\n\n'.join([str(item) for item in nearby_places])
        await message.answer(f"объекты поблизости:\n{formated}")


@router.message()
async def handle_location(message: Message, state: FSMContext):
    if message.location is None:
        await start_command(message, state)
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(places_func(message, session)), asyncio.create_task(weather_func(message, session))]
        await asyncio.gather(*tasks)
