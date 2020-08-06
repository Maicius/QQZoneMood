import time
import os
import pandas as pd
import re
# %a 星期的简写。如 星期三为Web
# %A 星期的全写。如 星期三为Wednesday
# %b 月份的简写。如4月份为Apr
# %B 月份的全写。如4月份为April
# %c:  日期时间的字符串表示。（如： 04/07/10 10:43:39）
# %d:  日在这个月中的天数（是这个月的第几天）
# %f:  微秒（范围[0,999999]）
# %H:  小时（24小时制，[0, 23]）
# %I:  小时（12小时制，[0, 11]）
# %j:  日在年中的天数 [001,366]（是当年的第几天）
# %m:  月份（[01,12]）
# %M:  分钟（[00,59]）
# %p:  AM或者PM
# %S:  秒（范围为[00,61]，为什么不是[00, 59]，参考python手册~_~）
# %U:  周在当年的周数当年的第几周），星期天作为周的第一天
# %w:  今天在这周的天数，范围为[0, 6]，6表示星期天
# %W:  周在当年的周数（是当年的第几周），星期一作为周的第一天
# %x:  日期字符串（如：04/07/10）
# %X:  时间字符串（如：10:43:39）
# %y:  2个数字表示的年份
# %Y:  4个数字表示的年份
# %z:  与utc时间的间隔 （如果是本地时间，返回空字符串）
# %Z:  时区名称（如果是本地时间，返回空字符串）
# %%:  %% => %
# Oct 19, 2017 12:00:00 AM
# May 27, 2015 12:00:00 AM
from src.util.constant import WAITING_USER_LIST, BASE_DIR, WEB_IMAGE_PATH, USER_MAP_KEY


def get_short_date(date):
    time_array = time.strptime(date, "%Y-%m-%d")
    return time.strftime("%Y%m%d", time_array)


def get_standard_date(date):
    time_array = time.strptime(date, "%b %d, %Y %X %p")
    return time.strftime("%Y-%m-%d", time_array)


def get_standard_date2(date):
    time_array = time.strptime(date, "%Y-%m-%d %X")
    return time.strftime("%Y-%m-%d", time_array)



# 将字符串时间转换为时间戳
def get_mktime(date_string):
    return time.mktime(time.strptime(date_string, '%Y-%m-%d'))

# 将字符串时间转换为时间戳
def get_mktime2(date_string):
    return time.mktime(time.strptime(date_string, '%Y年%m月%d日'))

# 将时间戳转化为标准时间
def get_standard_time_from_mktime(mktime):
    return time.strftime("%Y-%m-%d", time.localtime(mktime))

# 将时间戳转化为标准时间3
def get_standard_time_from_mktime3(mktime):
    return time.strftime("%Y-%m-%d", time.localtime(mktime))


def get_standard_time_from_mktime2(mktime):
    temp = time.strftime("%Y-%m-%d", time.localtime(mktime))
    return get_mktime(temp)

def get_full_time_from_mktime(mktime):
    return time.strftime("%Y-%m-%d %X", time.localtime(mktime))


def get_month(date):
    time_array = time.strptime(str(date), "%Y-%m-%d")
    return time.strftime("%Y-%m", time_array)

def check_dir_exist(dir):
    if os.path.exists(dir) == False:
        os.makedirs(dir)

def open_file_list(path, open_data_frame = False):
    path_dir = os.listdir(path)
    if open_data_frame:
        df = pd.DataFrame()
    else:
        page_list = []
    for dir in path_dir:
        print('open dir:', dir, '...')
        file_name = path + dir
        if open_data_frame:
            data_df = do_read_csv(file_name)
            df = pd.concat([df, data_df], axis=0)
        else:
            data = do_open_file(file_name=file_name)
            page_list.append(data)

    if open_data_frame:
        return df
    else:
        return page_list




def do_open_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as r:
        try:
            data = r.read()
            print(file_name)
            return data
        except BaseException as e:
            format_error(e, file_name + "file error")

def get_file_full_path(path):
    path_dir = os.listdir(path)
    file_name_list = []
    for dir in path_dir:
        file_name = path + dir
        file_name_list.append(file_name)
    return file_name_list

def get_file_list(path):
    return os.listdir(path)

def do_read_csv(file_name):
    if file_name.find('.csv') != -1:
        data = pd.read_csv(file_name)
        return data
    elif file_name.find('.xlsx') != -1:
        data = pd.read_excel(file_name)
        return data
    else:
        return pd.DataFrame()


def format_error(e, msg=""):
    print('ERROR===================')
    print(e)
    print(msg)
    print('ERROR===================')

def date_to_millis(d):
    return int(time.mktime(d.timetuple())) * 1000

def remove_waste_emoji(text):
    text = re.subn(re.compile('\[em\].*?\[\/em\]'), '', text)[0]
    text = re.subn(re.compile('@\{.*?\}'), '', text)[0]
    return text

extra_chars = set("\"\'!#$%&\()*+,-./:;<=>?@[\\]^_`{|}~！#￥%&？《》{}“”，：‘’。（）·、；【】")
def remove_special_tag(text):
    all_tag = set(re.findall(u'[^\u4e00-\u9fa5a-zA-Z0-9\*]', text))
    special_tag = all_tag.difference(extra_chars)
    for tag in special_tag:
        text = text.replace(tag, '')
    return text

def test_remove_special_tag():
    text1 = "🌕🍙"
    text2 = "LoToRy.🤓"
    text3 = "一棵树的头像🤔"
    text4 = "{\"name\": \"高冷的逗比\"}"
    assert "" == remove_special_tag(text1)
    assert "LoToRy." == remove_special_tag(text2)
    assert "一棵树的头像" == remove_special_tag(text3)
    assert "{\"name\":\"高冷的逗比\"}" == remove_special_tag(text4)

def do_clear_data_by_user(QQ, conn):
    DATA_DIR_KEY = BASE_DIR + QQ + '/'
    WEB_IMAGE_PATH_DIR = WEB_IMAGE_PATH + QQ + '/'
    if os.path.exists(DATA_DIR_KEY):
        # 删除有QQ号的所有key
        # 该方法在docker中无法使用，因为该容器内无redis-cli
        # delete_cmd = "redis-cli KEYS \"*" + QQ + "*\"|xargs redis-cli DEL"
        # print(delete_cmd)
        # os.system(delete_cmd)
        # 删除 该路径下所有文件
        os.system("rm -rf " + DATA_DIR_KEY)
        os.system("rm -rf " + WEB_IMAGE_PATH_DIR)
        conn.hdel(USER_MAP_KEY, QQ)
        conn.lrem(WAITING_USER_LIST, 0, QQ)
        # redis的del不支持正则表达式，因此只能循环删除
        all_keys = conn.keys("*" + QQ + "*")
        print()
        for key in all_keys:
            conn.delete(key)
        # os.removedirs(os.path.join(BASE_DIR, QQ))
        finish = 1
    else:
        finish = 2
    return finish

def get_standard_time_with_name(time):
    time_list = time.split('-')
    time = time_list[0] + '年' + time_list[1] + '月' + time_list[2] + '日'
    return time

if __name__ =='__main__':
    print(get_mktime('2018-09-6'))
    print(get_standard_time_with_name('2018-9-06'))
    print(get_standard_time_from_mktime3(1566545874))
    print(get_full_time_from_mktime(1566545874))
    test_remove_special_tag()
