import datetime

from src.threadPool.ImageThreadPool import ImageThreadPool
from src.util import util
from copy import deepcopy
import json
from src.util.constant import BASE_DIR, EXPIRE_TIME_IN_SECONDS, BASE_PATH, QR_CODE_MAP_KEY
import re
import logging
from src.web.entity.UserInfo import UserInfo
from src.web.web_util.web_util import get_redis_conn
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import threading
import random

class BaseSpider(object):
    """
    基类，初始化与爬虫相关的工具和方法
    """
    def __init__(self, use_redis=False, debug=False, mood_begin=0, mood_num=-1, stop_time='-1',
                 download_small_image=False, download_big_image=False,
                 download_mood_detail=True, download_like_detail=True, download_like_names=True, recover=False,
                 cookie_text=None, from_web=False, username='', nickname='', no_delete=True, pool_flag='127.0.0.1', from_client=False):
        # 初始化下载项
        self.mood_begin = mood_begin
        self.mood_num = mood_num
        self.recover = recover
        self.download_small_image = download_small_image
        self.download_big_image = download_big_image
        self.download_mood_detail = download_mood_detail
        self.download_like_detail = download_like_detail
        self.download_like_names = download_like_names
        # 控制线程数量，包括获取动态的线程数量和好友数据的线程数量，默认为10，这里表示两个子任务都开启10个线程
        self.thread_num = 10
        self.thread_list = []
        self.from_client = from_client
        self.no_delete = no_delete
        if stop_time != '-1':
            self.stop_time = util.get_mktime(stop_time)
        else:
            self.stop_time = -1
        self.begin_time = datetime.datetime.now()
        self.host = 'https://user.qzone.qq.com'
        self.h5_host = 'h5.qzone.qq.com'
        self.http_host = 'http://user.qzone.qq.com'
        self.use_redis = use_redis
        self.debug = debug
        self.cookie_text = cookie_text
        self.pool_flag = pool_flag
        self.from_web = from_web
        self.random_qr_name = str(random.random())
        self.QR_CODE_PATH  = BASE_PATH + '/src/web/static/image/qr' + self.random_qr_name
        self.headers = {
            'host': 'user.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:66.0) Gecko/20100101 Firefox/66.0',
            'connection': 'keep-alive'
        }
        self.h5_headers = deepcopy(self.headers)
        self.h5_headers['host'] = self.h5_host
        if use_redis:
            self.re = self.connect_redis()

        if not from_web and not from_client:
            self.username, self.password, self.nickname = self.get_username_password()

        else:
            self.username = username
            self.nickname = nickname
            # 保存用户的二维码名称，传递给前端
            if self.use_redis:
                self.re.hset(QR_CODE_MAP_KEY, self.username, self.random_qr_name)
        self.init_user_info()

        self.image_thread_pool = ImageThreadPool(20)

    def init_user_info(self):
        self.init_file_name()
        self.mood_host = self.http_host + '/' + self.username + '/mood/'
        # 在爬取好友动态时username会变为好友的QQ号，所以此处需要备份
        self.raw_username = deepcopy(self.username)
        self.raw_nickname = deepcopy(self.nickname)
        self.user_info = UserInfo(self.username).load()
        if self.user_info is None:
            self.user_info = UserInfo(self.username)
        self.user_info.QQ = self.username
        self.user_info.nickname = self.nickname


    def get_username_password(self):
        config_path = BASE_DIR + 'config/userinfo.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as r:
                userinfo = json.load(r)
            return userinfo['username'], userinfo['password'], userinfo['nick_name']
        except:
            print("Error: File Not Found==============")
            print("请检查配置文件是否正确配置!!!!")
            print("Please check config file")
            print("Path:", config_path)
            exit(1)

    # 将响应字符串转化为标准Json
    def get_json(self, str1):
        arr = re.findall(r'[^()]+', str1)
        # for i in range(1, len(arr) - 1):
        #     json += arr[i]
        json = "".join(arr[1:-1])
        return json.strip()

    # 从本地恢复数据（用于爬虫意外中断之后的数据恢复）
    def do_recover_from_exist_data(self):
        if self.use_redis:
            try:
                self.content = json.loads(self.re.get(self.CONTENT_FILE_NAME))
                self.like_list_names = json.loads(self.re.get(self.LIKE_LIST_NAME_FILE_NAME))
                self.mood_details = json.loads(self.re.get(self.MOOD_DETAIL_FILE_NAME))
                self.like_detail = json.loads(self.re.get(self.LIKE_DETAIL_FILE_NAME))
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

    def format_error(self, e, msg=""):
        print('ERROR===================')
        print(e)
        print(msg)
        logging.error(e)
        logging.error(msg)
        print('ERROR===================')
        if self.debug:
            # raise e
            pass

    def logging_info(self, info):
        logging.info(info)

    def init_parameter(self):
        self.mood_count = 0
        self.like_detail = []
        self.like_list_names = []
        self.content = []
        self.unikeys = []
        self.tid = ""
        self.mood_details = []
        self.error_like_detail_unikeys = []
        self.error_like_list_unikeys = []
        self.error_mood_unikeys = []
        self.error_like_detail = {}
        self.error_like_list = {}
        self.error_mood = {}
        self.until_stop_time = True


    def init_file_name(self):
        """
        初始化所有文件名
        :return:
        """
        self.USER_BASE_DIR = BASE_DIR + self.username + '/'
        logging_dir = self.USER_BASE_DIR + 'log/'
        if self.debug:
            print("logging_dir:", logging_dir)
        util.check_dir_exist(logging_dir)
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=logging_dir + self.username + '.log',
                            filemode='w+')
        logging.info('file_name_head:' + self.username)

        DATA_DIR_HEAD = self.USER_BASE_DIR + 'data/'
        self.CONTENT_FILE_NAME = DATA_DIR_HEAD + 'QQ_content.json'
        self.LIKE_DETAIL_FILE_NAME = DATA_DIR_HEAD + 'QQ_like_detail' + '.json'
        self.LIKE_LIST_NAME_FILE_NAME = DATA_DIR_HEAD + 'QQ_like_list_name' + '.json'
        self.MOOD_DETAIL_FILE_NAME = DATA_DIR_HEAD + 'QQ_mood_detail' + '.json'

        ERROR_DIR_HEAD = self.USER_BASE_DIR + 'error/'
        self.ERROR_LIKE_DETAIL_FILE_NAME = ERROR_DIR_HEAD + 'QQ_like_detail_error' + '.json'
        self.ERROR_LIKE_LIST_NAME_FILE_NAME = ERROR_DIR_HEAD + 'QQ_like_list_name_error' + '.json'
        self.ERROR_MOOD_DETAIL_FILE_NAME = ERROR_DIR_HEAD + 'QQ_mood_detail_error' + '.json'
        self.ERROR_LIKE_DETAIL_UNIKEY_FILE_NAME = ERROR_DIR_HEAD + 'QQ_like_detail_error_unikey' + '.txt'
        self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME = ERROR_DIR_HEAD + 'QQ_like_list_error_unikey' + '.txt'
        self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME = ERROR_DIR_HEAD + 'QQ_mood_detail_error_unikey' + '.txt'

        self.SMALL_IMAGE_DIR = self.USER_BASE_DIR + 'qq_image/'
        self.BIG_IMAGE_DIR = self.USER_BASE_DIR + 'qq_big_image/'
        util.check_dir_exist(DATA_DIR_HEAD)
        util.check_dir_exist(ERROR_DIR_HEAD)
        util.check_dir_exist(self.SMALL_IMAGE_DIR)
        util.check_dir_exist(self.BIG_IMAGE_DIR)

        USER_BASE_DIR = BASE_DIR + self.username + '/'
        util.check_dir_exist(USER_BASE_DIR)
        FRIEND_DIR_HEAD = USER_BASE_DIR + 'friend/'
        self.FRIEND_LIST_FILE_NAME = FRIEND_DIR_HEAD + 'friend_list.json'
        self.FRIEND_DETAIL_FILE_NAME = FRIEND_DIR_HEAD + 'friend_detail.json'
        self.FRIEND_DETAIL_LIST_FILE_NAME = FRIEND_DIR_HEAD + 'friend_detail_list.csv'
        self.FRIEND_DETAIL_EXCEL_FILE_NAME = FRIEND_DIR_HEAD + 'friend_detail_list.xlsx'
        # 头像下载到web的static文件夹，以便在web中调用

        self.FRIEND_HEADER_IMAGE_PATH = BASE_PATH + '/src/web/static/image/' + self.username + '/header/'
        self.web_image_bash_path = BASE_PATH + '/src/web/static/image/'+ self.username + '/'
        util.check_dir_exist(USER_BASE_DIR + 'friend/')
        util.check_dir_exist(self.FRIEND_HEADER_IMAGE_PATH)
        self.init_analysis_path()
        if self.debug:
            print("Init file Name Finish:", self.USER_BASE_DIR)

    def init_analysis_path(self):
        self.friend_dir = BASE_DIR + self.username + '/friend/' + 'friend_detail_list.csv'
        self.history_like_agree_file_name = BASE_DIR +  self.username + '/friend/' + 'history_like_list.json'
        RESULT_BASE_DIR = self.USER_BASE_DIR + "data/result/"

        self.MOOD_DATA_FILE_NAME = RESULT_BASE_DIR + 'mood_data.csv'
        self.MOOD_DATA_EXCEL_FILE_NAME = RESULT_BASE_DIR + 'mood_data.xlsx'

        LABEL_BASE_DIR = self.USER_BASE_DIR + "data/label/"
        self.LABEL_FILE_CSV = LABEL_BASE_DIR + 'label_data.csv'
        self.LABEL_FILE_EXCEL = LABEL_BASE_DIR + 'label_data.xlsx'

        self.label_path = self.USER_BASE_DIR + 'data/label/'
        self.image_path = self.USER_BASE_DIR + 'image/'
        util.check_dir_exist(RESULT_BASE_DIR)
        util.check_dir_exist(LABEL_BASE_DIR)
        util.check_dir_exist(self.label_path)
        util.check_dir_exist(self.image_path)

    def load_all_data_from_json(self):
        self.content = self.load_data_from_json(self.CONTENT_FILE_NAME)
        self.like_list_names = self.load_data_from_json(self.LIKE_LIST_NAME_FILE_NAME)
        self.mood_details = self.load_data_from_json(self.MOOD_DETAIL_FILE_NAME)
        self.like_detail = self.load_data_from_json(self.LIKE_DETAIL_FILE_NAME)
        print("Success to Load Data From Json")

    def load_data_from_json(self, file_name):
        try:
            with open(file_name, encoding='utf-8') as content:
                data = json.load(content)
            return data
        except BaseException as e:
            self.format_error(e, 'Failed to load data ' + file_name)

    def delete_cache(self):
        self.re.delete(self.LIKE_LIST_NAME_FILE_NAME)
        self.re.delete(self.MOOD_DETAIL_FILE_NAME)
        self.re.delete(self.LIKE_DETAIL_FILE_NAME)

    def save_data_to_redis(self, final_result=False):
        """
        保存数据到redis中
        :param final_result: 是否为最终结果，如果是，则会保存错误信息，如果不是，则仅做缓存
        :return:
        """
        try:
            if self.use_redis:
                self.re.set(self.CONTENT_FILE_NAME, json.dumps(self.content, ensure_ascii=False))

                if self.download_like_names:
                    self.re.set(self.LIKE_LIST_NAME_FILE_NAME,
                                json.dumps(self.like_list_names, ensure_ascii=False))

                if self.download_mood_detail:
                    self.re.set(self.MOOD_DETAIL_FILE_NAME,
                                json.dumps(self.mood_details, ensure_ascii=False))

                if self.download_like_detail:
                    self.re.set(self.LIKE_DETAIL_FILE_NAME,
                                json.dumps(self.like_detail, ensure_ascii=False))

                if not self.no_delete:
                    self.re.expire(self.LIKE_LIST_NAME_FILE_NAME, EXPIRE_TIME_IN_SECONDS)
                    self.re.expire(self.MOOD_DETAIL_FILE_NAME, EXPIRE_TIME_IN_SECONDS)
                    self.re.expire(self.LIKE_DETAIL_FILE_NAME, EXPIRE_TIME_IN_SECONDS)

                if final_result:
                    if self.download_like_detail:
                        self.re.set(self.ERROR_LIKE_DETAIL_FILE_NAME,
                                    json.dumps(self.error_like_detail, ensure_ascii=False))
                        self.re.set(self.ERROR_LIKE_DETAIL_UNIKEY_FILE_NAME, "==".join(self.error_like_detail_unikeys))

                    if self.download_like_names:
                        self.re.set(self.ERROR_LIKE_LIST_NAME_FILE_NAME,
                                    json.dumps(self.error_like_list, ensure_ascii=False))
                        self.re.set(self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME, "==".join(self.error_like_list_unikeys))

                    if self.download_mood_detail:
                        self.re.set(self.ERROR_MOOD_DETAIL_FILE_NAME,
                                    json.dumps(self.error_mood, ensure_ascii=False))
                        self.re.set(self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME, "==".join(self.error_mood_unikeys))

                    if not self.no_delete:
                        self.re.expire(self.ERROR_LIKE_DETAIL_FILE_NAME, EXPIRE_TIME_IN_SECONDS)
                        self.re.expire(self.ERROR_LIKE_DETAIL_UNIKEY_FILE_NAME, EXPIRE_TIME_IN_SECONDS)
                        self.re.expire(self.ERROR_LIKE_LIST_NAME_FILE_NAME, EXPIRE_TIME_IN_SECONDS)
                        self.re.expire(self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME, EXPIRE_TIME_IN_SECONDS)
                        self.re.expire(self.ERROR_MOOD_DETAIL_FILE_NAME, EXPIRE_TIME_IN_SECONDS)
                        self.re.expire(self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME, EXPIRE_TIME_IN_SECONDS)

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

    def save_all_data_to_json(self):
        self.save_data_to_json(data=self.content, file_name=self.CONTENT_FILE_NAME)
        if self.download_mood_detail:
            self.save_data_to_json(data=self.mood_details, file_name=self.MOOD_DETAIL_FILE_NAME)
            self.save_data_to_json(data=self.error_mood, file_name=self.ERROR_MOOD_DETAIL_FILE_NAME)
            self.save_data_to_txt(data=self.error_mood_unikeys, file_name=self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME)

        if self.download_like_names:
            self.save_data_to_json(data=self.like_detail, file_name=self.LIKE_DETAIL_FILE_NAME)
            self.save_data_to_json(data=self.error_like_detail, file_name=self.ERROR_LIKE_DETAIL_FILE_NAME)
            self.save_data_to_txt(data=self.error_like_detail_unikeys, file_name=self.ERROR_LIKE_DETAIL_FILE_NAME)

        if self.download_like_detail:
            self.save_data_to_json(data=self.like_list_names, file_name=self.LIKE_LIST_NAME_FILE_NAME)
            self.save_data_to_json(data=self.error_like_list, file_name=self.ERROR_LIKE_LIST_NAME_FILE_NAME)
            self.save_data_to_txt(data=self.error_like_list_unikeys,
                                  file_name=self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME)

        self.save_data_to_redis(final_result=True)

    def connect_redis(self):
        conn = get_redis_conn(self.pool_flag)
        if conn is None:
            print("连接数据库失败")
            exit(1)
        else:
            return conn

    def check_time(self, mood, stop_time, until_stop_time=True):
        create_time = mood['created_time']
        if self.debug:
            print('time:', create_time, stop_time)
        if stop_time >= create_time:
            until_stop_time = False
            print('达到设置的停止时间，即将退出爬虫')
            return until_stop_time
        else:
            return until_stop_time

    def check_comment_num(self, mood):
        cmt_num = mood['cmtnum']
        if cmt_num > 20:
            return cmt_num
        else:
            return -1

    def download_image(self, url, name):
        image_url = url
        try:
            r = self.req.get(url=image_url, headers=self.headers, timeout=20)
            image_content = r.content
            # 异步保存图片，提高效率
            # t = threading.Thread(target=self.save_image_concurrent, args=(image_content, name))
            # t.start()
            thread = self.image_thread_pool.get_thread()
            t = thread(target=self.save_image_concurrent, args=(image_content, name))
            t.start()
            # t = self.image_thread_pool2.submit(self.save_image_concurrent, (image_content, name))
        except BaseException as e:
            self.format_error(e, 'Failed to download image:' + name)

    def save_image_concurrent(self, image, name):
        try:
            file_image = open(name + '.jpg', 'wb+')
            file_image.write(image)
            file_image.close()
            self.image_thread_pool.add_thread()
        except BaseException as e:
            self.format_error(e, "Failed to save image:" + name)

    def save_image_single(self, image, name):
        try:
            file_image = open(name + '.jpg', 'wb+')
            file_image.write(image)
            file_image.close()
        except BaseException as e:
            self.format_error(e, "Failed to save image:" + name)

    def show_image(self, file_path):
        t = threading.Thread(target=self.do_show_image, args=(file_path,))
        t.start()

    def do_show_image(self, file_path):
        image = mpimg.imread(file_path)
        plt.imshow(image)
        plt.axis('off')
        plt.show()

    def result_report(self):
        print("#######################")
        print('爬取用户:', self.username)
        print('总耗时:', (datetime.datetime.now() - self.begin_time).seconds / 60, '分钟')
        print('QQ空间动态数据数量:', len(self.mood_details))
        print('最终失败的数据量:')
        print('--------------')
        print('动态:', len(self.error_mood_unikeys))
        print('点赞详情（包括浏览量）:', len(self.error_like_detail_unikeys))
        print('点赞好友列表:', len(self.error_like_list_unikeys))
        print('--------------')
        print("########################")