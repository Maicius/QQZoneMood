import unittest

from src.spider.BaseSpider import BaseSpider

class SpiderTest(unittest.TestCase):

    def test_connect_redis(self):
        bs = BaseSpider(use_redis=True, from_web=True)
        bs.connect_redis()

    def test_read_config_file(self):
        BaseSpider(use_redis=False, from_web=False)