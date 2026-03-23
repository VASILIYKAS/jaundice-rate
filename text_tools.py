import pymorphy2
import string
import asyncio
import time


def _clean_word(word):
    word = word.replace('«', '').replace('»', '').replace('…', '')
    # FIXME какие еще знаки пунктуации часто встречаются ?
    word = word.strip(string.punctuation)
    return word


async def split_by_words(morph, text):
    """Учитывает знаки пунктуации, регистр и словоформы, выкидывает предлоги."""
    words = []
    start_time = time.monotonic()

    for word in text.split():
        elapsed = time.monotonic() - start_time

        if elapsed > 3.0:
            raise asyncio.TimeoutError("Обработка текста превысила 3 секунды")
        
        cleaned_word = _clean_word(word)

        parsed = await asyncio.to_thread(morph.parse, cleaned_word)
        normalized = parsed[0].normal_form

        if len(normalized) > 2 or normalized == 'не':
            words.append(normalized)
            
    return words


def calculate_jaundice_rate(article_words, charged_words):
    """Расчитывает желтушность текста, принимает список "заряженных" слов и ищет их внутри article_words."""

    if not article_words:
        return 0.0

    found_charged_words = [word for word in article_words if word in set(charged_words)]

    score = len(found_charged_words) / len(article_words) * 100

    return round(score, 2)
