import unittest

from src.spider.BaseSpider import BaseSpider
from src.spider.QQZoneSpider import QQZoneSpider


class SpiderTest(unittest.TestCase):

    def test_connect_redis(self):
        bs = BaseSpider(use_redis=True, from_web=True)
        bs.connect_redis()

    def test_read_config_file(self):
        BaseSpider(use_redis=False, from_web=False)

    def test_get_json(self):
        test_str = '_Callback( {"code":0, "subcode":0, "message":"succ"});'
        expect = '{"code":0, "subcode":0, "message":"succ"}'
        bs = BaseSpider(use_redis=False, from_web=False)
        res = bs.get_json(test_str)
        assert res == expect

    # 测试每个线程划分的说说数量
    def test_step(self):
        sp = QQZoneSpider(use_redis=False, debug=False)
        step1 = sp.find_best_step(1100, 5)
        step2 = sp.find_best_step(1222, 5)
        step3 = sp.find_best_step(2222, 10)
        assert step1 == 220
        assert step2 == 240
        assert step3 == 220

    def test_selenium_login(self):
        sp = QQZoneSpider(use_redis=False, debug=False)
        sp.login()

    def test_get_main_page(self):
        sp = QQZoneSpider(use_redis=False, debug=False)
        sp.login()
        sp.get_main_page_info()

    # 测试下载图片，不下载动态
    def test_download_image(self):
        sp = QQZoneSpider(use_redis=False, debug=False, mood_num=20, download_mood_detail=False,
                          download_like_detail=False, download_like_names=False, download_big_image=True,
                          download_small_image=True)
        sp.login()
        sp.get_mood_list()
