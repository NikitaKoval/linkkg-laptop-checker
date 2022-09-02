#!/usr/bin/env python
from functools import lru_cache
from typing import List

from lxml import etree
import requests

KEYWORD_TO_BE_CLEARED = ('Ультрабук', 'Ноутбук', 'ноутбук', 'Игровой', 'Ultrabook')
URL = 'https://www.link.kg/price.php?s_ids=1&clarifyApply='


class Product:
    def __init__(self, title, price_kgs, price_usd):
        self.title = title.strip()
        self.price_kgs = price_kgs.strip()
        self.price_usd = price_usd.strip()

        self._clean()

    def _clean(self):
        for word in KEYWORD_TO_BE_CLEARED:
            self._remove_from_title(word)
        self.title = self.title.strip()

    def _remove_from_title(self, word):
        self.title = self.title.replace(word, '')

    @classmethod
    def fromlist(cls, values):
        return (cls(*value) for value in values)

    @property
    @lru_cache
    def keywords(self) -> List:
        return list(map(lambda x: x.strip(), self.title.split(',')))


class TableParser:
    def __init__(self, provider):
        self.provider = provider

        self.parsed = []

    def parse(self):
        tree = etree.HTML(self.provider.html)
        items = tree.xpath('//table[@class="catalogue"]//tr')
        for item in items:
            try:
                title = item.getchildren()[1].getchildren()[0].tail.strip()
                price_kgs = item.getchildren()[2].getchildren()[0].tail
                price_usd = item.getchildren()[3].text
                self.parsed.append((title, price_kgs, price_usd))
            except:
                pass


class HTMLProvider:
    def __init__(self, url):
        self.url = url

        self.html = None

    def fetch_html(self):
        response = requests.get(URL)
        self.html = response.text


class ProductRepo:
    def __init__(self, products):
        self.products = products

    @classmethod
    def from_parsed_tuples(cls, product_tuples):
        return cls(Product.fromlist(parser.parsed))

class Filter:
    def __init__(self, product_repo, keywords=None):
        self.product_repo = product_repo
        if keywords is None:
            self.keywords = []
        self.keywords = keywords

        self.matched = []

    def find_matches(self):
        for item in self.product_repo.products:
            if any(self._clauses(item)):
                self.matched.append(item)

    def _clauses(self, product):
        for keyword in self.keywords:
            yield keyword in product.title


if __name__ == '__main__':
    provider = HTMLProvider(URL)
    parser = TableParser(provider)

    provider.fetch_html()
    parser.parse()

    repo = ProductRepo.from_parsed_tuples(parser.parsed)
    filter = Filter(repo, [' DDR5'])
    filter.find_matches()
    for product in filter.matched:
        print('\n'.join(product.keywords))
        print('---')
        print(f'{product.price_kgs}')
        print(f'{product.price_usd}')
        print('\n')
