from QQZone.QQZoneAnalysis import QQZoneAnalysis
import json
from QQZone.util.util import get_file_list
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
        mean_score = self.image_score_df[self.image_score_df['score'] != -1].mean()[0]
        self.image_score_df.loc[self.image_score_df.score == -1, 'score'] = mean_score
        tid_list = self.mood_data_df['tid'].values
        for tid in tid_list:
            scores = self.image_score_df[self.image_score_df.image.str.contains(tid)].score
            if len(scores) > 0:
                self.mood_data_df.loc[self.mood_data_df.tid == tid, 'score'] = round(scores.mean(),2)
        self.mood_data_df.fillna(mean_score)

    def export_df_after_score(self):
        self.mood_data_df.drop(['Unnamed: 0'], axis=1, inplace=True)
        self.mood_data_df.to_csv(self.MOOD_DATA_SCORE_FILE_NAME)


if __name__ =='__main__':
    train = TrainMood()
    train.calculate_score_for_each_mood()
    train.export_df_after_score()
