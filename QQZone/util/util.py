import time
import os
import pandas as pd
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

# 将时间戳转化为标准时间
def get_standard_time_from_mktime(mktime):
    return time.strftime("%Y-%m-%d", time.localtime(mktime))


def get_month(date):
    time_array = time.strptime(str(date), "%Y-%m-%d")
    return time.strftime("%Y-%m", time_array)

def check_file_exist(dir):
    if os.path.exists(dir) == False:
        os.makedirs(dir)

def open_file_list(path, open_data_frame = False):
    path_dir = os.listdir(path)
    if open_data_frame:
        df = pd.DataFrame()
    else:
        page_list = []
    for dir in path_dir:
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


def do_read_csv(file_name):
    if file_name.find('.csv') != -1:
        data = pd.read_csv(file_name)
        return data
    else:
        return pd.DataFrame()


def format_error(e, msg=""):
    print('ERROR===================')
    print(e)
    print(msg)
    print('ERROR===================')

if __name__ =='__main__':
    print(get_mktime('2018-09-6'))
    print(get_mktime('2018-9-06'))