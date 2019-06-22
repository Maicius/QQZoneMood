from flask import Blueprint, session

import json
from src.util.constant import *
from flask import request
from src.spider.main import web_interface
import threading
from time import sleep

from src.web.controller.dataController import do_clear_data_by_user
from src.web.web_util.web_constant import INVALID_LOGIN, SUCCESS_STATE, FAILED_STATE, FINISH_FRIEND, WAITING_USER_STATE, \
    ALREADY_IN, CHECK_COOKIE, LOGGING_STATE, NOT_MATCH_STATE
from src.web.web_util.web_util import check_password, md5_password, init_redis_key, get_redis_conn, judge_pool

spider = Blueprint('spider', __name__)


@spider.route('/query_spider_info/<QQ>/<password>')
def query_spider_info(QQ, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    info = conn.lpop(WEB_SPIDER_INFO + QQ)
    if not check_password(conn, QQ, password):
        if info is not None and info.find("登陆失败") != -1:
            return json.dumps(dict(finish=FAILED_STATE, info=info))
        else:
            return json.dumps(dict(finish=INVALID_LOGIN, info=0))
    finish = 0
    mood_num = -1
    friend_num = 0
    if info is not None:
        if info.find(".jpg") != -1:
            finish = LOGGING_STATE
        elif info.find(LOGIN_NOT_MATCH) != -1:
            conn.lrem(WAITING_USER_LIST, QQ)
            conn.hdel(USER_MAP_KEY, QQ)
            finish = NOT_MATCH_STATE
        elif info.find(FRIEND_INFO_PRE) != -1:
            finish = FINISH_FRIEND
            friend_num = int(info.split(':')[1])
        elif info.find(MOOD_NUM_PRE) != -1:
            finish = SUCCESS_STATE
            mood_num = int(info.split(':')[1])
        elif info.find("失败") != -1:
            conn.lrem(WAITING_USER_LIST, QQ)
            conn.hdel(USER_MAP_KEY, QQ)
            finish = FAILED_STATE
            mood_num = FAILED_STATE
        result = dict(info=info, finish=finish, mood_num=mood_num, friend_num=friend_num)
        return json.dumps(result, ensure_ascii=False)
    else:
        info = ''
        result = dict(info=info, finish=finish, mood_num=mood_num, friend_num=friend_num)
        return json.dumps(result, ensure_ascii=False)

@spider.route('/query_spider_num/<QQ>/<mood_num>/<password>')
def query_spider_num(QQ, mood_num, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=INVALID_LOGIN))
    info = conn.get(MOOD_COUNT_KEY + str(QQ))
    # 强制停止，保证在由于网络等原因导致爬取的说说数量有缺失时也能正常停止程序
    finish_key = conn.get(MOOD_FINISH_KEY + str(QQ))
    finish = 0
    if mood_num == "null":
        mood_num = 0
    if finish_key == "1" or int(info) >= int(mood_num):
        finish = SUCCESS_STATE
    return json.dumps(dict(num=info, finish=finish, finish_key=finish_key))


@spider.route('/start_spider', methods=['GET', 'POST'])
def start_spider():
    if request.method == 'POST':
        nick_name = request.form['nick_name']
        qq = request.form['qq']
        stop_time = str(request.form['stop_time'])
        mood_num = int(request.form['mood_num'])
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
                result = dict(result="连接数据库失败，请稍后再尝试")
                return json.dumps(result, ensure_ascii=False)
        init_redis_key(conn, qq)
        waiting_list = check_waiting_list(conn)
        # 如果排队用户大于阈值，就返回
        waiting_num = len(waiting_list)
        login_success = conn.get(USER_LOGIN_STATE + qq)
        if qq in waiting_list and login_success == "1":
            friend_num = conn.get(FRIEND_NUM_KEY + qq)
            mood_num = conn.get(MOOD_NUM_KEY + qq)
            result = dict(result=ALREADY_IN, waiting_num=waiting_num, friend_num=friend_num, mood_num=mood_num)
            return json.dumps(result, ensure_ascii=False)
        elif qq in waiting_list and login_success == "0":
            conn.lrem(WAITING_USER_LIST, qq)

        if waiting_num >= SPIDER_USER_NUM_LIMIT:
            result = dict(result=WAITING_USER_STATE, waiting_num=waiting_num)
            return json.dumps(result, ensure_ascii=False)
        else:
            # 放进数组，开始爬虫
            conn.rpush(WAITING_USER_LIST, qq)
        try:
            t = threading.Thread(target=web_interface,
                                 args=(qq, nick_name, stop_time, mood_num, "xxx", no_delete, password, pool_flag))
            t.start()
            result = dict(result=SUCCESS_STATE)
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
        return json.dumps(dict(finish=INVALID_LOGIN))
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

# 强制停止spider
@spider.route('/stop_spider_force/<QQ>/<password>')
def stop_spider_force(QQ, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=INVALID_LOGIN))
    # 删除与该用户有关的数据
    finish = do_clear_data_by_user(QQ, conn)
    # 重新设置标记位
    conn.set(STOP_SPIDER_KEY + QQ, STOP_SPIDER_FLAG)
    conn.set(FORCE_STOP_SPIDER_FLAG + QQ, FORCE_STOP_SPIDER_FLAG)

    return json.dumps(dict(finish=finish))

@spider.route('/query_friend_info_num/<QQ>/<friend_num>/<password>')
def query_friend_info_num(QQ, friend_num, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=INVALID_LOGIN))
    info = conn.get(FRIEND_INFO_COUNT_KEY + str(QQ))
    finish = 0
    if friend_num == "null":
        friend_num = 0
    if int(info) >= int(friend_num):
        finish = 1
    return json.dumps(dict(num=info, finish=finish))


@spider.route('/query_clean_data/<QQ>/<password>')
def query_clean_data(QQ, password):
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=INVALID_LOGIN), ensure_ascii=False)
    while True:
        key = conn.get(CLEAN_DATA_KEY + QQ)
        if key == '1':
            break
        else:
            sleep(0.1)
    return json.dumps(dict(finish=key), ensure_ascii=False)


def check_waiting_list(conn):
    waiting_list = conn.lrange(WAITING_USER_LIST, 0, -1)
    return waiting_list

@spider.route('/query_finish_user_num')
def query_finish_user_num():
    pool_flag = session.get(POOL_FLAG)
    conn = get_redis_conn(pool_flag)
    if conn is None:
        host = judge_pool()
        conn = get_redis_conn(host)
    finish_user_num = conn.get(FINISH_USER_NUM_KEY)
    if finish_user_num is None:
        finish_user_num = 0
    waiting_list = check_waiting_list(conn)
    waiting_num = len(waiting_list)
    return json.dumps(dict(finish_user_num=finish_user_num, waiting_user_num=waiting_num))