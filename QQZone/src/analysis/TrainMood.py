from QQZone.src.analysis import QQZoneAnalysis
import json
from QQZone.src.util.util import get_file_list, get_mktime2
import pandas as pd
import re
from QQZone.src.analysis import SentimentClassify


class TrainMood(QQZoneAnalysis):
    """
    生成各种训练需要的数据集
    """

    def __init__(self, use_redis=False, debug=True, file_name_head='maicius'):
        QQZoneAnalysis.__init__(self, use_redis=use_redis, debug=debug, file_name_head='maicius',
                                stop_time='2014-06-10',
                                stop_num=500, analysis_friend=False)
        self.IMAGE_SCORE_FILE_PATH = '/Users/maicius/code/nima.pytorch/nima/result_dict.json'
        self.MOOD_DATA_SCORE_FILE_NAME = '../data/train/' + file_name_head + '_score_mood_data.csv'
        self.RE_DO_SENTIMENT_FILE_NAME = '../data/train/' + file_name_head + '_re_do_mood_data.csv'
        self.TEXT_LABEL_TRAIN_DATA = '../data/train/' + file_name_head + '_mood_text.csv'
        self.TRAIN_DATA_AFTER_CLASSIFIC = '../data/train/' + file_name_head + '_mood_classific.csv'
        self.TEXT_LABEL_RESULT_TRAIN_DATA = '../data/train3/text_' + file_name_head + '_label.csv'
        self.TEXT_CLASSIFICATION_DATA_SET = '../data/train/'
        self.FINAL_RESULT_TRAIN_DATA = '../data/train/' + file_name_head + '_final_train.csv'
        self.mood_data_df = pd.read_csv(self.MOOD_DATA_FILE_NAME)
        self.IMAGE_OBJECT_FILE_NAME = '../data/train3/' + file_name_head + '_image_object.csv'
        self.MOOD_DATA_AFTER_OBJECT = '../data/train/' + file_name_head + '_after_object.csv'
        with open(self.IMAGE_SCORE_FILE_PATH, 'r', encoding='utf-8') as r:
            self.image_score_dict = json.load(r)
        self.sc = SentimentClassify()
        self.image_score_df = pd.DataFrame(self.image_score_dict)
        self.mood_data_df['score'] = '-1'
        self.image_dir = '/Users/maicius/code/InterestingCrawler/QQZone/qq_big_image/maicius/'
        self.image_file_list = get_file_list(self.image_dir)
        self.label_dict = {'1': '旅游与运动',
                           '2': '爱情与家庭',
                           '3': '学习与工作',
                           '4': '广告',
                           '5': '生活日常',
                           '6': '其他',
                           '7': '人生感悟'}
        self.label_dict_reverse = {v: k for k, v in self.label_dict.items()}

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
                self.mood_data_df.loc[self.mood_data_df.tid == tid, 'score'] = round(scores.mean(), 2)
        self.mood_data_df.fillna(mean_score)
        print("score shape:", self.mood_data_df.shape)
        # self.mood_data_df.to_csv(self.MOOD_DATA_SCORE_FILE_NAME)
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
        print('send time:', self.mood_data_df.shape)

    def export_df_after_clean(self):
        try:
            self.mood_data_df.drop(['Unnamed: 0'], axis=1, inplace=True)
        except BaseException as e:
            print(e)
        self.mood_data_df.to_csv(self.MOOD_DATA_SCORE_FILE_NAME)

    def export_train_text(self):
        train_text = pd.read_csv(self.label_path + 'result/' + 'final.csv')
        train_text = train_text[['type', 'content']]
        train_text.columns = ['Y', 'content']
        train_text.fillna('空', inplace=True)
        train_text.Y = train_text.Y.apply(lambda x: self.label_dict[str(int(x))])
        train_text.content = train_text.content.apply(lambda x: str(x).replace('\n', ''))
        train_text.content = train_text.content.apply(lambda x: str(x).replace(' ', ''))
        train_text.content = train_text.content.apply(lambda x: remove_waste_emoji(x))
        train_text.fillna('空', inplace=True)
        train_dataset = train_text.sample(frac=0.8)
        val_dataset = train_text.sample(frac=0.3)
        test_dataset = train_text.sample(frac=0.3)

        self.print_label_dict(train_text)
        self.print_label_dict(train_dataset)
        self.print_label_dict(val_dataset)
        self.print_label_dict(test_dataset)

        train_dataset.to_csv(self.TEXT_CLASSIFICATION_DATA_SET + 'text_train.csv', sep='\t', index=None, header=None)
        val_dataset.to_csv(self.TEXT_CLASSIFICATION_DATA_SET + 'text_val.csv', sep='\t', index=None, header=None)
        test_dataset.to_csv(self.TEXT_CLASSIFICATION_DATA_SET + 'text_test.csv', sep='\t', index=None, header=None)
        self.calculate_avg_length(train_text)
        # train_text.to_csv(self.TEXT_LABEL_TRAIN_DATA, sep=' ', index=None, header=None)

    def calculate_avg_length(self, data_df):
        num = data_df.shape[0]
        content_list = data_df.content.sum()
        print(len(content_list) / num)

    def calculate_sentiment(self):
        print("Begin to calculate sentiment...")
        self.mood_data_df.content = self.mood_data_df.content.apply(lambda x: str(x).replace('\n', ''))
        self.mood_data_df.content = self.mood_data_df.content.apply(lambda x: str(x).replace(' ', ''))
        self.mood_data_df.content = self.mood_data_df.content.apply(lambda x: remove_waste_emoji(str(x)))
        # 使用apply会导致超过qps限额
        # sentiments = self.mood_data_df['content'].apply(lambda x: self.sc.get_sentiment_for_text(x))
        # self.mood_data_df['sentiment'] = sentiments
        self.mood_data_df['sentiments'] = -1
        for i in range(self.mood_data_df.shape[0]):
            content = self.mood_data_df.loc[i, 'content']
            sentiment = self.sc.get_sentiment_for_text(content)
            print('content:', content, 'senti:', sentiment)
            self.mood_data_df.loc[i, 'sentiments'] = sentiment

        self.mood_data_df = self.re_do_sentiment(self.mood_data_df)
        try:
            self.mood_data_df.drop(['Unnamed: 0'], axis=1, inplace=True)
        except BaseException as e:
            print(e)
        self.mood_data_df.to_csv('after_sentiment.csv')
        print("text sentiment:", self.mood_data_df.shape)

    def print_label_dict(self, data_df):
        for item in self.label_dict.values():
            print(item, data_df.loc[data_df.Y == item, :].shape[0])
        print('==========')

    def re_do_sentiment(self, data_df):
        # data_df = pd.read_csv(self.MOOD_DATA_SCORE_FILE_NAME)
        for i in range(data_df.shape[0]):
            sentiment = data_df.loc[i, 'sentiments']
            content = data_df.loc[i, 'content']
            if sentiment == -1:
                content = content.replace('\u2207', '')
                content = content.replace('\ue40c', '')
                content = content.replace('\ue412', '')
                content = content.replace('\ue056', '')
                sentiment = self.sc.get_sentiment_for_text(str(content))
                data_df.loc[i, 'sentiments'] = sentiment
        data_df.to_csv(self.RE_DO_SENTIMENT_FILE_NAME)
        return data_df

    def export_classification_data(self):
        """
        导出待分类待的数据
        :return:
        """
        data = pd.read_csv(self.RE_DO_SENTIMENT_FILE_NAME)
        data_df = data[['content']]
        data_df['Y'] = '旅游与运动'
        data_df.fillna('空', inplace=True)
        columns = ['Y', 'content']
        data_df = data_df.ix[:, columns]
        print(data_df.shape)
        data_df.to_csv(self.TEXT_CLASSIFICATION_DATA_SET + 'text_maicius.csv', sep='\t')

    def combine_text_type_data(self):
        data = pd.read_csv(self.MOOD_DATA_SCORE_FILE_NAME)
        print('mood_after_object_data:', data.shape)
        label = pd.read_csv(self.TEXT_LABEL_RESULT_TRAIN_DATA)
        print('label data:', label.shape)
        label_y = label['Y']
        data['type'] = label_y
        data.to_csv(self.TRAIN_DATA_AFTER_CLASSIFIC)

    def attach_image_object_for_each_mood(self):
        with open('qq_big_image.json', 'r', encoding='utf-8') as r:
            data = json.load(r)

        with open('category.json', 'r', encoding='utf-8') as r:
            category = json.load(r)

        category_df = pd.DataFrame(category)
        image_object_df = pd.DataFrame(
            columns=['tid', 'person', 'vehicle', 'outdoor', 'animal', 'accessory', 'sports', 'kitchen', 'food',
                     'furniture',
                     'electronic', 'appliance', 'indoor'])
        i = 0
        for key, value in data.items():
            tid = key.split('--')[0].split('/')[-1]
            if image_object_df.loc[image_object_df.tid == tid].shape[0] == 0:
                image_object_df.loc[i, 'tid'] = tid
                i +=1
            for item in value:
                item = item.split(' ')[0]
                super_cate = category_df.loc[category_df.name.str.contains(item), 'supercategory']
                if len(super_cate) > 0:
                    print(super_cate)
                    image_object_df.loc[image_object_df.tid == tid, super_cate.values[0]] = 1
        image_object_df.fillna(0, inplace=True)
        image_object_df['vector'] = 0
        image_object_df['vector'] = image_object_df['tid'].apply(lambda x: image_object_df.loc[image_object_df.tid == x,'person':].values[0])
        image_object_df.to_csv(self.IMAGE_OBJECT_FILE_NAME)

    def combine_image_object(self):
        image_object_df = pd.read_csv(self.IMAGE_OBJECT_FILE_NAME)
        mood_data_df = pd.read_csv(self.TRAIN_DATA_AFTER_CLASSIFIC)
        try:
            mood_data_df.drop(['vector'], axis=1, inplace=True)
        except BaseException as e:
            print(e)
        image_object = image_object_df[['tid', 'vector']]
        print(image_object_df.shape, mood_data_df.shape)
        result = pd.merge(mood_data_df, image_object, on='tid', how='left')
        print(result.shape)
        result.to_csv(self.MOOD_DATA_AFTER_OBJECT)

    def export_final_train_data(self):
        data = pd.read_csv(self.MOOD_DATA_AFTER_OBJECT)
        train = data[['n_E', 'score', 'time_state', 'sentiments', 'type', 'vector']]
        train = train.loc[6:, :]
        self.mean_score = self.image_score_df[self.image_score_df['score'] != -1].mean()[0]
        train.score = train['score'].apply(lambda x: self.change_neg_image_score(x))
        train.type = train['type'].map(self.label_dict_reverse)
        train.vector.fillna('[0 0 0 0 0 0 0 0 0 0 0 0 0]', inplace=True)
        train.vector = train.vector.apply(lambda x: self.change_vector_to_int(x))
        train.sort_values(by='n_E', inplace=True, ascending=False)
        train.to_csv(self.FINAL_RESULT_TRAIN_DATA)

    def change_neg_image_score(self, score):
        if score == -1:
            return self.mean_score
        else:
            return score

    def change_vector_to_int(self, vector):
        vector = re.findall(re.compile('[0-9]'), vector)
        str_vector = "".join(vector)
        sum = 0
        length = len(str_vector)
        for i in range(length):
            sum += int(str_vector[i]) **(length - 1)
        return sum


def remove_waste_emoji(text):
    text = re.subn(re.compile('\[em\].*?\[\/em\]'), '', text)[0]
    text = re.subn(re.compile('@\{.*?\}'), '', text)[0]
    return text


if __name__ == '__main__':
    train = TrainMood(use_redis=True, debug=True, file_name_head='maicius')
    # train.calculate_score_for_each_mood()
    # train.calculate_send_time()
    # train.calculate_sentiment()
    # train.export_df_after_clean()
    train.export_train_text()
    # train.export_classification_data()
    # train.attach_image_object_for_each_mood()

    # train.combine_text_type_data()
    # train.combine_image_object()
    # train.export_final_train_data()
