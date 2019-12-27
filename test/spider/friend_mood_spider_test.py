import unittest

from src.spider.QQZoneFriendMoodSpider import QQZoneFriendMoodSpider
from src.analysis.QQZoneAnalysis import QQZoneAnalysis

class FriendMoodSpiderTest(unittest.TestCase):
    """
    测试获取好友说说内容
    """

    def test_init(self):
        QQZoneFriendMoodSpider()

    def test_change_name(self):
        fms = QQZoneFriendMoodSpider(mood_num=20)
        fms.change_username("120000", "test")
        assert fms.raw_username != fms.username

    def test_get_friend_mood(self):
        fms = QQZoneFriendMoodSpider(mood_num=20)
        fms.get_friend_mood()

    def test_generate_friend_info(self):
        qa = QQZoneAnalysis(mood_num=200, use_redis=True)
        qa.get_friend_mood()
        qa.get_useful_info_from_json()
        qa.draw_like_cloud(qa.mood_data_df)
        qa.draw_cmt_cloud(qa.mood_data_df)


if __name__ =='__main__':
    unittest.main()