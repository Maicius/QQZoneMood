import re
import json
import pandas as pd
import jieba
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
from PIL import Image
import matplotlib.pyplot as plt
from src.spider.QQZoneFriendMoodSpider import QQZoneFriendMoodSpider
from src.analysis.Average import Average
from src.util.constant import BASE_DIR, SYSTEM_FONT, EXPIRE_TIME_IN_SECONDS
from src.util.util import get_standard_time_from_mktime2
import numpy as np
import time

class QQZoneAnalysis(QQZoneFriendMoodSpider):
    def __init__(self, use_redis=False, debug=False, username='', analysis_friend=False, mood_begin=0, mood_num=-1,
                 stop_time='-1', from_web=False, nickname='', no_delete=True, cookie_text='', pool_flag='127.0.0.1', exprot_excel=True, export_csv=False):
        """

        :param use_redis:
        :param debug:
        :param username:
        :param analysis_friend: 是否要分析好友数据（比如最早的好友、共同好友数量最多的好友），如果要分析该类指标，必须已经获取了好友数据
        :param mood_begin:
        :param mood_num:
        :param stop_time:
        :param from_web:
        :param nickname:
        :param no_delete:
        :param cookie_text:
        :param pool_flag:
        :param exprot_excel:
        :param export_csv:
        """
        QQZoneFriendMoodSpider.__init__(self, use_redis=use_redis, debug=debug, recover=False, username=username, mood_num=mood_num,
                              mood_begin=mood_begin, stop_time=stop_time, from_web=from_web, nickname=nickname,
                              no_delete=no_delete, cookie_text=cookie_text, analysis=True, export_excel=exprot_excel, export_csv=export_csv, pool_flag=pool_flag)
        self.mood_data = []
        self.mood_data_df = pd.DataFrame()
        self.like_detail_df = []
        self.like_list_names_df = []
        self.analysis_friend = analysis_friend
        self.has_clean_data = False
        self.cmt_df = None
        self.like_uin_df = None
        self.av = Average(use_redis=False, file_name_head=username, analysis=True, debug=debug)
        self.cmt_friend_set = set()
        # 用于绘制词云图的字体，请更改为自己电脑上任意一款支持中文的字体，否则将无法显示中文
        self.system_font = SYSTEM_FONT


    def load_file_from_redis(self):
        self.do_recover_from_exist_data()

    def save_data_to_csv(self):
        pd.DataFrame(self.mood_data_df).to_csv(self.MOOD_DATA_FILE_NAME)

    def save_data_to_excel(self):
        pd.DataFrame(self.mood_data_df).to_excel(self.MOOD_DATA_EXCEL_FILE_NAME)

    def load_mood_data(self):
        try:
            self.mood_data_df = pd.read_csv(self.MOOD_DATA_FILE_NAME)
            self.mood_data_df['uin_list'] = self.mood_data_df['uin_list'].apply(
                lambda x: json.loads(x.replace('\'', '\"')))
        except:
            try:
                self.mood_data_df = pd.read_excel(self.MOOD_DATA_EXCEL_FILE_NAME)
                self.mood_data_df['uin_list'] = self.mood_data_df['uin_list'].apply(
                    lambda x: json.loads(x.replace('\'', '\"')))
            except BaseException as e:
                print("加载mood_data_df失败，开始重新清洗数据")
                self.get_useful_info_from_json()

    def get_useful_info_from_json(self):
        """
        从原始动态数据中清洗出有用的信息
        结果存储在self.mood_data_df中
        :return:
        """

        self.load_file_from_redis()
        for i in range(len(self.mood_details)):
            self.parse_mood_detail(self.mood_details[i])

        for i in range(len(self.like_list_names)):
            self.parse_like_names(self.like_list_names[i])

        for i in range(len(self.like_detail)):
            self.parse_like_and_prd(self.like_detail[i])

        mood_data_df = pd.DataFrame(self.mood_data)
        like_detail_df = pd.DataFrame(self.like_detail_df)
        like_list_df = pd.DataFrame(self.like_list_names_df)
        if mood_data_df.empty:
            self.has_clean_data = True
            print("该用户没有数据或无访问权限")
            return
        data_df = pd.merge(left=mood_data_df, right=like_detail_df, how='inner', left_on='tid', right_on='tid')
        data_df = pd.merge(left=data_df, right=like_list_df, how='inner', left_on='tid', right_on='tid')

        data_df = data_df.sort_values(by='time_stamp', ascending=False).reset_index()

        data_df.drop(['total_num', 'index'], axis=1, inplace=True)
        # data_df.drop_duplicate()
        try:
            n_E = self.av.calculate_E(data_df)
            max_n_E = max(n_E)
            data_df['n_E'] = n_E
            data_df['user'] = self.username

            self.mood_data_df = data_df
            data_df = data_df.sort_values(by='n_E', ascending=False)
            date = data_df['time'].values[0]
            # date = self.mood_data_df.loc[self.mood_data_df.n_E == max_n_E, 'time'].values[0]
            # 计算熵最高的日期
            self.user_info.most_date = date
        except:
            self.user_info.most_date = ''
        finally:
            self.has_clean_data = True

    def calculate_send_time(self):
        """
        计算每条说说的发送时间
        分为以下五种类型：
        0.0点-3点
        1.3-6
        2.6点-9点
        3.9-12
        4.12点-15
        5.15-18
        6.18-21
        7.21-24
        :return:
        """
        if self.friend_df is None:
            self.friend_df = pd.read_csv(self.FRIEND_DETAIL_LIST_FILE_NAME)
        if not self.has_clean_data:
            self.get_useful_info_from_json()
        try:
            day_begin_time = self.mood_data_df['time_stamp'].apply(lambda x: get_standard_time_from_mktime2(x))
            day_time_stamp = self.mood_data_df['time_stamp']
            time_diff = day_time_stamp - day_begin_time
            # 3个小时的时间差
            time_step = 60 * 60 * 3
            time_state = time_diff.apply(lambda x: x // time_step)
            time_state_df = pd.DataFrame(time_state)
            time_state_df['count'] = 1

            time_state_df = time_state_df.groupby(by='time_stamp').sum().reset_index()
            temp = max(time_state_df['count'].values)
            most_state = time_state_df.loc[time_state_df['count'] == temp, 'time_stamp'].values[0]
            # 判断是否是夜猫子
            is_night = (time_state_df.loc[time_state_df['time_stamp'] == 0, 'count'].values[0] / time_state_df['count'].sum()) > 0.1
            self.mood_data_df['time_state'] = time_state
            self.time_step_df = pd.DataFrame(time_state)
            if self.debug:
                print('send time:', self.mood_data_df.shape)
            self.user_info.most_time_state = most_state
            self.user_info.is_night = int(is_night)
        except BaseException as e:
            self.format_error(e, "Failed to analysis sedn mood time")
            self.user_info.most_time_state = 0
            self.user_info.is_night = 0


    def parse_mood_detail(self, mood):
        try:
            msglist = json.loads(mood)
        except BaseException:
            msglist = mood
        tid = msglist['tid']
        try:
            secret = msglist['secret']
            # 过滤私密说说
            if secret:
                pass
            else:
                content = msglist['content']
                time = msglist['createTime']
                time_stamp = msglist['created_time']

                if 'pictotal' in msglist:
                    pic_num = msglist['pictotal']
                else:
                    pic_num = 0
                cmt_num = msglist['cmtnum']
                cmt_list = []
                cmt_total_num = cmt_num
                if 'commentlist' in msglist:
                    comment_list = msglist['commentlist'] if msglist['commentlist'] is not None else []

                    for i in range(len(comment_list)):
                        try:
                            comment = comment_list[i]
                            comment_content = comment['content']
                            if i < 20:
                                comment_name = comment['name']
                                comment_time = comment['createTime2']
                                comment_reply_num = comment['replyNum']
                                comment_reply_list = []
                                if comment_reply_num > 0:
                                    for comment_reply in comment['list_3']:
                                        comment_reply_content = comment_reply['content']
                                        # 去掉 @{uin:117557,nick:16,who:1,auto:1} 这种文字
                                        comment_reply_content = \
                                            re.subn(re.compile('\@\{.*?\}'), '', comment_reply_content)[
                                                0].strip()
                                        comment_reply_name = comment_reply['name']
                                        comment_reply_time = comment_reply['createTime2']
                                        comment_reply_list.append(dict(comment_reply_content=comment_reply_content,
                                                                       comment_reply_name=comment_reply_name,
                                                                       comment_reply_time=comment_reply_time))
                            else:
                                comment_name = comment['poster']['name']
                                comment_time = comment['postTime']
                                comment_reply_num = comment['extendData']['replyNum']
                                comment_reply_list = []
                                if comment_reply_num > 0:
                                    for comment_reply in comment['replies']:
                                        comment_reply_content = comment_reply['content']
                                        # 去掉 @{uin:117557,nick:16,who:1,auto:1} 这种文字
                                        comment_reply_content = \
                                            re.subn(re.compile('\@\{.*?\}'), '', comment_reply_content)[
                                                0].strip()
                                        comment_reply_name = comment_reply['poster']['name']
                                        comment_reply_time = comment_reply['postTime']
                                        comment_reply_list.append(dict(comment_reply_content=comment_reply_content,
                                                                       comment_reply_name=comment_reply_name,
                                                                       comment_reply_time=comment_reply_time))

                            cmt_total_num += comment_reply_num
                            cmt_list.append(
                                dict(comment_content=comment_content, comment_name=comment_name,
                                     comment_time=comment_time,
                                     comment_reply_num=comment_reply_num, comment_reply_list=comment_reply_list))
                        except BaseException as e:
                            self.format_error(e, comment)

                if self.analysis_friend:
                    try:
                        if self.friend_df.empty:
                            self.friend_df = pd.read_csv(self.FRIEND_DETAIL_LIST_FILE_NAME)
                        friend_num = self.calculate_friend_num_timeline(time_stamp, self.friend_df)

                    except BaseException as e:
                        print("暂无好友数据，请先运行QQZoneFriendSpider")
                        friend_num = -1

                else:
                    friend_num = -1
                self.mood_data.append(dict(tid=tid, content=content, time=time, time_stamp=time_stamp, pic_num=pic_num,
                                           cmt_num=cmt_num,
                                           cmt_total_num=cmt_total_num,
                                           cmt_list=cmt_list, friend_num=friend_num))
        except BaseException as e:
            self.format_error(e, "Error in parse mood:" + str(msglist))
            self.mood_data.append(dict(tid=tid, content=msglist['message'], time="", time_stamp="", pic_num=0,
                                       cmt_num=0,
                                       cmt_total_num=0,
                                       cmt_list=[], friend_num=-1))

    def parse_like_and_prd(self, like):
        try:
            data = like['data'][0]
            current = data['current']
            key = current['key'].split('/')[-1]
            newdata = current['newdata']
            # 点赞数
            if 'LIKE' in newdata:
                like_num = newdata['LIKE']
                # 浏览数
                prd_num = newdata['PRD']

                if self.debug:
                    if key == like['tid']:
                        print("correct like tid")
                    else:
                        print("wrong like tid")
                self.like_detail_df.append(dict(tid=like['tid'], like_num=like_num, prd_num=prd_num))
            else:
                self.like_detail_df.append(dict(tid=like['tid'], like_num=0, prd_num=0))
        except BaseException as e:
            print(like)
            self.format_error(e, 'Error in like, return 0')
            self.like_detail_df.append(dict(tid=like['tid'], like_num=0, prd_num=0))

    def parse_like_names(self, like):
        try:
            data = like['data']
            total_num = data['total_number']
            like_uin_info = data['like_uin_info']
            uin_list = []

            for uin in like_uin_info:
                nick = uin['nick']
                gender = uin['gender']
                uin_list.append(dict(nick=nick, gender=gender))
            self.like_list_names_df.append(dict(total_num=total_num, uin_list=uin_list, tid=like['tid']))
        except BaseException as e:
            self.format_error(e, "Error in parse like names")
            self.like_list_names_df.append(dict(total_num=0, uin_list=[], tid=like['tid']))

    def drawWordCloud(self, word_text, filename, dict_type=False, background_image='image/tom2.jpeg'):
        """

        :param word_text:
        :param filename:
        :param dict_type:
        :param background_image: 词云图的背景形状
        :return:
        """
        mask = Image.open(BASE_DIR + background_image)
        mask = np.array(mask)
        my_wordcloud = WordCloud(
            background_color='white',  # 设置背景颜色
            mask=mask,  # 设置背景图片
            max_words=2000,  # 设置最大现实的字数
            stopwords=STOPWORDS,  # 设置停用词
            font_path=self.system_font,  # 设置字体格式，如不设置显示不了中文
            max_font_size=50,  # 设置字体最大值
            random_state=30,  # 设置有多少种随机生成状态，即有多少种配色方案
            scale=1.3
        )
        if not dict_type:
            my_wordcloud = my_wordcloud.generate(word_text)
        else:
            my_wordcloud = my_wordcloud.fit_words(word_text)
        image_colors = ImageColorGenerator(mask)
        my_wordcloud.recolor(color_func=image_colors)
        # 以下代码显示图片
        plt.imshow(my_wordcloud)
        plt.axis("off")
        # 保存图片
        if not self.from_web:
            my_wordcloud.to_file(filename=self.image_path + filename + '.jpg')
            print("result file path:", self.image_path + filename + '.jpg')
            plt.show()
        else:
            my_wordcloud.to_file(filename=self.web_image_bash_path + filename + '.jpg')
            print("result file path:", self.web_image_bash_path + filename + '.jpg')

    def get_jieba_words(self, content):
        word_list = jieba.cut(content, cut_all=False)
        word_list2 = []
        with open(BASE_DIR + '中文停用词库.txt', 'r', encoding='gbk') as r:
            waste_words = r.readlines()
        waste_words = list(map(lambda x: x.strip(), waste_words))
        waste_words.extend(['uin', 'nick'])
        waste_words = set(waste_words)
        for word in word_list:
            if len(word) >= 2 and word.find('e') == -1 and word not in waste_words:
                word_list2.append(word)
        words_text = " ".join(word_list2)
        return words_text

    def draw_content_cloud(self, df):
        content = df['content'].sum()
        words = self.get_jieba_words(content)
        self.drawWordCloud(words, self.username + '_content')

    def draw_cmt_cloud(self, df):
        cmt_df = self.av.calculate_cmt_rank(df)
        if not cmt_df.empty:
            cmt_dict = {x[0]: x[1] for x in cmt_df.values}
            self.drawWordCloud(cmt_dict, self.username + '_cmt', dict_type=True)

    def rank_like_people(self, df):
        uin_list = df['uin_list']
        all_uin_list = []
        for item in uin_list:
            all_uin_list.extend(item)
        if len(all_uin_list) > 0:
            all_uin_df = pd.DataFrame(all_uin_list)
            all_uin_count = all_uin_df.groupby(['nick']).count().reset_index()
            return all_uin_count
        else:
            return pd.DataFrame()

    def draw_like_cloud(self, df):
        all_uin_count = self.rank_like_people(df)
        if not all_uin_count.empty:
            all_uin_dict = {str(x[0]): x[1] for x in all_uin_count.values}
            self.drawWordCloud(all_uin_dict, self.username + '_like', dict_type=True)

    def get_non_activate_friend(self):
        """
        计算曾经很活跃但是现在不活跃的好友
        :return:
        """
        # 获取当前的秒级时间戳
        now_time = time.time()
        last_year_time = now_time - 60 * 60 * 24 * 365
        recent_year_df = self.mood_data_df[self.mood_data_df['time_stamp'] > last_year_time]
        if not recent_year_df.empty:
            recent_like_df = self.rank_like_people(recent_year_df)
            recent_friend_set = set(recent_like_df['nick'].values)
            self.user_info.non_activate_friend_num = len(self.cmt_friend_set - recent_friend_set)
        newest_time = self.mood_data_df.head(1)['time_stamp'].values[0]

        self.user_info.non_activate_time = int((now_time - newest_time) / (24 * 3600))

        pass

    def export_mood_df(self, export_csv=True, export_excel=True):
        """
        根据传入的文件名前缀清洗原始数据，导出csv和excel表
        :param file_name_head:
        :param export_csv:
        :param export_excel:
        :return:
        """
        if not self.has_clean_data:
            self.get_useful_info_from_json()
        if export_csv:
            self.save_data_to_csv()
        if export_excel:
            self.save_data_to_excel()
        print("保存清洗后的数据成功", self.username)

    def get_most_people(self):
        """
        计算点赞和评论最多的好友
        :return:
        """
        if not self.has_clean_data:
            self.get_useful_info_from_json()
        # 取得点赞的人的数据
        all_uin_count = self.rank_like_people(self.mood_data_df)
        if not all_uin_count.empty:
            all_uin_count = all_uin_count.sort_values(by="gender", ascending=False).reset_index()
            most_like_name = all_uin_count.loc[0, 'nick']
            self.user_info.total_like_num = int(all_uin_count['gender'].sum())
            all_uin_count.columns = ['index', 'name', 'value']
            self.user_info.total_like_list = json.loads(all_uin_count.head(5)[['name', 'value']].to_json(orient="records"))
            like_friend_set = set(all_uin_count['name'].values)
            self.user_info.like_friend_name = most_like_name
        else:
            self.user_info.like_friend_name = ''

        # 取得评论的人的数据
        cmt_df = self.av.calculate_cmt_rank(self.mood_data_df).reset_index()

        if not cmt_df.empty:
            self.user_info.total_cmt_num = int(cmt_df['cmt_times'].sum())
            self.user_info.cmt_friend_num = cmt_df.shape[0]
            most_cmt_name = cmt_df.loc[0, 'cmt_name']
            cmt_friend_set = set(cmt_df['cmt_name'].values)
            self.user_info.cmt_friend_name = most_cmt_name
            self.cmt_friend_set = cmt_friend_set
            try:
                self.user_info.like_friend_num = len(like_friend_set - cmt_friend_set)
            except:
                self.logging.error("获取只点赞的好友数量失败")
        else:
            self.user_info.cmt_friend_name = ''
        self.get_non_activate_friend()



    def calculate_history_like_agree(self):
        """
        计算历史上每条说说的内容、点赞量和评论量
        :return:
        """
        if not self.has_clean_data:
            self.get_useful_info_from_json()
        history_df = self.mood_data_df.loc[:, ['cmt_total_num', 'like_num', 'content', 'time']]
        history_json = history_df.to_json(orient='records', force_ascii=False)
        if self.use_redis:
            self.re.set(self.history_like_agree_file_name, json.dumps(history_json, ensure_ascii=False))
            if not self.no_delete:
                self.re.expire(self.history_like_agree_file_name, EXPIRE_TIME_IN_SECONDS)
        else:
            self.save_data_to_json(history_json, self.history_like_agree_file_name)

def clean_label_data():
    new_list = ['maicius']
    for name in new_list:
        print(name + '====================')
        analysis = QQZoneAnalysis(use_redis=True, debug=True, username=name, analysis_friend=False)
        # print(analysis.check_data_shape())
        analysis.get_useful_info_from_json()
        analysis.save_data_to_csv()
        # analysis.save_data_to_excel()
        # analysis.export_label_data(analysis.mood_data_df)
        # analysis.draw_content_cloud(analysis.mood_data_df)
        # analysis.draw_cmt_cloud(analysis.mood_data_df)
        analysis.draw_like_cloud(analysis.mood_data_df)
        # analysis.export_all_label_data()

def get_most_people(username):
    analysis = QQZoneAnalysis(use_redis=True, debug=True, username=username, analysis_friend=False, from_web=True)
    analysis.get_most_people()

def export_mood_df(username):
    analysis = QQZoneAnalysis(use_redis=True, debug=True, username=username, analysis_friend=False, from_web=True)
    analysis.export_mood_df()


if __name__ == '__main__':
    export_mood_df("1272082503")
    get_most_people("1272082503")
    # clean_label_data()
