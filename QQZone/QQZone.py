# coding:utf-8
# QQ空间动态爬虫
# 只能爬自己的！！！
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
import datetime


class Spider(object):
    def __init__(self, use_redis=False, debug=False, file_name_head=''):
        """
        init method
        :param use_redis: If true, use redis and json file to save data, if false, use json file only.
        :param debug: If true, print info in console
        :param file_name_head: 文件名的前缀
        """
        self.begin_time = datetime.datetime.now()
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
        self.error_like_detail_unikeys = []
        self.error_like_list_unikeys = []
        self.error_mood_unikeys = []
        self.error_like_detail = {}
        self.error_like_list = {}
        self.error_mood = {}
        self.init_file_name(file_name_head)

        if (use_redis):
            self.re = self.connect_redis()

    def init_file_name(self, file_name_head):
        self.CONTENT_FILE_NAME = 'data/' + file_name_head + '_QQ_content.json'
        self.LIKE_DETAIL_FILE_NAME = 'data/' + file_name_head + '_QQ_like_detail' + '.json'
        self.LIKE_LIST_NAME_FILE_NAME = 'data/' + file_name_head + '_QQ_like_list_name' + '.json'
        self.MOOD_DETAIL_FILE_NAME = 'data/' + file_name_head + '_QQ_mood_detail' + '.json'

        self.ERROR_LIKE_DETAIL_FILE_NAME = 'error/' + file_name_head + '_QQ_like_detail_error' + '.json'
        self.ERROR_LIKE_LIST_NAME_FILE_NAME = 'error/' + file_name_head + '_QQ_like_list_name_error' + '.json'
        self.ERROR_MOOD_DETAIL_FILE_NAME = 'error/' + file_name_head + '_QQ_mood_detail_error' + '.json'

        self.ERROR_LIKE_DETAIL_UNIKEY_FILE_NAME = 'error/' + file_name_head + '_QQ_like_detail_error_unikey' + '.txt'
        self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME = 'error/' + file_name_head + '_QQ_like_list_error_unikey' + '.txt'
        self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME = 'error/' + file_name_head + '_QQ_mood_detail_error_unikey' + '.txt'
        self.SMALL_IMAGE_DIR = 'qq_image/'
        self.BIG_IMAGE_DIR = 'qq_big_image/'

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
        print("Login success")
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
    def get_aggree_url(self, unikey):
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
    def get_mood_detail_url(self, unikey, tid):
        url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6?'
        params = {
            "uin": self.__username,
            "unikey": unikey,
            "tid": tid,
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
    def get_like_detail_url(self, unikey):
        """

        :param unikeys:
        :return:
        """
        like_url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2?'
        params = {
            "_stp": '',
            "unikey": unikey,
            # 'face': '0<|>0<|>0<|>0<|>0<|>0<|>0<|>0<|>0<|>0',
            'face': 0,
            'fupdate': 1,
            'g_tk': self.g_tk,
            'qzonetoken': ''
        }
        like_url = like_url + parse.urlencode(params)
        return like_url

    def get_like_detail(self, curlikekey):
        # unikeys = "<|>".join(curlikekey)
        unikeys = curlikekey
        like_url = self.get_like_detail_url(unikeys)
        if unikeys != '':
            try:
                like_content = self.get_json(self.req.get(like_url).content.decode('utf-8'))
                # like_content是所有的点赞信息，其中like字段为点赞数目，list是点赞的人列表，有的数据中list为空
                return like_content
            except BaseException as e:
                # 因为这里错误较多，所以进行一次retry，如果不行则保留unikey
                self.format_error(e, 'Retry to get like_url:' + unikeys)
                try:
                    like_content = self.get_json(self.req.get(like_url).content.decode('utf-8'))
                    return like_content
                except BaseException as e:
                    self.error_like_detail_unikeys.append(unikeys)
                    self.format_error(e, 'Failed to get like_url:' + unikeys)
                    return {}
        else:
            self.error_like_detail_unikeys.append(unikeys)
            return {}

    # 将响应字符串转化为标准Json
    def get_json(self, str1):
        arr = re.findall(r'[^()]+', str1)
        json = ""
        for i in range(1, len(arr) - 1):
            json += arr[i]
        return json

    def get_mood_list(self, mood_begin=0, mood_num=100, download_small_image=False, recover=False,
                      download_big_image=False, download_mood_detail=True, download_like_detail=True,
                      download_like_names=True):
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
                self.do_get_infos(self.unikeys, download_small_image=download_small_image,
                                  download_big_image=download_big_image, download_mood_detail=download_mood_detail,
                                  download_like_detail=download_like_detail, download_like_names=download_like_names)
                pos += 20
                # 每抓100条保存一次数据
                if pos % 100 == 0:
                    self.save_data_to_redis(final_result=False)
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
        if (self.debug):
            print('Error Unikeys Num:', len(self.error_like_detail_unikeys))
            print('Retry to get them...')
        self.retry_error_unikey()
        self.save_all_data_to_json()
        self.result_report()
        print("finish===================")

    def do_get_infos(self, unikeys, download_small_image, download_big_image, download_mood_detail,
                     download_like_detail, download_like_names):
        for unikey in unikeys:
            if (self.debug):
                print('unikey:' + unikey['unikey'])
            self.unikey = unikey['unikey']
            self.tid = unikey['tid']
            # 获取动态详情
            try:
                if download_mood_detail:
                    mood_detail = self.get_mood_detail(self.unikey, self.tid)
                    self.mood_details.append(mood_detail)

                # 获取点赞详情（方法一）
                # 此方法有时候不能获取到点赞的人的昵称，但是点赞的数量这个数据一直存在
                if download_like_detail:
                    like_detail = self.get_like_detail(unikey['curlikekey'])
                    self.like_detail.append(like_detail)

                # 获取点赞详情（方法二）
                # 此方法能稳定获取到点赞的人的昵称，但是有的数据已经被清空了
                if download_like_names:
                    like_list_name = self.get_like_list(self.unikey)
                    self.like_list_names.append(like_list_name)
                if download_small_image:
                    for pic_url in unikey['small_pic_list']:
                        file_name = self.tid + '--' + pic_url.split('/')[-1]
                        self.download_image(pic_url, self.SMALL_IMAGE_DIR + file_name)

                if download_big_image:
                    for big_pic_url in unikey['big_pic_list']:
                        if self.debug:
                            print('大图地址:', big_pic_url)
                        file_name = self.tid + '--' + big_pic_url.split('/')[-1]
                        self.download_image(big_pic_url, self.BIG_IMAGE_DIR + file_name)


            except BaseException as e:
                self.format_error(e, 'continue to capture...')
                continue

    def retry_error_unikey(self):
        """
        重新下载第一次下载中失败的数据
        :param download_image:
        :return:
        """
        # 深拷贝
        error_detail_unikeys = copy.deepcopy(self.error_like_detail_unikeys)
        self.error_like_detail_unikeys = []
        for error_detail_unikey in error_detail_unikeys:
            like_detail = self.get_like_detail(error_detail_unikey)
            self.error_like_detail[error_detail_unikey] = like_detail

        error_mood_unikeys = copy.deepcopy(self.error_mood_unikeys)
        self.error_mood_unikeys = []
        for error_mood_unikey in error_mood_unikeys:
            mood_detail = self.get_mood_detail(error_mood_unikey[0], error_mood_unikey[1])
            self.error_mood[error_mood_unikey] = mood_detail

        error_like_list_unikeys = copy.deepcopy(self.error_like_list_unikeys)
        self.error_like_list_unikeys = []
        for error_like_list_unikey in error_like_list_unikeys:
            like_list = self.get_like_list(error_like_list_unikey)
            self.error_like_list[error_like_list_unikey] = like_list

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
        self.save_data_to_json(data=self.like_list_names, file_name=self.LIKE_LIST_NAME_FILE_NAME)
        self.save_data_to_json(data=self.mood_details, file_name=self.MOOD_DETAIL_FILE_NAME)
        self.save_data_to_json(data=self.like_detail, file_name=self.LIKE_DETAIL_FILE_NAME)
        self.save_data_to_json(data=self.error_mood, file_name=self.ERROR_MOOD_DETAIL_FILE_NAME)
        self.save_data_to_json(data=self.error_like_detail, file_name=self.ERROR_LIKE_DETAIL_FILE_NAME)
        self.save_data_to_json(data=self.error_like_list, file_name=self.ERROR_LIKE_LIST_NAME_FILE_NAME)
        self.save_data_to_txt(data=self.error_like_list_unikeys, file_name=self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME)
        self.save_data_to_txt(data=self.error_like_detail_unikeys, file_name=self.ERROR_LIKE_DETAIL_FILE_NAME)
        self.save_data_to_txt(data=self.error_mood_unikeys, file_name=self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME)
        self.save_data_to_redis(final_result=True)

    def save_data_to_redis(self, final_result=False):
        """
        保存数据到redis中
        :param final_result: 是否为最终结果，如果是，则会保存错误信息，如果不是，则仅做缓存
        :return:
        """
        try:
            if self.use_redis:
                self.re.set(self.CONTENT_FILE_NAME[5:], json.dumps(self.content, ensure_ascii=False))
                self.re.set(self.LIKE_LIST_NAME_FILE_NAME[5:],
                            json.dumps(self.like_list_names, ensure_ascii=False))
                self.re.set(self.MOOD_DETAIL_FILE_NAME[5:],
                            json.dumps(self.mood_details, ensure_ascii=False))
                self.re.set(self.LIKE_DETAIL_FILE_NAME[5:],
                            json.dumps(self.like_detail, ensure_ascii=False))

                if final_result:
                    self.re.set(self.ERROR_LIKE_DETAIL_FILE_NAME[6:],
                                json.dumps(self.error_like_detail, ensure_ascii=False))
                    self.re.set(self.ERROR_LIKE_LIST_NAME_FILE_NAME[6:],
                                json.dumps(self.error_like_list, ensure_ascii=False))
                    self.re.set(self.ERROR_MOOD_DETAIL_FILE_NAME[6:],
                                json.dumps(self.error_mood, ensure_ascii=False))
                    self.re.set(self.ERROR_LIKE_DETAIL_UNIKEY_FILE_NAME, "==".join(self.error_like_detail_unikeys))
                    self.re.set(self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME, "==".join(self.error_like_list_unikeys))
                    self.re.set(self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME, "==".join(self.error_mood_unikeys))
        except BaseException as e:
            self.format_error(e, 'Faild to save data in redis')

    def save_data_to_json(self, data, file_name):
        try:
            with open(file_name, 'w', encoding='utf-8') as w2:
                json.dump(data, w2, ensure_ascii=False)
        except BaseException as e:
            self.format_error(e, 'Failed to save file:' + file_name)

    def save_data_to_txt(self, data, file_name):
        try:
            with open(file_name, 'w', encoding='utf-8') as w:
                w.write(";".join(data))
        except BaseException as e:
            self.format_error(e, 'Failed to save file:' + file_name)

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
    def get_like_list(self, unikey):
        url = self.get_aggree_url(unikey)
        if (self.debug):
            print('获取点赞的人', url)
        try:
            like_list = self.req.get(url=url, headers=self.headers)
            like_list_detail = self.get_json(like_list.content.decode('utf-8'))
            return like_list_detail
        except BaseException:
            try:
                like_list = self.req.get(url=url, headers=self.headers)
                like_list_detail = self.get_json(like_list.content.decode('utf-8'))
                return like_list_detail
            except BaseException as e:
                self.format_error(e, 'Failed to get agree:' + url)
                self.error_like_list_unikeys.append(unikey)
                return {}

    # 获得每一条说说的详细内容
    def get_mood_detail(self, unikey, tid):
        url_detail = self.get_mood_detail_url(unikey, tid)
        if (self.debug):
            print('获取说说动态详情:', url_detail)
        try:
            mood_detail = self.req.get(url=url_detail, headers=self.headers)
            json_mood = self.get_json(str(mood_detail.content.decode('utf-8')))
            return json_mood
        except BaseException:
            try:
                mood_detail = self.req.get(url=url_detail, headers=self.headers)
                json_mood = self.get_json(str(mood_detail.content.decode('utf-8')))
                return json_mood
            except BaseException as e:
                self.format_error(e, 'Failed to get mood_detail:' + url_detail)
                self.error_mood_unikeys.append((unikey, tid))
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
            big_pic_list = []

            if 'pic' in item:
                item_key = item['pic']
                # 保存所有图片的预览图下载地址
                for i in range(len(item_key)):
                    if 'smallurl' in item_key[i]:
                        smallurl = item_key[i]['smallurl']
                        pic_list.append(smallurl)
                    if 'url2' in item_key[i]:
                        big_url = item_key[i]['url2']
                        big_pic_list.append(big_url)

                # 如果存在多张图片或没有图片
                if len(item_key) != 1:
                    curlikekey = unikey + "<.>" + unikey
                else:
                    curlikekey = item_key[0]['curlikekey']
                # curlikekey_list.append(curlikekey)
            else:
                curlikekey = unikey + "<.>" + unikey

            unikey_tid_list.append(
                dict(unikey=unikey, tid=tid, small_pic_list=pic_list, curlikekey=curlikekey, big_pic_list=big_pic_list))
        return unikey_tid_list

    def download_image(self, url, name):
        image_url = url
        try:
            r = self.req.get(url=image_url, headers=self.headers)
            image_content = (r.content)
            file_image = open(name + '.jpg', 'wb+')
            file_image.write(image_content)
            file_image.close()
        except BaseException as e:
            self.format_error(e, 'Failed to download image:' + name)

    def result_report(self):
        print("#######################")
        print('爬取用户:', self.__username)
        print('总耗时:', (datetime.datetime.now() - self.begin_time).seconds / 60, '分钟')
        print('QQ空间动态数据数量:', len(self.mood_details))
        print('最终失败的数据量:')
        print('--------------')
        print('动态:', len(self.error_mood_unikeys))
        print('点赞详情（包括浏览量）:', len(self.error_like_detail_unikeys))
        print('点赞好友列表:', len(self.error_like_list_unikeys))
        print('--------------')
        print("########################")

    def connect_redis(self):
        try:
            pool = redis.ConnectionPool(host="127.0.0.1", port=6379, decode_responses=True)
            re = redis.Redis(connection_pool=pool)
            return re
        except BaseException as e:
            print('Error===================')
            print(e)
            print('Failed to connect redis')
            print('===================')


def capture_data():
    sp = Spider(use_redis=True, debug=True, file_name_head='maicius')
    sp.login()
    sp.get_mood_list(mood_begin=0, mood_num=-1, download_small_image=False, download_big_image=True,
                     download_mood_detail=False, download_like_detail=False, download_like_names=False, recover=False, )


if __name__ == '__main__':
    capture_data()
