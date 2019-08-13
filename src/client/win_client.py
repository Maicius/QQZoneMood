import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
from src.spider.QQZoneSpider import QQZoneSpider
import math
import threading

class winClient(object):

    def __init__(self):
        self.sp = QQZoneSpider(use_redis=False, debug=False, from_client=True, mood_num=20)
        warm_tip = "****************************************\n" \
                   "**************QQ空间抽奖小程序***************\n" \
                   "****************中飞院定制版****************\n" \
                   "****************************************"
        self.output(warm_tip)
        try:
            self.sp.login_with_qr_code()
            url_mood = self.sp.get_mood_url()
            url_mood = url_mood + '&uin=' + str(self.sp.username)
            self.get_content_list(url_mood, 0)
            self.output("用户" + self.sp.username + "登陆成功！")
        except BaseException:
            self.output("用户登陆失败！请检查网络连接或稍后再试！")
            exit(1)
        self.output('------------------------')
        self.output("最近的20条说说")
        for item in self.content_list:
            content = item['content']
            if len(content) > 20:
                content = content[0:20] + '。。。'
            item_str = '|' + str(item['order']) + '|' + content
            self.output(item_str)
        while True:
            self.output('------------------------')
            self.output("以下输入请全部只输入数字！按回车键结束输入！")
            self.output("输入Q退出本程序")
            is_digit = False
            while not is_digit:
                self.output('请输入您要选择的说说序号:')
                mood_order = input()
                is_digit = self.check_input(mood_order)
            mood_order = int(mood_order)
            if mood_order <= 20:
                pos = math.ceil(mood_order / 20) - 1
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
                self.output('请输入抽奖的类型，1-点赞；2-评论；3-我全都要！ ：')
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
            self.output("恭喜以下用户中奖!")
            self.output(self.like_list_name)
            self.output(self.cmt_name)

    def get_content_list(self, url_mood, pos):
        self.sp.get_mood_in_range(pos=pos, mood_num=20, recover_index_split=0, url_mood=url_mood, until_stop_time=True)
        self.content_list = self.sp.get_unilikeKey_tid_and_smallpic(self.sp.content[0])

    def get_all(self, url_mood, pos, mood_order):
        self.get_content_list(url_mood, pos)
        unikey = self.content_list[mood_order - 1]
        key = unikey['unikey']
        tid = unikey['tid']
        self.start_like_cmt_thread(key, tid)

    def start_like_cmt_thread(self, key, tid):
        self.like_t = threading.Thread(target=self.get_like_names, args=(key, tid))
        self.cmt_t = threading.Thread(target=self.get_cmt_names, args=(key, tid))
        self.like_t.setDaemon(True)
        self.cmt_t.setDaemon(True)
        self.like_t.start()
        self.cmt_t.start()

    def get_like_names(self, key, tid):
        self.like_list_name = self.sp.get_like_list(key, tid)

    def get_cmt_names(self, key, tid):
        self.cmt_name = self.sp.get_mood_all_cmt(key, tid)

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

if __name__ == '__main__':
    wc = winClient()
