import os
from src.util.constant import BASE_DIR
from src.analysis.QQZoneAnalysis import get_mood_df
import pandas as pd

class QQUser(object):
    """
    生成User实体
    """


    def __init__(self, QQ='', name=''):
        RESULT_BASE_DIR = BASE_DIR + "data/result/" + QQ + '_mood_data.csv'
        if os.path.exists(RESULT_BASE_DIR):
            self.mood_df = pd.read_csv(RESULT_BASE_DIR)
        else:
            self.mood_df = get_mood_df(QQ)

    def get_mood_df(self):
        return self.mood_df
