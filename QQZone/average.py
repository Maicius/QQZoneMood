import numpy as np
import pandas as pd
from json import JSONDecodeError

from QQZone.QQZoneAnalysis import QQZoneAnalysis
import json

class Average(object):

    """
    创建一个平均数类
    用于计算cmt_total_num、like_num、prd_num的均值
    """
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
        self.CMT_RESULT_NAMES = 'data/' + file_name_head + '_cmt_result_names.csv'
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

    def normalized_V(self):
        self.n_V = (self.V - min(self.V)) / (max(self.V) - min(self.V))
        if self.qqzone.debug:
            print("Self.nv:")
            print(self.n_V)

    def concat_n_V(self):
        self.df['n_V'] = self.n_V
        self.df.to_csv(self.N_V_FILE_NAME)

    def format_output(self):
        print("用户名：", self.qqzone.username)
        print("平均评论数量:", self.cmt_total_num_average)
        print("平均点赞数量:", self.like_num_average)
        print("平均浏览量:", self.prd_num_average)

    def calculate_cmt_rank(self):
        cmt_list = self.df['cmt_list']
        print(cmt_list.shape)
        cmt_list_csv = []
        wrong_count = 0
        for item in cmt_list.values:
            item1 = item.replace("\"", "\”")
            item2 = item1.replace("\'", "\"")
            # print(item2)
            try:
                json_item = json.loads(item2)
                cmt_list_csv.extend(json_item)
            except JSONDecodeError as e:
                item3 = item2.replace("\\xa0", "")
                try:
                    json_item = json.loads(item3)
                    cmt_list_csv.extend(json_item)
                except JSONDecodeError as e:
                    wrong_count +=1
                    print(e, item3)
                    pass
        print(wrong_count)
        cmt_df = pd.DataFrame(cmt_list_csv)
        print(cmt_df.shape)
        all_cmt_name_df = cmt_df['comment_name']
        cmt_names = cmt_df['comment_name'].drop_duplicates()
        cmt_result_csv = []
        for name in cmt_names:
            cmt_name_result = (all_cmt_name_df == name)
            cmt_times = cmt_name_result.sum()
            cmt_result_csv.append(dict(cmt_name=name, cmt_times=cmt_times))
        cmt_result_csv_df = pd.DataFrame(cmt_result_csv)
        cmt_result_csv_df.sort_values(by='cmt_times', inplace=True, ascending=False)
        cmt_result_csv_df.to_csv(self.CMT_RESULT_NAMES)

    def calculate_like_rank(self):
        pass

if __name__ == '__main__':
    av = Average(use_redis=True, debug=True, file_name_head="maicius")
    av.calculate_all()
    av.format_output()
    av.calculate_cmt_rank()