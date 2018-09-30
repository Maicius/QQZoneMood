import redis
from QQZone import Spider
import re
import json
import pandas as pd


class QQZoneAnalysis(Spider):
    def __init__(self, use_redis=False, debug=False, file_name_head=''):
        Spider.__init__(self, use_redis, debug, file_name_head)
        self.mood_data = []
        self.MOOD_DATA_FILE_NAME = 'data/' + file_name_head + '_mood_data.csv'

    def load_file_from_redis(self):
        self.do_recover_from_exist_data()

    def  check_data_shape(self):
        if len(self.mood_details) == len(self.like_list_names) == len(self.like_detail):
            return True
        else:
            print(len(self.mood_details), len(self.like_list_names), len(self.like_detail))
            return False

    def save_data_to_csv(self):
        self.mood_data_df = pd.DataFrame(self.mood_data)
        self.mood_data_df.to_csv(self.MOOD_DATA_FILE_NAME)

    def get_useful_info_from_json(self):
        self.load_file_from_redis()
        for i in range(len(self.mood_details)):
            total_num, uin_list = self.parse_like_names(self.like_list_names[i])
            key, like_num, prd_num = self.parse_like_and_prd(self.like_detail[i])
            if total_num != like_num:
                print('点赞数据有丢失:', total_num, like_num)
            like_num = max(total_num, like_num)
            self.parse_mood_detail(self.mood_details[i], key=key, uin_list=uin_list, like_num=like_num, prd_num=prd_num)

    def parse_mood_detail(self, mood, key, uin_list, like_num, prd_num):
        msglist = json.loads(mood)
        tid = msglist['tid']
        if key == tid:
            print('Correct')
        else:
            print('Wrong tid and key:', tid, key)
        content = msglist['content']
        time = msglist['createTime']
        time_stamp = msglist['created_time']
        secret = msglist['secret']
        if 'pictotal' in msglist:
            pic_num = msglist['pictotal']
        else:
            pic_num = 0
        cmt_num = msglist['cmtnum']
        cmt_list = []
        cmt_total_num = cmt_num
        if 'commentlist' in msglist:
            comment_list = msglist['commentlist']

            for comment in comment_list:
                comment_content = comment['content']
                comment_name = comment['name']
                comment_time = comment['createTime2']
                comment_reply_num = comment['replyNum']
                cmt_total_num += comment_reply_num
                comment_reply_list = []
                if comment_reply_num > 0:
                    for comment_reply in comment['list_3']:
                        comment_reply_content = comment_reply['content']
                        # 去掉 @{uin:117557,nick:16,who:1,auto:1} 这种文字
                        comment_reply_content = re.subn(re.compile('\@\{.*?\}'), '', comment_reply_content)[0].strip()
                        comment_reply_name = comment_reply['name']
                        comment_reply_time = comment_reply['createTime2']
                        comment_reply_list.append(dict(comment_reply_content=comment_reply_content,
                                                       comment_reply_name=comment_reply_name,
                                                       comment_reply_time=comment_reply_time))
                cmt_list.append(
                    dict(comment_content=comment_content, comment_name=comment_name, comment_time=comment_time,
                         comment_reply_num=comment_reply_num, comment_reply_list=comment_reply_list))


        self.mood_data.append(dict(tid=tid, content=content, time=time, time_stamp=time_stamp, pic_num=pic_num,
                                   cmt_num=cmt_num, like_num=like_num, prd_num=prd_num, uin_list=uin_list, cmt_total_num=cmt_total_num,
                                   cmt_list=cmt_list, secret=secret))

    def parse_like_and_prd(self, like):
        try:
            data = json.loads(like)['data'][0]
            current = data['current']
            key = current['key'].split('/')[-1]
            newdata = current['newdata']
            # 点赞数
            if 'LIKE' in newdata:
                like_num = newdata['LIKE']
                # 浏览数
                prd_num = newdata['PRD']
                return key, like_num, prd_num
            else:
                return key, 0, 0
        except BaseException as e:
            print(like)
            self.format_error(e, 'Error in like, return 0')
            return 0, 0, 0


    def parse_like_names(self, like):
        data = json.loads(like)['data']
        total_num = data['total_number']
        like_uin_info = data['like_uin_info']
        uin_list = []
        for uin in like_uin_info:
            nick = uin['nick']
            gender = uin['gender']
            uin_list.append(dict(nick=nick, gender=gender))
        return total_num, uin_list


if __name__ == '__main__':
    analysis = QQZoneAnalysis(use_redis=True, debug=False, file_name_head='maicius')
    print(analysis.check_data_shape())
    analysis.get_useful_info_from_json()
    analysis.save_data_to_csv()
