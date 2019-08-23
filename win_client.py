import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
from src.spider.QQZoneSpider import QQZoneSpider
from src.util.util import get_full_time_from_mktime
import math
import threading
import pandas as pd
import json
import re
import time
"""
QQ空间抽奖小程序
可以指定说说并从点赞或评论的人中随机抽奖
"""
class winClient(object):
    like_list = []
    cmt_list = []
    def __init__(self):
        self.sp = QQZoneSpider(use_redis=False, debug=False, from_client=True, mood_num=20)
        warm_tip = "****************************************\n" \
                   "**************QQ空间抽奖小程序***************\n" \
                   "****************************************"
        self.output(warm_tip)
        self.output("请输入获取最近访客的时间间隔，默认为60秒")
        time_step = input()
        try:
            time_step = int(time_step)
        except:
            time_step = 60
        visit_file_name = "最近访客" + get_full_time_from_mktime(int(time.time())) + ".xlsx"
        self.output("最近访客文件名:" + visit_file_name)

        try:
            self.sp.login_with_qr_code()
            self.output("用户" + self.sp.username + "登陆成功！")
        except BaseException:
            self.output("用户登陆失败！请检查网络连接或稍后再试！")
            exit(1)

        visit_t = threading.Thread(target=self.sp.parse_recent_visit, args=[visit_file_name, time_step])
        visit_t.start()
        self.output("正在获取最近的说说...")
        url_mood = self.sp.get_mood_url()
        url_mood = url_mood + '&uin=' + str(self.sp.username)
        self.content_list = self.get_content_list(url_mood, 0)
        self.content_list += self.get_content_list(url_mood, 20)
        self.content_list += self.get_content_list(url_mood, 40)
        self.output('------------------------')
        self.output("最近的60条说说:")
        for item in self.content_list:
            content = item['content']
            if len(content) > 20:
                content = content[0:20] + '。。。'
            item_str = '|' + str(item['order']) + '|' + content
            self.output(item_str)
        while True:
            try:
                self.output('------------------------')
                self.output("**以下输入请全部只输入数字！按回车键结束输入！**")
                self.output("**输入Q退出本程序**")
                is_digit = False
                while not is_digit:
                    self.output('请输入您要选择的说说序号:')
                    mood_order = input()
                    is_digit = self.check_input(mood_order)
                mood_order = int(mood_order)
                if mood_order > len(self.content_list):
                    pos = (math.ceil(mood_order / 20) - 1) * 20
                    mood_order = mood_order % 20
                    t1 = threading.Thread(target=self.get_all, args=(url_mood, pos, mood_order))
                    t1.setDaemon(True)
                    t1.start()
                else:
                    unikey = self.content_list[mood_order - 1]
                    key = unikey['unikey']
                    tid = unikey['tid']
                    t2 = threading.Thread(target=self.start_like_cmt_thread, args=(key, tid))
                    t2.setDaemon(True)
                    t2.start()
                is_digit = False
                while not is_digit:
                    self.output('请输入抽奖的类型，1-点赞；2-评论；(其它)-我全都要！ ：')
                    type = input()
                    is_digit = self.check_input(type)
                is_digit = False
                while not is_digit:
                    self.output('请选择抽奖的用户数量：')
                    user_num = input()
                    is_digit = self.check_input(user_num)
                # 等待线程运行完
                try:
                    t1.join()
                    t2.join()
                    self.like_t.join()
                    self.cmt_t.join()
                except:
                    pass
                self.type = int(type)
                self.user_num = int(user_num)
                self.file_name = self.content_list[mood_order - 1]['content']
                if len(self.file_name) > 10:
                    self.file_name = self.file_name[:10]
                self.file_name = re.sub('[^\w\u4e00-\u9fff]+', '', self.file_name)
                if len(self.file_name) <= 0:
                    self.file_name = str(mood_order)
                print("说说:", self.file_name)
                self.do_raffle()
                cmt_df = pd.DataFrame(self.cmt_list)
                like_df = pd.DataFrame(self.like_list)
                cmt_df.to_excel("评论-" + self.file_name + '.xlsx', index=False)
                like_df.to_excel("点赞-" + self.file_name + '.xlsx', index=False)
            except BaseException as e:
                if str(e) == '2':
                    exit(2)
                else:
                    self.output('----------------------')
                    print(e)
                    self.output("未知错误，请重新尝试")
                    self.output('----------------------')


    def get_content_list(self, url_mood, pos):
        self.sp.get_mood_in_range(pos=pos, mood_num=pos + 20, recover_index_split=0, url_mood=url_mood, until_stop_time=True)
        content_list = self.sp.get_unilikeKey_tid_and_smallpic(self.sp.content[0], count=pos)
        self.sp.content.pop()
        return content_list

    def get_all(self, url_mood, pos, mood_order):
        self.content_list = self.get_content_list(url_mood, pos)
        unikey = self.content_list[mood_order - 1]
        key = unikey['unikey']
        tid = unikey['tid']
        self.start_like_cmt_thread(key, tid)

    def do_raffle(self):
        if self.type == 1:
            raffle_list = self.like_list
        elif self.type == 2:
            raffle_list = self.cmt_list
        else:
            raffle_list = self.like_list + self.cmt_list
        raffle_df = pd.DataFrame(raffle_list)
        if raffle_df.empty:
            self.output("候选用户为空，选择的该条说说可能没有点赞或评论，请重新选择")
            return
        else:
            self.output("共有满足条件的候选用户" + str(raffle_df.shape[0]) + "名")
        raffle_df.drop_duplicates('qq', inplace=True)
        if self.user_num >= raffle_df.shape[0]:
            self.output("抽奖目标人数大于候选人数,因此所有人中奖！")
            self.output('------------------------')
            raffle_json = json.loads(raffle_df.to_json(orient="records"))
            for user in raffle_json:
                print('| ', user['qq'],' |', user['name'])
        else:
            self.output("恭喜以下中奖用户！")
            self.output('------------------------')
            raffled = raffle_df.sample(n=self.user_num)
            raffle_json = json.loads(raffled.to_json(orient="records"))

            for user in raffle_json:
                print('| ', user['qq'],' |', user['name'])
        self.output('------------------------')


    def start_like_cmt_thread(self, key, tid):
        self.like_t = threading.Thread(target=self.get_like_names, args=(key, tid))
        self.cmt_t = threading.Thread(target=self.get_cmt_names, args=(key, tid))
        self.like_t.setDaemon(True)
        self.cmt_t.setDaemon(True)
        self.like_t.start()
        self.cmt_t.start()

    def get_like_names(self, key, tid):
        self.like_list_name = self.sp.get_like_list(key, tid)
        self.parse_like_names()

    def get_cmt_names(self, key, tid):
        self.cmt_name = self.sp.get_mood_all_cmt(key, tid)
        self.parse_cmt_names()

    def check_input(self, x):
        if x == 'Q' or x == 'q':
            self.output("即将退出本程序！希望您使用愉快！")
            exit(2)
        try:
            x = int(x)
            if x <= 0:
                raise BaseException
            return True
        except BaseException:
            self.output("输入的不是大于0的数字，请重新输入！")
            return False

    def output(self, x):
        print(x)

    def parse_like_names(self):
        like_names = self.like_list_name['data']['like_uin_info']
        like_list = []
        for name in like_names:
            uin = name['fuin']
            nick = name['nick']
            like_list.append(dict(qq=uin, name=nick))
        self.like_list = like_list

    def parse_cmt_names(self):
        cmt_list = []
        for i, name in enumerate(self.cmt_name):
            if i < 20:
                temp = name['owner']
                user = dict(qq=temp['uin'], name=temp['name'])
            else:
                cmt_name = name['poster']['name']
                cmt_id = name['poster']['id']
                user = dict(qq=cmt_id, name=cmt_name)
            user['content'] = name['content']
            cmt_list.append(user)
        self.cmt_list = cmt_list

if __name__ == '__main__':
    wc = winClient()
