import aiohttp
import asyncio
import pymorphy2
import anyio
import logging
import time

from aiohttp import web
from contextlib import contextmanager
from pathlib import Path
from enum import Enum
from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from text_tools import split_by_words, calculate_jaundice_rate
from functools import partial


logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


@contextmanager
def elapsed_time():
    start = time.monotonic()
    yield lambda: time.monotonic() - start


def load_charged_words(folder='charged_dict'):
    folder_path = Path(folder)
    word_files = ['negative_words.txt', 'positive_words.txt']
    all_words = set()

    for filename in word_files:
        file_path = folder_path / filename

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    all_words.add(word)

    return list(all_words)


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, morph, charged_words, url):
    try:
        html = await fetch(session, url)
        clean_text = sanitize(html, True)
        article_words = await split_by_words(morph, clean_text)
        words_count = len(article_words)
        score = calculate_jaundice_rate(article_words, charged_words)

        return {
            'status': ProcessingStatus.OK.value,
            'url': url,
            'score': score,
            'words_count': words_count,
        }

    except asyncio.TimeoutError:
        return {
            'status': ProcessingStatus.TIMEOUT.value,
            'url': url,
            'score': None,
            'words_count': None,
        }

    except ArticleNotFound:
        return {
            'status': ProcessingStatus.PARSING_ERROR.value,
            'url': url,
            'score': None,
            'words_count': None,
        }

    except (aiohttp.ClientError, aiohttp.ClientResponseError):
        return {
            'status': ProcessingStatus.FETCH_ERROR.value,
            'url': url,
            'score': None,
            'words_count': None,
        }


async def handle(request, morph, charged_words):
    urls_param = request.query.get('urls', '')
    
    if not urls_param:
        return web.json_response(
            {"error": "Параметр 'urls' обязателен"}, 
            status=400
        )
    
    urls_list = [url.strip() for url in urls_param.split(',') if url.strip()]
    
    if not urls_list:
        return web.json_response(
            {"error": "Список URL пуст"}, 
            status=400
        )
    
    if len(urls_list) > 10:
        return web.json_response(
            {"error": "too many urls in request, should be 10 or less"}, 
            status=400
        )
    
    invalid_urls = []
    for url in urls_list:
        if not url.startswith('https://inosmi.ru/'):
            invalid_urls.append(url)
    
    if invalid_urls:
        return web.json_response(
            {"error": f"URL не принадлежат inosmi.ru: {', '.join(invalid_urls)}"},
            status=400
        )
    
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls_list:
            task = asyncio.create_task(process_article(session, morph, charged_words, url))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
    
    return web.json_response(results)


async def on_startup(app):
    charged_words = load_charged_words()
    morph = pymorphy2.MorphAnalyzer()
    
    app['charged_words'] = charged_words
    app['morph'] = morph
    
    logging.info("Приложение запущено, данные загружены")


def main():
    app = web.Application()
    
    app.on_startup.append(on_startup)
    
    charged_words = load_charged_words()
    morph = pymorphy2.MorphAnalyzer()
    
    handler = partial(handle, morph=morph, charged_words=charged_words)
    
    app.add_routes([web.get('/', handler)])
    
    web.run_app(app, host='127.0.0.1', port=8080)


if __name__ == '__main__':
    main()
