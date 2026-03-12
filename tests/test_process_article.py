import pytest
import asyncio
import aiohttp
import pymorphy2

from server import process_article, ProcessingStatus, load_charged_words


morph = pymorphy2.MorphAnalyzer()
charged_words = load_charged_words()


@pytest.mark.anyio
async def test_process_article_fetch_error():
    async with aiohttp.ClientSession() as session:
        result = await process_article(
            session, 
            morph, 
            charged_words, 
            'https://inosmi.ru/politic/20190629/245376799111111.html'
        )
        
        assert result['status'] == ProcessingStatus.FETCH_ERROR.value
        assert result['score'] is None
        assert result['words_count'] is None


@pytest.mark.anyio
async def test_process_article_parsing_error():
    async with aiohttp.ClientSession() as session:
        result = await process_article(
            session,
            morph,
            charged_words,
            'https://inosmi.ru/'
        )
        
        assert result['status'] == ProcessingStatus.PARSING_ERROR.value
        assert result['score'] is None
        assert result['words_count'] is None


@pytest.mark.anyio
async def test_process_article_timeout():

    timeout = aiohttp.ClientTimeout(total=1)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        result = await process_article(
            session,
            morph,
            charged_words,
            'https://httpbin.org/delay/5'
        )
        
        assert result['status'] == ProcessingStatus.TIMEOUT.value
        assert result['score'] is None
        assert result['words_count'] is None