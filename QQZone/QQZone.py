# coding:utf-8
# 爬取 自己 的QQ空间动态并做分析
# 包括动态内容、点赞的人、评论的人、评论的话
# 登陆使用的是Selenium， 无法识别验证码
# 若出现验证码，则先尝试手动从浏览器登陆并退出再运行程序

from selenium import webdriver
import requests
import time
from urllib import parse
import re
import redis
import json


class Spider(object):
    def __init__(self):
        self.web = webdriver.Chrome()
        self.web.get('https://user.qzone.qq.com')
        self.__username = ''
        self.__password = ''
        self.headers = {
            'host': 'h5.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'connection': 'keep-alive'
        }
        self.headers2 = {
            'host': 'h5.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'connection': 'keep-alive'
        }
        self.req = requests.Session()
        self.cookies = {}
        self.qzonetoken = ""
        self.re = connect_redis()
        self.content = []
        self.unikeys = []
        self.like_list_names = []
        self.tid = ""
        self.mood_details = []

    # 模拟登陆， 需要selenium
    def login(self):
        self.web.switch_to_frame('login_frame')
        log = self.web.find_element_by_id("switcher_plogin")
        log.click()
        time.sleep(1)
        username = self.web.find_element_by_id('u')
        username.send_keys(self.__username)
        ps = self.web.find_element_by_id('p')
        ps.send_keys(self.__password)
        btn = self.web.find_element_by_id('login_button')
        time.sleep(5)
        btn.click()
        time.sleep(5)
        self.web.get('https://user.qzone.qq.com/{}'.format(self.__username))
        cookie = ''
        for elem in self.web.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + ";"
        self.cookies = cookie
        self.get_g_tk()
        self.headers['Cookie'] = self.cookies
        self.web.quit()

    # 构造获取动态的URL
    def get_mood_url(self):
        url = 'https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6?'
        params = {
            "sort": 0,
            "start": 0,
            "num": 20,
            "cgi_host": "http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6",
            "replynum": 100,
            "callback": "_preloadCallback",
            "code_version": 1,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "notice": 0,
            "format": "jsonp",
            "need_private_comment": 1,
            "g_tk": self.g_tk
        }
        url = url + parse.urlencode(params)
        return url

    # 构造点赞的人的URL
    def get_aggree_url(self):
        url = 'https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app?'
        params = {
            "uin": self.__username,
            "unikey": self.unikey,
            "begin_uin": 0,
            "query_count": 60,
            "if_first_page": 1,
            "g_tk": self.g_tk,
        }
        url = url + parse.urlencode(params)
        return url

    # 构造获取动态详情的url
    def get_mood_detail_url(self):
        url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6?'
        params = {
            "uin": self.__username,
            "unikey": self.unikey,
            "tid": self.tid,
            "t1_source": 1,
            "ftype": 0,
            "sort": 0,
            "pos": 0,
            "num": 20,
            "callback": "_preloadCallback",
            "code_version": 1,
            "format": "jsonp",
            "need_private_comment": 1,
            "g_tk": self.g_tk
        }
        url = url + parse.urlencode(params)
        return url

    # 将响应字符串转化为标准Json
    def get_json(self, str1):
        arr = re.findall(r'[^()]+', str1)
        json = ""
        for i in range(1, len(arr) - 1):
            json += arr[i]
        return json

    # 获取动态详情列表（一页20个）
    def get_mood_list(self):
        urlMood = self.get_mood_url()
        url_Mood = urlMood + '&uin=' + str(self.__username)
        self.re = connect_redis()
        pos = 0
        # 1700为我空间动态数量
        while pos < 1700:
            url__ = url_Mood + '&pos=' + str(pos)
            mood_list = self.req.get(url=url__, headers=self.headers)
            jsonContent = self.get_json(str(mood_list.content.decode('utf-8')))
            self.content.append(jsonContent)
            # print(jsonContent)
            # 获取每条动态的unikey
            self.unikeys = self.get_unilikeKey(jsonContent)
            # 获取点赞的人的详情列表
            for unikey in self.unikeys:
                print('unikey' + unikey)
                self.unikey = unikey
                like_detail = self.get_like_list()

                self.like_list_names.append(like_detail)
                self.tid = self.get_tid(unikey)

                # 获取动态详情
                mood_detail = self.get_mood_detail()
                self.mood_details.append(mood_detail)
            # print('1272082503', jsonContent)
            # 存储到json文件
            with open('data/data' + str(pos) + '.json', 'w', encoding='utf-8') as w:
                w.write(jsonContent)
            pos += 20
            # 每抓100条保存一次数据到redis，如果没有redis需要注释掉这部分
            if pos % 100 == 0:
                self.re.set("QQ", json.dumps(self.content, ensure_ascii=False))
                self.re.set("QQ_like_list_all", json.dumps(self.like_list_names, ensure_ascii=False))
                self.re.set("QQ_mood_details", json.dumps(self.mood_details, ensure_ascii=False))
            print(pos)
        # time.sleep(2)

        # print(self.content)
        # 保存所有数据到指定文件
        with open('data/like' + '.json', 'w', encoding='utf-8') as w2:
            json.dump(self.like_list_names, w2, ensure_ascii=False)

        with open('data/mood_detail' + '.json', 'w', encoding='utf-8') as w3:
            json.dump(self.mood_details, w3, ensure_ascii=False)

        print(self.content)
        print("content:" + json.dumps(self.content))
        print("=====================")
        print("agree" + json.dumps(self.like_list_names, ensure_ascii=False))

        # 保存数据到redis， 如没有redis需要注释掉这部分
        self.re.set("QQ", json.dumps(self.content, ensure_ascii=False))
        self.re.set("QQ_like_list_all", json.dumps(self.like_list_names, ensure_ascii=False))
        self.re.set("QQ_mood_details", json.dumps(self.mood_details, ensure_ascii=False))
        print("finish")

    # 获得点赞的人
    def get_like_list(self):
        url = self.get_aggree_url()
        print(url)
        like_list = self.req.get(url=url, headers=self.headers)
        like_list_detail = self.get_json(like_list.content.decode('utf-8'))
        # like_list_detail = like_list_detail.replace('\\n', '')
        # print(like_list_detail)
        # print("success to get like list")
        return like_list_detail

    # 获得每一条说说的详细内容
    def get_mood_detail(self):
        urlDetail = self.get_mood_detail_url()
        # print(urlDetail)
        mood_detail = self.req.get(url=urlDetail, headers=self.headers)
        json_mood = self.get_json(str(mood_detail.content.decode('utf-8')))

        return json_mood

    # 根据unikey 获得tid
    def get_tid(self, unikey):
        # unikey是链接，形如：http://user.qzone.qq.com/1272082503/mood/4770d24bc5bb7459cc140200.1
        # 其中，4770d24bc5bb7459cc14020是tid
        tids = unikey.split("/")
        tid = tids[5].split(".")
        return tid[0]

    # 核心加密字段
    def get_g_tk(self):
        p_skey = self.cookies[self.cookies.find('p_skey=') + 7: self.cookies.find(';', self.cookies.find('p_skey='))]
        h = 5381
        for i in p_skey:
            h += (h << 5) + ord(i)
        print('g_tk', h & 2147483647)
        self.g_tk = h & 2147483647

    # 这里是从每条说说的图片地址中截取unikey，如果该条说说没有图片，则获取不到
    # unikey 是用于辨别每条说说的唯一识别码
    def get_unilikeKey(self, mood_detail):
        allunikey = []
        jsonData = json.loads(mood_detail)
        # print(jsonData)
        for item in jsonData['msglist']:
            # print(item.keys())
            if 'pic' in item:
                itemKey = item['pic']
                if 'curlikekey' in itemKey[0]:
                    unikey = itemKey[0]['curlikekey'].split('^||^')
                    print('unikey:' + unikey[0])
                    allunikey.append(unikey[0])
        return allunikey


