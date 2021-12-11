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
        fms = QQZoneFriendMoodSpider(mood_num=200)
        fms.get_friend_mood()

    # 本方法用于测试获取某一指定的tid的说说的所有评论
    def test_get_friend_target_mood(self):
        target_tid = 'c060675ac576a961ebdc0800'
        cmt_num = 233
        fms = QQZoneFriendMoodSpider(mood_num=20)
        fms.get_friend_mood()
        cmt_list = fms.get_all_cmt_num(cmt_num, target_tid)
        print(len(cmt_list))


    def test_generate_friend_info(self):
        qa = QQZoneAnalysis(mood_num=200, use_redis=False, debug=True)
        # 建议在resource/config/friend_info.json中配置需要爬取的好友QQ号
        # 也可以直接在这里传入qq号，此处传入的QQ号优先级比配置文件大，但是配置文件可以批量传入QQ号
        qa.get_friend_mood(friend_qq='')
        qa.get_useful_info_from_json()
        qa.draw_like_cloud(qa.mood_data_df)
        qa.draw_cmt_cloud(qa.mood_data_df)


if __name__ =='__main__':
    unittest.main()
