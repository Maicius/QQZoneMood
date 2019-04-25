import os
from src.util.constant import BASE_DIR
from src.analysis.QQZoneAnalysis import get_mood_df
import pandas as pd

class QQUser(object):
    """
    生成Web实体
    """
    def __init__(self, QQ='', name=''):
        RESULT_BASE_DIR = BASE_DIR + "data/result/" + name + '_mood_data.csv'
        if os.path.exists(RESULT_BASE_DIR):
            mood_df = pd.read_csv(RESULT_BASE_DIR)
        else:
            mood_df = get_mood_df(name)


