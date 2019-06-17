import unittest

from src.analysis.QQZoneAnalysis import QQZoneAnalysis


class AnalysisTest(unittest.TestCase):

    def test_init(self):
        QQZoneAnalysis()

    def test_load_data(self):
        qa = QQZoneAnalysis(use_redis=True)
        qa.load_file_from_redis()
        print("data len:",len(qa.content))

    def test_load_data_from_json(self):
        qa = QQZoneAnalysis(use_redis=False)
        qa.load_all_data_from_json()

    # 测试数据清洗
    def test_clean_data(self):
        qa = QQZoneAnalysis(use_redis=False)
        qa.get_useful_info_from_json()
        assert qa.has_clean_data == True

    def test_calculate_send_time(self):
        qa = QQZoneAnalysis(use_redis=True)
        qa.calculate_send_time()
        print("TEST IS NIGHT:", bool(qa.user_info.is_night))

    # 绘制经常评论的人的词云图
    def test_draw_cmt_cloud(self):
        qa = QQZoneAnalysis(use_redis=True)
        qa.get_useful_info_from_json()
        qa.draw_cmt_cloud(qa.mood_data_df)

    # 绘制说说关键字词云图
    def test_draw_content_cloud(self):
        qa = QQZoneAnalysis(use_redis=True)
        qa.get_useful_info_from_json()
        qa.draw_content_cloud(qa.mood_data_df)

    # 绘制点赞的人的词云图
    def test_draw_like_cloud(self):
        qa = QQZoneAnalysis(use_redis=True)
        qa.get_useful_info_from_json()
        qa.draw_like_cloud(qa.mood_data_df)

    # 计算点赞和评论最多的人
    def test_get_most_people(self):
        qa = QQZoneAnalysis(use_redis=True)
        qa.get_most_people()
        print(qa.user_info.like_friend_name)
        print(qa.user_info.cmt_friend_name)

    def test_get_history(self):
        qa = QQZoneAnalysis(use_redis=True)
        qa.calculate_history_like_agree()
        print(len(qa.re.get(qa.history_like_agree_file_name)))

    def test_most_common_friend(self):
        qa = QQZoneAnalysis(use_redis=True, export_csv=True)
        qa.get_most_common_friend()

if __name__ =='__main__':
    unittest.main()