def connect_redis():
    pool = redis.ConnectionPool(host="127.0.0.1", port=6379)
    re = redis.Redis(connection_pool=pool)
    return re


def doAnalysis(file_name, commentNumber, commentList):
    f = open(file_name, encoding='utf-8')
    data = json.load(f)
    agreeDict = []
    for item in data['msglist']:
        print(item['content'])
        # print(item.keys())
        time_local = time.localtime(item['created_time'])
        # 转换成新的时间格式(2016-05-05 20:28:54)
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        print(dt)
        if 'pic' in item:
            itemKey = item['pic']
            if 'curlikekey' in itemKey[0]:
                unikey = itemKey[0]['curlikekey'].split('^||^')
                # print(unikey)
        if 'commentlist' in item:
            commentNumber.append(len(item['commentlist']))
            for item2 in item['commentlist']:
                if item2['name'] in commentList:
                    commentList[item2['name']] += 1
                else:
                    commentList[item2['name']] = 1
                    # print(item2['name'])
        else:
            commentNumber.append(0)
    f.close()


def analysisMoodDetails():
    f = open('data/mood_detail.json', encoding='utf-8')
    data = json.load(f)
    mood_words = ""
    for item in data:
        mood = json.loads(item)
        # print(mood.keys())
        mood_words += mood['content']
    with open('data/mood_details.txt', 'w', encoding='utf-8') as mood_writer:
        mood_writer.write(mood_words)

# 计算点赞的人、评论的人
def calculate_info():
    commentList = {}
    commentNumber = []
    pos = 0
    while pos < 1700:
        fileName = 'data/data' + str(pos) + '.json'
        doAnalysis(fileName, commentNumber, commentList)
        pos += 20
    f = open('data/like.json', encoding='utf-8')
    data = json.load(f)
    totalAgree = 0
    agreeNick = {}
    agreeNumberList = []
    for item in data:
        item = json.loads(item)
        uin_data = item['data']
        totalAgree += int(uin_data['total_number'])
        agreeNumberList.append(uin_data['total_number'])
        # print(str(agreeNumberList))
        for item_uin in uin_data['like_uin_info']:
            if item_uin['nick'] in agreeNick:
                agreeNick[item_uin['nick']] += 1
            else:
                agreeNick[item_uin['nick']] = 1
    agreeNumberList.sort(reverse=True)
    commentNumber.sort(reverse=True)
    print("累计点赞数：" + str(totalAgree))
    print("平均点赞数" + str(totalAgree / 1700))
    print("点赞次数" + str(agreeNumberList))
    print("点赞的人：" + str(sorted(agreeNick.items(), key=lambda item2: item2[1], reverse=True)))
    # print("评论数:" + str(commentNumber))
    print("给我评论的人：" + str(sorted(commentList.items(), key=lambda nameItem: nameItem[1], reverse=True)))
    print("finish")
    f.close()


def capture_data():
    sp = Spider()
    sp.login()
    print("Login success")
    sp.get_mood_list()
    print("Finish to capture")

if __name__ == '__main__':
    # 执行capture_data以为的函数时请注释掉capture_data
    capture_data()

    # 计算一些信息
    calculate_info()
    # analysisMoodDetails()
