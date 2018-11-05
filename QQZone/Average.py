import numpy as np
import pandas as pd
from json import JSONDecodeError
import json

class Average(object):

    """
    创建一个平均数类
    用于计算cmt_total_num、like_num、prd_num的均值
    """
    def __init__(self, use_redis=False, debug=True, file_name_head="", filename="", analysis = False):
        """

        :param use_redis:
        :param debug:
        :param file_name_head:
        :param filename:
        :param filename_list:
        """
        self.debug = debug
        self.df = None
        self.filename = filename
        self.file_name_head = file_name_head
        self.N_E_FILE_NAME = 'data/result/' + file_name_head + '_n_E_mood_data.csv'
        self.CMT_RESULT_NAMES = 'data/result/' + file_name_head + '_cmt_result_names.csv'
        if self.filename == '' and self.file_name_head != '':
            self.filename = 'data/' + file_name_head + '_mood_data.csv'

        if not analysis:
            self.read_data_from_csv()

    def read_data_from_csv(self):
        if self.filename == "":
            self.format_error("文件名不能为空")
            exit(1)
        else:
            data_df = pd.DataFrame(pd.read_csv(self.filename))
        if self.debug:
            print("data df shape:", data_df.shape)
        self.df = data_df

    def calculate_E(self, df):
        """
        根据传入的df获取e值
        :param df:
        :return:
        """
        self.cmt_total_num_average = df['cmt_total_num'].mean()
        self.like_num_average = df['like_num'].mean()
        self.prd_num_average = df['prd_num'].mean()
        a = self.like_num_average / self.cmt_total_num_average  ##平均点赞量与平均评论量的比值
        b = self.prd_num_average / self.like_num_average  ##平均浏览量与平均点赞量的比值
        m = df['cmt_total_num']
        n = df['like_num']
        h = df['prd_num']
        self.E = m * a * b + n * b + h
        self.normalized_E()
        return self.n_E

    def format_error(self, e, msg=""):
        print('ERROR===================')
        print(e)
        print(msg)
        print('ERROR===================')
        if self.debug:
            # raise e
            pass

    def normalized_E(self):
        self.n_E = (self.E - min(self.E)) / (max(self.E) - min(self.E))
        if self.debug:
            print("Self.nv:")
            print(self.n_E)

    def concat_n_E(self):
        self.df['n_E'] = self.n_E
        self.df.to_csv(self.N_E_FILE_NAME)

    def format_output(self):
        print("用户名：", self.filename)
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
    av.calculate_E(av.df)
    av.format_output()
    av.calculate_cmt_rank()