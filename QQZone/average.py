import numpy as np
import pandas as pd
from QQZone.QQZoneAnalysis import QQZoneAnalysis


class Average(object):

    """
    创建一个平均数类"，用于计算cmt_total_num、like_num、prd_num的均值"""

    def __init__(self, use_redis=False, debug=True, file_name_head="", filename="", filename_list=None):
        """

        :param use_redis:
        :param debug:
        :param file_name_head:
        :param filename:
        :param filename_list:
        """
        self.df = None
        self.filename = filename
        self.filename_list = filename_list
        self.N_V_FILE_NAME = 'data/' + file_name_head + '_n_v_mood_data.csv'
        self.qqzone = QQZoneAnalysis(use_redis, debug, file_name_head)
        if file_name_head != "" and filename == "":
            self.filename = self.qqzone.MOOD_DATA_FILE_NAME
        self.read_data_from_csv()

    def calculate_E(self, i):
        """计算某一条动态的热度，并用E表示"""
        m = self.df[i, 2]  ##第i条动态的评论数
        n = self.df[i, 5]  ##第i条动态的点赞数
        h = self.df[i, 7]  ##第i条动态的浏览数
        a = self.like_num_average / self.cmt_total_num_average  ##平均点赞量与平均评论量的比值
        b = self.prd_num_average / self.like_num_average  ##平均浏览量与平均点赞量的比值
        E = m * a * b + n * b + h  ##计算热度
        return E

    def read_data_from_csv(self):
        if self.filename == "" and self.filename_list is None:
            self.qqzone.format_error("文件名不能为空")
        data_df = pd.DataFrame()
        if self.filename_list is not None:
            for file_name in self.filename_list:
                df = pd.DataFrame(pd.read_csv(file_name))
                data_df = pd.concat([data_df, df], axis=0)
        if self.filename_list is None and self.filename != "":
            data_df = pd.DataFrame(pd.read_csv(self.filename))

        if self.qqzone.debug:
            print("Read Data From:", self.filename, self.filename_list)
            print("data df shape:", data_df.shape)
        self.df = data_df

    def calculate_all(self):
        self.cmt_total_num_average = self.df['cmt_total_num'].mean()
        self.like_num_average = self.df['like_num'].mean()
        self.prd_num_average = self.df['prd_num'].mean()
        a = self.like_num_average / self.cmt_total_num_average  ##平均点赞量与平均评论量的比值
        b = self.prd_num_average / self.like_num_average  ##平均浏览量与平均点赞量的比值
        m = self.df['cmt_total_num']
        n = self.df['like_num']
        h = self.df['prd_num']
        self.E = m * a * b + n * b + h
        self.V = self.E / self.df['friend_num']
        self.normalized_V()
        self.concat_n_V()

    def normalized_V(self):
        self.n_V = (self.V - min(self.V)) / (max(self.V) - min(self.V))
        if self.qqzone.debug:
            print("Self.nv:")
            print(self.n_V)

    def concat_n_V(self):
        self.df['n_V'] = self.n_V
        self.df.to_csv(self.N_V_FILE_NAME)


if __name__ == '__main__':
    av = Average(use_redis=True, debug=True, file_name_head="maicius")
    av.calculate_all()