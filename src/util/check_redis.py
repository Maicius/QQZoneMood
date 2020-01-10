# coding = utf-8
import os
import time
import datetime
import redis
import re
from src.util import util
from src.util.constant import BASE_DIR, WEB_IMAGE_PATH

WAITING_USER_LIST = 'waiting_user_list'

class CheckUser(object):
    def __init__(self, host):
        self.user_set = set()
        self.user_dict = {}
        self.pool = redis.ConnectionPool(host=host, port=6379, decode_responses=True)
        self.user_file_dict = {}
        # date = datetime.datetime.now().strftime('%Y-%m-%d')
        # logging_dir = BASE_DIR + 'user_log/'
        # print("logging_user_dir:", logging_dir)
        # util.check_dir_exist(logging_dir)
        # logging.basicConfig(level=logging.INFO,
        #                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        #                     datefmt='%a, %d %b %Y %H:%M:%S',
        #                     filename=logging_dir + date + '.log',
        #                     filemode='w+')

    def check_exist(self):
        # logging.info(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + 'database is running')
        conn = redis.Redis(connection_pool=self.pool)
        waiting_user_set = set(conn.lrange(WAITING_USER_LIST, 0, -1))
        if not self.user_set:
            self.user_set = waiting_user_set
        else:
            self.user_set = self.user_set.intersection(waiting_user_set)
        for item in self.user_set:
            if item not in self.user_dict:
                self.user_dict[item] = 1
            else:
                self.user_dict[item] += 1
            # logging.info(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'---' + item + ':' + str(self.user_dict[item]))
        indexs = self.user_dict.keys()

        for index in indexs:
            if index not in self.user_set:
                # logging.info(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'---' + index + ' no longer exist, delete it from dict')
                self.user_dict[index] = 0
            if self.user_dict[index] >= 10:
                conn.lrem(WAITING_USER_LIST, 0, index)
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'---' + index + ' time >= 10, delete it from redis')
                self.user_dict[index] = 0
        cu.check_user_file()

    def check_user_file(self):
        file_list = os.listdir(BASE_DIR)
        user_file_list = []
        for file in file_list:
            if re.match('[0-9]+', file):
                user_file_list.append(file)
        # print(user_file_list)
        for user_file in user_file_list:
            if user_file in self.user_file_dict:
                self.user_file_dict[user_file] += 1
                if self.user_file_dict[user_file] > 60 * 24:
                    DATA_DIR_KEY = BASE_DIR + user_file + '/'
                    WEB_IMAGE_PATH_DIR = WEB_IMAGE_PATH + user_file + '/'
                    os.system("rm -rf " + DATA_DIR_KEY)
                    os.system("rm -rf " + WEB_IMAGE_PATH_DIR)
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'---' + user_file + ' time >= 24小时, delete it')
            else:
                self.user_file_dict[user_file] = 1

        indexs = self.user_dict.keys()
        for index in indexs:
            if index not in user_file_list:
                self.user_file_dict.pop(index)



if __name__ == '__main__':
    cu = CheckUser("127.0.0.1")
    while True:
        cu.check_exist()
        time.sleep(2)
    # while True:
    #     cu.check_user_file()
    #     time.sleep(2)