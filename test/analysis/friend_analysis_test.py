import unittest
from src.analysis.QQZoneAnalysis import QQZoneAnalysis


class FriendAnalysisTest(unittest.TestCase):

    def setUp(self) -> None:
        self.qa = QQZoneAnalysis(use_redis=True)
        self.qa.change_username("850053825", "fuyuko")

    def test_init(self) -> None:
        pass

    def test_get_friend_data(self):
        self.qa.get_friend_mood()

    def test_clean_friend_data(self):
        self.qa.get_useful_info_from_json()
        assert self.qa.has_clean_data == True

    def test_draw_friend_cmt_cloud(self):
        self.qa.get_useful_info_from_json()
        self.qa.draw_cmt_cloud(self.qa.mood_data_df)

    # 计算点赞和评论最多的人
    def test_get_friend_most_people(self):
        self.qa.get_most_people()
        print(self.qa.user_info.like_friend_name)
        print(self.qa.user_info.cmt_friend_name)

    # 绘制说说关键字词云图
    def test_draw_content_cloud(self):
        self.qa.get_useful_info_from_json()
        self.qa.draw_content_cloud(self.qa.mood_data_df)

    # 绘制点赞的人的词云图
    def test_draw_like_cloud(self):
        self.qa.get_useful_info_from_json()
        self.qa.draw_like_cloud(self.qa.mood_data_df)

    def test_get_history(self):
        self.qa.calculate_history_like_agree()
        print(len(self.qa.re.get(self.qa.history_like_agree_file_name)))

    def test_export_data_df(self):
        self.qa.export_mood_df()

if __name__ == '__main__':
    unittest.main()