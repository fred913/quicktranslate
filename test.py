# coding: utf-8

import asyncio
import time

import aiohttp


async def test_translation():
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:8000/translate',
                               params={
                                   'text': 'Hello world',
                                   'to_lang': 'zh_CN'
                               }) as response:
            assert response.status == 200
            data = await response.json()
            print(data)
    end_time = time.time()
    print(f"Time (via GET) taken: {(end_time - start_time)*1000}ms")


async def test_translation_via_post():
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8000/translate',
                                json={
                                    'text': 'Hello world',
                                    'to_lang': 'zh_CN'
                                }) as response:
            assert response.status == 200
            data = await response.json()
            print(data)
    end_time = time.time()
    print(f"Time (via POST) taken: {(end_time - start_time)*1000}ms")


if __name__ == '__main__':
    asyncio.run(test_translation())
    asyncio.run(test_translation_via_post())
