import asyncio
import pymorphy2

from text_tools import split_by_words


def test_split_by_words():
    # Экземпляры MorphAnalyzer занимают 10-15Мб RAM т.к. загружают в память много данных
    # Старайтесь организовать свой код так, чтоб создавать экземпляр MorphAnalyzer заранее и в единственном числе
    morph = pymorphy2.MorphAnalyzer()

    result = asyncio.run(split_by_words(morph, 'Во-первых, он хочет, чтобы'))
    assert result == ['во-первых', 'хотеть', 'чтобы']

    result = asyncio.run(split_by_words(morph, '«Удивительно, но это стало началом!»'))
    assert result == ['удивительно', 'это', 'стать', 'начало']