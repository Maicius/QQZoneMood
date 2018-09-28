import redis
from QQZone import Spider
import re


class QQZoneAnalysis(Spider):
    def __init__(self, use_redis=False, debug=False, file_name_head=''):
        Spider.__init__(self, use_redis, debug, file_name_head)
        self.mood_data = {}

    def load_file_from_redis(self):
        self.do_recover_from_exist_data()

    def get_useful_info_from_json(self):
        self.load_file_from_redis()
        for mood in self.mood_details:
            msglist = mood['msglist']
            tid = msglist['tid']
            content = msglist['content']
            time = msglist['createTime']
            time_stamp = msglist['created_time']
            pic_num = len(msglist['pictotal'])
            cmt_num = msglist['cmtnum']
            cmt_list = []
            if 'commentlist' in msglist:
                comment_list = msglist['commentlist']
                for comment in comment_list:
                    comment_content = comment['content']
                    comment_name = comment['name']
                    comment_time = comment['createTime2']
                    comment_reply_num = comment['reply_num']
                    comment_reply_list = []
                    if comment_reply_num > 0:

                        for comment_reply in comment['list_3']:
                            comment_reply_content = comment_reply['content']
                            # 去掉 @{uin:117557,nick:16,who:1,auto:1} 这种文字
                            comment_reply_content = re.subn(re.compile('\@\{.*\} '), '', comment_reply_content)[0]
                            comment_reply_name = comment_reply['name']
                            comment_reply_time = comment_reply['createTime2']
                            comment_reply_list.append(dict(comment_reply_content=comment_reply_content,
                                                           comment_reply_name=comment_reply_name,
                                                           comment_reply_time=comment_reply_time))
                    cmt_list.append(
                        dict(comment_content=comment_content, comment_name=comment_name, comment_time=comment_time,
                             comment_reply_num=comment_reply_num, comment_reply_list=comment_reply_list))

            # 这里以tid为key构建dict，是为了方便后面根据tid添加图片、点赞数量等数据
            self.mood_data[tid] = dict(tid=tid, content=content, time=time, time_stamp=time_stamp, pic_num=pic_num,
                                       cmt_num=cmt_num, cmt_list=cmt_list)
            print(tid)
            pass
        pass


if __name__ == '__main__':
    analysis = QQZoneAnalysis(use_redis=True, debug=False, file_name_head='maicius')
    analysis.get_useful_info_from_json()

