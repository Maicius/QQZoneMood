import unittest

from src.spider.QQZoneFriendMoodSpider import QQZoneFriendMoodSpider


class FriendMoodSpiderTest(unittest.TestCase):

    def test_init(self):
        QQZoneFriendMoodSpider()

    def test_change_name(self):
        fms = QQZoneFriendMoodSpider(mood_num=20)
        fms.change_username("120000")
        assert fms.raw_username != fms.username

    def test_get_friend_mood(self):
        fms = QQZoneFriendMoodSpider(mood_num=20)
        fms.get_friend_mood()
