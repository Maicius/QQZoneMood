import unittest

from src.spider.BaseSpider import BaseSpider
from src.spider.QQZoneSpider import QQZoneSpider
from src.spider.main import capture_main_data
import json

class SpiderTest(unittest.TestCase):
    """
    对Spider进行测试
    """
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
        sp = QQZoneSpider(use_redis=False, debug=True)
        sp.login()
        sp.get_main_page_info()

    # 测试下载图片，不下载动态
    def test_download_image(self):
        sp = QQZoneSpider(use_redis=False, debug=False, mood_num=100, download_mood_detail=False,
                          download_like_detail=False, download_like_names=False, download_big_image=True,
                          download_small_image=True)
        sp.login()
        sp.get_mood_list()
        print("Thread Wait:", sp.image_thread_pool.time_spend)

    # 测试抽取tid
    def test_extract_tid(self):
        sp = QQZoneSpider(use_redis=False, debug=False, mood_num=20, download_mood_detail=False,
                          download_like_detail=True, download_like_names=False)
        str1 = 'http://user.qzone.qq.com/1272082503/mood/4770d24b00acd95c13e00500.1<.>http://user.qzone.qq.com/1272082503/mood/4770d24b00acd95c13e00500.1'
        str2 = 'http://user.qzone.qq.com/1272082503/mood/4770d24bbb83d95c05600900.1^||^https://b339.photo.store.qq.com/psb?/91b7c939-e3c7-41d8-a450-626a11d7ce19/4iKMKW.M8phXT8bghzPgKjz.rdkmby5vOiOJi4PqSlk!/b/dFMBAAAAAAAA&bo=7gI2Be4CNgURECc!^||^0'
        str3 = 'http://user.qzone.qq.com/1272082503/mood/4770d24b5c91d65cf9af0b00.1<.>http://user.qzone.qq.com/1272082503/mood/4770d24b5c91d65cf9af0b00.1'
        expect1 = '4770d24b00acd95c13e00500'
        expect2 = '4770d24bbb83d95c05600900'
        expect3 = '4770d24b5c91d65cf9af0b00'

        assert expect1 == sp.extract_tid_from_unikey(str1)
        assert expect2 == sp.extract_tid_from_unikey(str2)
        assert expect3 == sp.extract_tid_from_unikey(str3)

    # 测试只下载说说详情
    def test_capture_info(self):
        sp = QQZoneSpider(use_redis=True, debug=False, mood_num=20, download_mood_detail=False,
                          download_like_detail=True, download_like_names=False)

        sp.login()
        sp.get_mood_list()

    # 并发获取200条说说数据
    def test_capture_info_parallel(self):
        sp = QQZoneSpider(use_redis=True, debug=False, mood_num=200)
        sp.login()
        sp.get_mood_list()

    # 获取全部说说数据，不下载图片
    def test_capture_main_data(self):
        sp = QQZoneSpider(use_redis=True, debug=False)
        sp.login()
        sp.get_main_page_info()
        sp.get_mood_list()

    def test_simple_qr_login(self):
        sp = QQZoneSpider(use_redis=False, debug=True, mood_num=200)
        sp.login_with_qr_code()

    def test_login_with_qr_code(self):
        sp = QQZoneSpider(use_redis=True, debug=True, mood_num=200)
        sp.login_with_qr_code()
        print("Login success")
        sp.get_main_page_info()
        sp.get_mood_list()

    def test_get_first_mood(self):
        sp = QQZoneSpider(use_redis=False, debug=True)
        sp.login_with_qr_code()
        mood_num = sp.get_mood_num()
        sp.get_first_mood(mood_num)

    def test_retry(self):
        failed_msg = '{"code":-3000,"message":"\xe8\xaf\xb7\xe5\x85\x88\xe7\x99\xbb\xe5\xbd\x95\xe7\xa9\xba\xe9\x97\xb4","result":{"code":1003,"msg":"\xe8\xaf\xb7\xe5\x85\x88\xe7\x99\xbb\xe5\xbd\x95\xe7\xa9\xba\xe9\x97\xb4","now":1596656257},"subcode":-1000001}'
        pass


if __name__ =='__main__':
    unittest.main()