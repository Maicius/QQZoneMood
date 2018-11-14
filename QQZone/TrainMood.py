from QQZone.QQZoneAnalysis import QQZoneAnalysis
import json
from QQZone.util.util import get_file_list, get_mktime2
import pandas as pd

class TrainMood(QQZoneAnalysis):
    def __init__(self, use_redis=False, debug=True, file_name_head='maicius'):
        QQZoneAnalysis.__init__(self, use_redis=True, debug=True, file_name_head='maicius', stop_time='2014-06-10',
                                  stop_num=500, analysis_friend=False)
        self.IMAGE_SCORE_FILE_PATH = '/Users/maicius/code/nima.pytorch/nima/result_dict.json'
        self.MOOD_DATA_SCORE_FILE_NAME = 'data/train/' + file_name_head + '_score_mood_data.csv'
        self.mood_data_df = pd.read_csv(self.MOOD_DATA_FILE_NAME)

        with open(self.IMAGE_SCORE_FILE_PATH, 'r', encoding='utf-8') as r:
            self.image_score_dict = json.load(r)

        self.image_score_df = pd.DataFrame(self.image_score_dict)
        self.mood_data_df['score'] = '-1'
        self.image_dir = '/Users/maicius/code/InterestingCrawler/QQZone/qq_big_image/maicius/'
        self.image_file_list = get_file_list(self.image_dir)

    def calculate_score_for_each_mood(self):
        """
        计算每条说说中图片的平均分
        对于没有图片的按均值进行填充
        :return:
        """
        mean_score = self.image_score_df[self.image_score_df['score'] != -1].mean()[0]
        self.image_score_df.loc[self.image_score_df.score == -1, 'score'] = mean_score
        tid_list = self.mood_data_df['tid'].values
        for tid in tid_list:
            scores = self.image_score_df[self.image_score_df.image.str.contains(tid)].score
            if len(scores) > 0:
                self.mood_data_df.loc[self.mood_data_df.tid == tid, 'score'] = round(scores.mean(),2)
        self.mood_data_df.fillna(mean_score)
        # self.export_df_after_score()

    def calculate_send_time(self):
        """
        计算每条说说的发送时间
        分为以下五种类型：
        0.午夜：0点-4点
        1.凌晨：4点-8点
        2.上午：8点-12点
        3.下午：12点-16点
        4.傍晚：16点-20点
        5.晚上：20点-24点
        :return:
        """
        day_begin_time = self.mood_data_df['time'].apply(lambda x: get_mktime2(x))
        day_time_stamp = self.mood_data_df['time_stamp']
        time_diff = day_time_stamp - day_begin_time
        # 四个小时的时间差
        time_step = 60 * 60 * 4
        time_state = time_diff.apply(lambda x: x // time_step)
        self.mood_data_df['time_state'] = time_state


    def export_df_after_score(self):
        self.mood_data_df.drop(['Unnamed: 0'], axis=1, inplace=True)
        self.mood_data_df.to_csv(self.MOOD_DATA_SCORE_FILE_NAME)


if __name__ =='__main__':
    train = TrainMood()
    train.calculate_score_for_each_mood()
    train.calculate_send_time()
    train.export_df_after_score()

