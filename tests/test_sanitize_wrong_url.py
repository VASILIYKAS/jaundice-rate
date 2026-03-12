import requests
import pytest

from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound


def test_sanitize_wrong_url():
    resp = requests.get('http://example.com')
    resp.raise_for_status()
    with pytest.raises(ArticleNotFound):
        sanitize(resp.text)