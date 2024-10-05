import asyncio

import aiohttp
from pack3.config_reader import config


class Address:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return ", ".join(self.__dict__.values())


class NearbyPlace:

    def __init__(self, name, address: Address, type):
        self._name = name
        self._address = address
        self._type = type

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @property
    def type(self):
        return self._type

    def __repr__(self):
        return (f"название: {self._name}\n\n"
                f"адрес: {self._address}\n\n"
                f"тип: {self._type}\n\n")


class MapTripAPI:

    def __init__(self, api_key):
        self._api_key = api_key

    async def _get_info_by_id(self, id, session: aiohttp.ClientSession):
        url = f'https://api.opentripmap.com/0.1/ru/places/xid/{id}'
        params = {'apikey': self._api_key}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if len(data) > 0 and resp.status == 200:
                return NearbyPlace(data['name'] if data["name"] else "без названия", Address(**data["address"]), data['kinds'].replace(',', ', ').replace('_', ' '))
            else:
                return None

    async def get_nearby_places(self, lat, lon, radius, session: aiohttp.ClientSession):
        url = 'https://api.opentripmap.com/0.1/ru/places/radius'
        params = {'lat': lat, 'lon': lon, 'radius': radius, "lang": "ru", 'apikey': self._api_key, "limit": 10}
        response = await session.get(url, params=params)
        js = await response.json()
        if len(js['features']) == 0:
            return None
        ids = []
        for place in js["features"]:
            ids.append(place["properties"]["xid"])
        tasks = []
        for id in ids:
            tasks.append(asyncio.create_task(self._get_info_by_id(id, session)))
        await asyncio.gather(*tasks)
        results = [item.result() for item in tasks if item.result() is not None]
        return results


map_trip_api = MapTripAPI(api_key=config.trip_map_token.get_secret_value())