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
import copy

class Spider(object):
    def __init__(self, use_redis=False, debug=False, file_name_head=''):
        """
        init method
        :param use_redis: If true, use redis and json file to save data, if false, use json file only.
        :param debug: If true, print info in console
        """
        self.host = 'https://user.qzone.qq.com'
        self.http_host = 'http://user.qzone.qq.com'
        self.use_redis = use_redis
        self.debug = debug
        self.file_name_head = file_name_head
        self.__username, self.__password = self.get_username_password()
        self.mood_host = self.http_host + '/' + self.__username + '/mood/'
        self.headers = {
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
        self.content = []
        self.unikeys = []
        self.like_detail = []
        self.like_list_names = []
        self.tid = ""
        self.mood_details = []
        self.error_unikeys = []
        self.CONTENT_FILE_NAME = 'data/' + file_name_head + '_QQ_content.json'
        self.LIKE_DETAIL_FILE_NAME = 'data/' + file_name_head + '_QQ_like_detail' + '.json'
        self.LIKE_LIST_NAME_FILE_NAME = 'data/' + file_name_head + '_QQ_like_list_name' + '.json'
        self.MOOD_DETAIL_FILE_NAME = 'data/' + file_name_head + '_QQ_mood_details' + '.json'
        if (use_redis):
            self.re = connect_redis()

    def login(self):
        """
        模拟登陆， 需要selenium
        登陆成功后获取cookie，并存在self.cookie中
        :return:
        """
        self.web = webdriver.Chrome()
        self.web.get(self.host)
        self.web.switch_to.frame('login_frame')
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
        # 获取cookie
        for elem in self.web.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + ";"
        self.cookies = cookie
        # 根据cookie计算g_tk值
        self.get_g_tk()
        self.headers['Cookie'] = self.cookies
        self.web.quit()

    def get_username_password(self):
        with open('userinfo.json', 'r', encoding='utf-8') as r:
            userinfo = json.load(r)
        return userinfo['username'], userinfo['password']

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

    # 由于有的比较老旧的说说的点赞信息被清空了，需要从这里获取点赞的数目
    def get_like_num_url(self, unikey):
        """

        :param unikeys:
        :return:
        """
        like_url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2?'
        params = {
            "_stp": '',
            "unikey": unikey,
            # 'face': '0<|>0<|>0<|>0<|>0<|>0<|>0<|>0<|>0<|>0',
            'face':0,
            'fupdate': 1,
            'g_tk': self.g_tk,
            'qzonetoken': ''
        }
        like_url = like_url + parse.urlencode(params)
        return like_url

    def get_like_num(self, curlikekey):
        # unikeys = "<|>".join(curlikekey)
        unikeys = curlikekey
        if unikeys != '':
            try:
                like_url = self.get_like_num_url(unikeys)
                like_content = self.get_json(self.req.get(like_url).content.decode('utf-8'))
                # like_content是所有的点赞信息，其中like字段为点赞数目，list是点赞的人列表，有的数据中list为空
                return like_content
            except BaseException as e:
                self.format_error(e, 'Failed to get like_url:' + unikeys)
                return {}
        else:
            return {}

    # 将响应字符串转化为标准Json
    def get_json(self, str1):
        arr = re.findall(r'[^()]+', str1)
        json = ""
        for i in range(1, len(arr) - 1):
            json += arr[i]
        return json

    def get_mood_list(self, mood_begin=0, mood_num=100, download_image=False, recover=False):
        """
         # 获取动态详情列表（一页20个）
        :param file_name_head: 文件名的前缀
        :param mood_num: 下载的动态数量，最好设置为20的倍数
        :param download_image: 是否下载图片，下载的图片是仅供预览用的小图，该步骤比较耗时
        :param recover: 是否从redis或文件中恢复数据（主要用于爬虫意外终端之后的数据恢复）
        :return:
        """
        url_mood = self.get_mood_url()
        url_mood = url_mood + '&uin=' + str(self.__username)
        pos = mood_begin
        recover_index_split = 0
        if recover:
            recover_index = self.do_recover_from_exist_data()
            pos = recover_index // 20 * 20
            recover_index_split = recover_index % 20
        # 如果mood_num为-1，则下载全部的动态
        if mood_num == -1:
            url__ = url_mood + '&pos=' + str(pos)
            mood = self.req.get(url=url__, headers=self.headers).content.decode('utf-8')
            mood_json = json.loads(self.get_json(mood))
            mood_num = mood_json['usrinfo']['msgnum']


        # 1700为我空间动态数量
        while pos < mood_num:
            print('正在爬取', pos, '...')
            try:
                url__ = url_mood + '&pos=' + str(pos)
                mood_list = self.req.get(url=url__, headers=self.headers)
                json_content = self.get_json(str(mood_list.content.decode('utf-8')))
                self.content.append(json_content)
                # 获取每条动态的unikey
                self.unikeys = self.get_unilikeKey_tid_and_smallpic(json_content)

                # 从数据中恢复后，避免重复爬取相同数据
                if recover_index_split != 0:
                    self.unikeys = self.unikeys[recover_index_split:]
                    recover_index_split = 0

                # 获取数据
                self.do_get_infos(self.unikeys, download_image)
                pos += 20
                # 每抓100条保存一次数据
                if pos % 100 == 0:
                    if self.use_redis:
                        self.re.set(self.CONTENT_FILE_NAME[5:], json.dumps(self.content, ensure_ascii=False))
                        self.re.set(self.LIKE_LIST_NAME_FILE_NAME[5:],
                                    json.dumps(self.like_list_names, ensure_ascii=False))
                        self.re.set(self.MOOD_DETAIL_FILE_NAME[5:],
                                    json.dumps(self.mood_details, ensure_ascii=False))
                        self.re.set(self.LIKE_DETAIL_FILE_NAME[5:],
                                    json.dumps(self.like_detail, ensure_ascii=False))
                    # 缓存到json文件
                    # with open('data/' + self.file_name_head + str(pos) + '.json', 'w', encoding='utf-8') as w:
                    #     w.write(json_content)
            except BaseException as e:
                print("ERROR===================")
                print("因错误导致爬虫终止....现在临时保存数据")
                self.save_all_data_to_json()
                print('已爬取的数据页数(20条一页):', pos)
                print("保存临时数据成功")
                print("ERROR===================")
                raise e
        # 保存所有数据到指定文件
        print('保存最终数据中...')
        if len(self.error_unikeys) > 0:
            if(self.debug):
                print('Error Unikeys Num:', len(self.error_unikeys))
                print('Retry to get them...')
            self.get_error_unikey(download_image)
        self.save_all_data_to_json()
        print("finish===================")

    def do_get_infos(self,unikeys,  download_image):
        for unikey in unikeys:
            if (self.debug):
                print('unikey:' + unikey['unikey'])
            self.unikey = unikey['unikey']
            self.tid = unikey['tid']
            # 获取动态详情
            try:
                mood_detail = self.get_mood_detail()
                self.mood_details.append(mood_detail)
                # 获取点赞详情（方法一）
                # 此方法有时候不能获取到点赞的人的昵称，但是点赞的数量这个数据一直存在
                like_detail = self.get_like_num(unikey['curlikekey'])
                self.like_detail.append(like_detail)
                # 获取点赞详情（方法二）
                # 此方法能稳定获取到点赞的人的昵称，但是有的数据已经被清空了
                like_list_name = self.get_like_list()
                self.like_list_names.append(like_list_name)
                if download_image:
                    for pic_url in unikey['smallpic_list']:
                        file_name = self.tid + '--' + pic_url.split('/')[-1]
                        self.download_image(pic_url, file_name)
            except BaseException as e:
                self.format_error(e, 'continue to capture...')
                # 保存抓取失败的数据信息
                self.error_unikeys.append(unikey)
                continue

    def get_error_unikey(self, download_image):
        """
        重新下载第一次下载中失败的数据
        :param download_image:
        :return:
        """

        # 深拷贝，避免do_get_infos中对self.error_unikeys的更改导致的错误
        error_unikeys = copy.deepcopy(self.error_unikeys)
        self.do_get_infos(error_unikeys, download_image)

    def do_recover_from_exist_data(self):
        if self.use_redis:
            try:
                self.content = json.loads(self.re.get(self.CONTENT_FILE_NAME[5:]))
                self.like_list_names = json.loads(self.re.get(self.LIKE_LIST_NAME_FILE_NAME[5:]))
                self.mood_details = json.loads(self.re.get(self.MOOD_DETAIL_FILE_NAME[5:]))
                self.like_detail = json.loads(self.re.get(self.LIKE_DETAIL_FILE_NAME[5:]))
                if self.debug:
                    print('Finish to recover data from redis:')
                    print('content:', len(self.content))
                    print('like_list_names:', len(self.like_list_names))
                    print('mood_details:', len(self.mood_details))
                    print('like_detail:', len(self.like_detail))
                return len(self.like_list_names)
            except BaseException as e:
                self.format_error(e, 'Failed to recover data from redis')
                print('Now, try to recover data from json files...')
                self.load_all_data_from_json()
        else:
            self.load_all_data_from_json()


    def save_all_data_to_json(self):
        self.save_data_to_json(data=self.content, file_name=self.CONTENT_FILE_NAME)
        self.save_data_to_json(data=self.like_list_names, file_name = self.LIKE_LIST_NAME_FILE_NAME)
        self.save_data_to_json(data=self.mood_details, file_name=self.MOOD_DETAIL_FILE_NAME)
        self.save_data_to_json(data=self.like_detail, file_name=self.LIKE_DETAIL_FILE_NAME)

        if self.use_redis:
            if self.use_redis:
                self.re.set(self.CONTENT_FILE_NAME[5:], json.dumps(self.content, ensure_ascii=False))
                self.re.set(self.LIKE_LIST_NAME_FILE_NAME[5:],
                            json.dumps(self.like_list_names, ensure_ascii=False))
                self.re.set(self.MOOD_DETAIL_FILE_NAME[5:],
                            json.dumps(self.mood_details, ensure_ascii=False))
                self.re.set(self.LIKE_DETAIL_FILE_NAME[5:],
                            json.dumps(self.like_detail, ensure_ascii=False))

    def save_data_to_json(self, data, file_name):
        with open(file_name, 'w', encoding='utf-8') as w2:
            json.dump(data, w2, ensure_ascii=False)

    def load_all_data_from_json(self):
        self.content = self.load_data_from_json(self.CONTENT_FILE_NAME)
        self.like_list_names = self.load_data_from_json(self.LIKE_LIST_NAME_FILE_NAME)
        self.mood_details = self.load_data_from_json(self.MOOD_DETAIL_FILE_NAME)
        self.like_detail = self.load_data_from_json(self.LIKE_DETAIL_FILE_NAME)

    def load_data_from_json(self, file_name):
        try:
            with open(file_name, encoding='utf-8') as content:
                data = json.load(content)
            return data
        except  BaseException as e:
            self.format_error(e, 'Failed to load data ' + file_name)


    def format_error(self, e, msg):
        print('ERROR===================')
        print(e)
        print(msg)
        print('ERROR===================')


    # 获得点赞的人
    def get_like_list(self):
        url = self.get_aggree_url()
        if (self.debug):
            print('获取点赞的人', url)
        try:
            like_list = self.req.get(url=url, headers=self.headers)
            like_list_detail = self.get_json(like_list.content.decode('utf-8'))
            # like_list_detail = like_list_detail.replace('\\n', '')
            # print(like_list_detail)
            # print("success to get like list")
            return like_list_detail
        except BaseException as e:
            self.format_error(e, 'Failed to get agree:' + url)
            return {}


    # 获得每一条说说的详细内容
    def get_mood_detail(self):
        url_detail = self.get_mood_detail_url()
        if(self.debug):
            print('获取说说动态详情:', url_detail)
        try:
            mood_detail = self.req.get(url=url_detail, headers=self.headers)
            json_mood = self.get_json(str(mood_detail.content.decode('utf-8')))
            return json_mood
        except BaseException as e:
            self.format_error(e, 'Failed to get mood_detail:' + url_detail)
            return {}

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

    # unikey 是用于辨别每条说说的唯一识别码
    # unikey eg: http://user.qzone.qq.com/1272082503/mood/4770d24b81eba85b0b110800.1
    def get_unilikeKey_tid_and_smallpic(self, mood_detail):
        unikey_tid_list = []
        jsonData = json.loads(mood_detail)
        for item in jsonData['msglist']:
            tid = item['tid']
            unikey = self.mood_host + tid + '.1'
            if (self.debug):
                print('unikey:' + unikey)
            # 如果存在图片
            pic_list = []
            curlikekey = ''
            if 'pic' in item:
                item_key = item['pic']
                # 保存所有图片的预览图下载地址
                for i in range(len(item_key)):
                    if 'smallurl' in item_key[i]:
                        smallurl = item_key[i]['smallurl']
                        pic_list.append(smallurl)
                # 如果存在多张图片
                if len(item_key) > 1:
                    curlikekey = unikey + "<.>" + unikey
                else:
                    curlikekey = item_key[0]['curlikekey']
                # curlikekey_list.append(curlikekey)
            unikey_tid_list.append(dict(unikey=unikey, tid=tid, smallpic_list=pic_list, curlikekey=curlikekey))
        return unikey_tid_list

    def download_image(self, url, name):
        image_url = url
        try:
            r = self.req.get(url=image_url, headers=self.headers)
            image_content = (r.content)
            file_image = open('qq_image/' + name + '.jpg', 'wb+')
            file_image.write(image_content)
            file_image.close()
        except BaseException as e:
            self.format_error(e, 'Failed to download image:' + name)


def connect_redis():
    try:
        pool = redis.ConnectionPool(host="127.0.0.1", port=6379, decode_responses=True)
        re = redis.Redis(connection_pool=pool)
        return re
    except BaseException as e:
        print('Error===================')
        print(e)
        print('Failed to connect redis')
        print('===================')


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
    sp = Spider(use_redis=True, debug=True, file_name_head='maicius')
    sp.login()
    print("Login success")
    sp.get_mood_list(mood_begin=0,  mood_num = -1, download_image=True, recover=True)

    print("Finish to capture")

def do_simple_query():
    """
    To do some simple redis query
    :return:
    """
    sp = Spider(use_redis=True, debug=True)
    like_list = json.loads(sp.re.get('maicius_QQ_like_list_all'))
    sp.save_data_to_json(like_list, 'maicius_QQ_like_list_all.json')


if __name__ == '__main__':
    # 执行capture_data以为的函数时请注释掉capture_data
    # capture_data()
    # 计算一些信息
    # calculate_info()
    # analysisMoodDetails()
    do_simple_query()

