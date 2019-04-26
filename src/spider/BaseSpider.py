import datetime
from src.util import util
from copy import deepcopy
import json
from src.util.constant import BASE_DIR
import re
import logging
import redis
from src.web.entity.UserInfo import UserInfo

class BaseSpider(object):
    """
    基类，初始化与爬虫相关的工具和方法
    """
    def __init__(self, use_redis=False, debug=False, mood_begin=0, mood_num=-1, stop_time='-1',
                 download_small_image=False, download_big_image=False,
                 download_mood_detail=True, download_like_detail=True, download_like_names=True, recover=False,
                 cookie_text=None):
        # 初始化下载项
        self.mood_begin = mood_begin
        self.mood_num = mood_num
        self.recover = recover
        self.download_small_image = download_small_image
        self.download_big_image = download_big_image
        self.download_mood_detail = download_mood_detail
        self.download_like_detail = download_like_detail
        self.download_like_names = download_like_names
        self.thread_num = 10
        self.thread_list = []
        if stop_time != '-1':
            self.stop_time = util.get_mktime(stop_time)
        else:
            self.stop_time = -1
        self.begin_time = datetime.datetime.now()
        self.host = 'https://user.qzone.qq.com'
        self.http_host = 'http://user.qzone.qq.com'
        self.use_redis = use_redis
        self.debug = debug
        self.cookie_text = cookie_text
        self.username, self.password, self.file_name_head, self.nick_name = self.get_username_password()
        self.mood_host = self.http_host + '/' + self.username + '/mood/'
        # 在爬取好友动态时username会变为好友的QQ号，所以此处需要备份
        self.raw_username = deepcopy(self.username)
        self.headers = {
            'host': 'user.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:66.0) Gecko/20100101 Firefox/66.0',
            'connection': 'keep-alive'
        }
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=BASE_DIR + 'log/' + self.username + '.log',
                            filemode='w+')
        if (use_redis):
            self.re = self.connect_redis()

        self.user_info = UserInfo().load(self.username)
        if self.user_info is None:
            self.user_info = UserInfo()
        self.user_info.QQ = self.username
        self.user_info.nickname = self.nick_name

    def get_username_password(self):
        config_path = BASE_DIR + 'config/userinfo.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as r:
                userinfo = json.load(r)
            return userinfo['username'], userinfo['password'], userinfo['file_name_head'], userinfo['nick_name']
        except:
            print("Error: File Not Found==============")
            print("请检查配置文件是否正确配置!!!!")
            print("Please check config file")
            print("Path:", config_path)
            exit(1)

    # 将响应字符串转化为标准Json
    def get_json(self, str1):
        arr = re.findall(r'[^()]+', str1)
        json = ""
        for i in range(1, len(arr) - 1):
            json += arr[i]
        return json

    # 从本地恢复数据（用于爬虫意外中断之后的数据恢复）
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

    def init_parameter(self):
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


    def init_file_name(self, file_name_head):
        logging.info('file_name_head:' + self.file_name_head)
        DATA_DIR_HEAD = BASE_DIR + 'data/' + file_name_head
        self.CONTENT_FILE_NAME = DATA_DIR_HEAD + '_QQ_content.json'
        self.LIKE_DETAIL_FILE_NAME = DATA_DIR_HEAD + '_QQ_like_detail' + '.json'
        self.LIKE_LIST_NAME_FILE_NAME = DATA_DIR_HEAD + '_QQ_like_list_name' + '.json'
        self.MOOD_DETAIL_FILE_NAME = DATA_DIR_HEAD + '_QQ_mood_detail' + '.json'

        ERROR_DIR_HEAD = BASE_DIR + 'error/' + file_name_head
        self.ERROR_LIKE_DETAIL_FILE_NAME = ERROR_DIR_HEAD + '_QQ_like_detail_error' + '.json'
        self.ERROR_LIKE_LIST_NAME_FILE_NAME = ERROR_DIR_HEAD + '_QQ_like_list_name_error' + '.json'
        self.ERROR_MOOD_DETAIL_FILE_NAME = ERROR_DIR_HEAD + '_QQ_mood_detail_error' + '.json'
        self.ERROR_LIKE_DETAIL_UNIKEY_FILE_NAME = ERROR_DIR_HEAD + '_QQ_like_detail_error_unikey' + '.txt'
        self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME = ERROR_DIR_HEAD + '_QQ_like_list_error_unikey' + '.txt'
        self.ERROR_MOOD_DETAIL_UNIKEY_FILE_NAME = ERROR_DIR_HEAD + '_QQ_mood_detail_error_unikey' + '.txt'


        self.SMALL_IMAGE_DIR = BASE_DIR + 'qq_image/' + file_name_head + '/'
        self.BIG_IMAGE_DIR = BASE_DIR + 'qq_big_image/' + file_name_head + '/'
        util.check_dir_exist(DATA_DIR_HEAD)
        util.check_dir_exist(ERROR_DIR_HEAD)
        util.check_dir_exist(self.SMALL_IMAGE_DIR)
        util.check_dir_exist(self.BIG_IMAGE_DIR)
        print("Init file Name Finish:", file_name_head)

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

    def save_data_to_redis(self, final_result=False):
        """
        保存数据到redis中
        :param final_result: 是否为最终结果，如果是，则会保存错误信息，如果不是，则仅做缓存
        :return:
        """
        try:
            if self.use_redis:
                self.re.set(self.CONTENT_FILE_NAME[5:], json.dumps(self.content, ensure_ascii=False))

                if self.download_like_names:
                    self.re.set(self.LIKE_LIST_NAME_FILE_NAME[5:],
                                json.dumps(self.like_list_names, ensure_ascii=False))

                if self.download_mood_detail:
                    self.re.set(self.MOOD_DETAIL_FILE_NAME[5:],
                                json.dumps(self.mood_details, ensure_ascii=False))

                if self.download_like_detail:
                    self.re.set(self.LIKE_DETAIL_FILE_NAME[5:],
                                json.dumps(self.like_detail, ensure_ascii=False))

                if final_result:
                    if self.download_like_detail:
                        self.re.set(self.ERROR_LIKE_DETAIL_FILE_NAME[6:],
                                    json.dumps(self.error_like_detail, ensure_ascii=False))
                        self.re.set(self.ERROR_LIKE_DETAIL_UNIKEY_FILE_NAME, "==".join(self.error_like_detail_unikeys))

                    if self.download_like_names:
                        self.re.set(self.ERROR_LIKE_LIST_NAME_FILE_NAME[6:],
                                    json.dumps(self.error_like_list, ensure_ascii=False))
                        self.re.set(self.ERROR_LIKE_LIST_NAME_UNIKEY_FILE_NAME, "==".join(self.error_like_list_unikeys))

                    if self.download_mood_detail:
                        self.re.set(self.ERROR_MOOD_DETAIL_FILE_NAME[6:],
                                    json.dumps(self.error_mood, ensure_ascii=False))
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
        try:
            pool = redis.ConnectionPool(host="127.0.0.1", port=6379, decode_responses=True)
            re = redis.Redis(connection_pool=pool)
            return re
        except BaseException as e:
            print('Error===================')
            print(e)
            print('Failed to connect redis')
            print('===================')

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