import numpy as np
import pandas as pd
class Average(object):
    """创建一个平均数类"，用于计算cmt_total_num、like_num、prd_num的均值"""
    def __init__(self):
        df = pd.DataFrame(pd.read_csv('maicius_mood_data.csv'), columns=['cmt_list', 'cmt_num', 'cmt_total_num', 'content', 'friend_num', 'like_num', 'pic_num', 'prd_num', 'tid', 'time', 'time_stamp'])
        self.cmt_total_num_average=df['cmt_total_num'].mean()
        self.like_num_average=df['like_num'].mean()
        self.prd_num_average=df['prd_num'].mean()
        self.df=df
    def calculate_E(self,i):
        """计算某一条动态的热度，并用E表示"""
        m=self.df[i,2]##第i条动态的评论数
        n=self.df[i,5]##第i条动态的点赞数
        h=self.df[i,7]##第i条动态的浏览数
        a=self.like_num_average/self.cmt_total_num_average##平均点赞量与平均评论量的比值
        b=self.prd_num_average/self.like_num_average##平均浏览量与平均点赞量的比值
        E=m*a*b+n*b+h##计算热度
        return E
