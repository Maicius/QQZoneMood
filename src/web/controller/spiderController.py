from flask import Blueprint,session

import json
from src.util.constant import *
from flask import request
from src.spider.main import web_interface
import threading
from time import sleep

from src.web.web_util.web_util import check_password, md5_password, init_redis_key, get_redis_conn, judge_pool

spider = Blueprint('spider',__name__)

@spider.route('/query_spider_info/<QQ>/<password>')
def query_spider_info(QQ, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2))
    info = conn.lpop(WEB_SPIDER_INFO + QQ)
    finish = 0
    mood_num = -1
    friend_num = 0
    if info is not None:
        if info.find(FRIEND_INFO_PRE) != -1:
            finish = 2
            friend_num = int(info.split(':')[1])
        elif info.find(MOOD_NUM_PRE) != -1:
            finish = 1
            mood_num = int(info.split(':')[1])
        elif info.find("失败") != -1:
            finish = -1
            mood_num = -1

    result = dict(info=info, finish=finish, mood_num=mood_num, friend_num=friend_num)
    return json.dumps(result, ensure_ascii=False)


@spider.route('/query_spider_num/<QQ>/<mood_num>/<password>')
def query_spider_num(QQ, mood_num, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2))
    info = conn.get(MOOD_COUNT_KEY + str(QQ))
    # 强制停止，保证在由于网络等原因导致爬取的说说数量有缺失时也能正常停止程序
    finish_key = conn.get(MOOD_FINISH_KEY + str(QQ))
    finish = 0
    if finish_key == "1" or int(info) >= int(mood_num):
        finish = 1
    return json.dumps(dict(num=info, finish=finish, finish_key=finish_key))

@spider.route('/start_spider', methods=['GET', 'POST'])
def start_spider():
    if request.method == 'POST':
        nick_name = request.form['nick_name']
        qq = request.form['qq']
        stop_time = str(request.form['stop_time'])
        mood_num = int(request.form['mood_num'])
        cookie = request.form['cookie']
        if cookie == None or len(cookie) < 10:
            return json.dumps(dict(result=0), ensure_ascii=False)
        no_delete = False if request.form['no_delete'] == 'false' else True
        password = request.form['password']
        password = md5_password(password)
        print("begin spider:", qq)
        pool_flag = session.get(POOL_FLAG)
        conn = get_redis_conn(pool_flag)
        if conn is None:
            try:
                session[POOL_FLAG] = judge_pool()
                pool_flag = session.get(POOL_FLAG)
                conn = get_redis_conn(pool_flag)
            except BaseException:
                result = dict(result="连接数据库失败，请刷新页面再尝试")
                return json.dumps(result, ensure_ascii=False)
        init_redis_key(conn, qq)
        waiting_num = check_waiting_list(conn)
        # 如果排队用户大于阈值，就返回
        if waiting_num > SPIDER_USER_NUM_LIMIT:
            result = dict(result=2, waiting_num=waiting_num)
            return json.dumps(result, ensure_ascii=False)
        else:
            # 放进数组，开始爬虫
            conn.rpush(WAITING_USER_LIST, qq)
        try:
            t = threading.Thread(target=web_interface,
                                 args=(qq, nick_name, stop_time, mood_num, cookie, no_delete, password, pool_flag))
            t.start()
            result = dict(result=1)
            return json.dumps(result, ensure_ascii=False)
        except BaseException as e:
            result = dict(result=e)
            return json.dumps(result, ensure_ascii=False)
    else:
        return "老哥你干嘛？"


@spider.route('/stop_spider/<QQ>/<password>')
def stop_spider(QQ, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2))
    # 更新标记位，停止爬虫
    conn.set(STOP_SPIDER_KEY + QQ, STOP_SPIDER_FLAG)
    stop = 0
    # 等待数据保存
    while True:
        finish_info = conn.get(STOP_SPIDER_KEY + QQ)
        if finish_info == FINISH_ALL_INFO:
            stop = 1
            break
        else:
            sleep(0.1)

    num = conn.get(MOOD_COUNT_KEY + str(QQ))
    friend_num = conn.get(FRIEND_INFO_COUNT_KEY + str(QQ))
    return json.dumps(dict(num=num, finish=stop, friend_num=friend_num))

@spider.route('/query_friend_info_num/<QQ>/<friend_num>/<password>')
def query_friend_info_num(QQ, friend_num, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if conn is None:
        return json.dumps(dict(num="数据库未连接", finish=0))
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2))
    info = conn.get(FRIEND_INFO_COUNT_KEY + str(QQ))
    finish = 0
    if int(info) >= int(friend_num):
        finish = 1
    return json.dumps(dict(num=info, finish=finish))

@spider.route('/query_clean_data/<QQ>/<password>')
def query_clean_data(QQ, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2), ensure_ascii=False)
    while True:
        key = conn.get(CLEAN_DATA_KEY + QQ)
        if key == '1':
            break
        else:
            sleep(0.1)
    return json.dumps(dict(finish=key), ensure_ascii=False)

def check_waiting_list(conn):
    waiting_num = conn.llen(WAITING_USER_LIST)
    return waiting_num
