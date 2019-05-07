from flask import Flask, render_template, redirect, url_for, send_from_directory

from src.util.constant import *
import json
from src.web.entity.QQUser import QQUser
from src.web.entity.UserInfo import UserInfo
from flask import request
from src.spider.main import web_interface
import threading
from time import sleep
import redis
import hashlib
import os

pool = redis.ConnectionPool(host="127.0.0.1", port=6379, decode_responses=True)


# 共享redis连接池
def get_pool():
    try:
        if pool:
            return pool
        else:
            return redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, max_connections=1000)
    except BaseException as e:
        print(e)


app = Flask(__name__)


@app.route('/data/<QQ>/<name>/<password>')
def data(QQ, name, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    if check_password(conn, QQ, password):
        user = UserInfo()
        user.load(QQ)
        result = dict(finish=1, user=user.to_dict())
        return json.dumps(result, ensure_ascii=False)
    else:
        result = dict(finish=0)
        return json.dumps(result, ensure_ascii=False)


@app.route('/')
def config():
    return render_template("config.html")


@app.route('/error')
def error():
    return render_template("error.html")


@app.route('/start_spider', methods=['GET', 'POST'])
def start_spider():
    if request.method == 'POST':
        nick_name = request.form['nick_name']
        qq = request.form['qq']
        stop_time = str(request.form['stop_time'])
        mood_num = int(request.form['mood_num'])
        cookie = request.form['cookie']
        no_delete = False if request.form['no_delete'] == 'false' else True
        password = request.form['password']

        password = md5_password(password)

        print("begin spider:", qq)
        try:
            t = threading.Thread(target=web_interface,
                                 args=(qq, nick_name, stop_time, mood_num, cookie, no_delete, password))
            init_redis_key(qq)
            t.start()
            result = dict(result=1)
            return json.dumps(result, ensure_ascii=False)
        except BaseException as e:
            result = dict(result=e)
            return json.dumps(result, ensure_ascii=False)
    else:
        return "老哥你干嘛？"


def md5_password(password):
    md5 = hashlib.md5()
    md5.update(password.encode("utf8"))
    return md5.hexdigest()


@app.route('/get_history/<QQ>/<name>/<password>')
def get_history(QQ, name, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    result = {}
    if not check_password(conn, QQ, password):
        result['finish'] = 0
        return json.dumps(result)
    user = QQUser(QQ=QQ, name=name)
    mood_df = user.get_mood_df()
    history_df = mood_df.loc[:, ['cmt_total_num', 'like_num', 'content', 'time']]
    history_json = history_df.to_json(orient='records', force_ascii=False)
    result['finish'] = 1
    result['data'] = history_json
    return json.dumps(result, ensure_ascii=False)


@app.route('/get_basic_info/<QQ>/<name>')
def get_basic_info(QQ, name):
    user = UserInfo()
    user.load(QQ)
    return render_template("data.html", user=user)


@app.route('/query_spider_info/<QQ>/<password>')
def query_spider_info(QQ, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2))
    info = conn.lpop(WEB_SPIDER_INFO + QQ)
    finish = 0
    mood_num = -1
    if info is not None:
        if info.find(MOOD_NUM_PRE) != -1:
            finish = 1
            mood_num = info.split(':')[1]
        elif info.find("失败") != -1:
            finish = -1
            mood_num = -1

    result = dict(info=info, finish=finish, mood_num=mood_num)
    return json.dumps(result, ensure_ascii=False)


@app.route('/query_spider_num/<QQ>/<mood_num>/<password>')
def query_spider_num(QQ, mood_num, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2))
    info = conn.get(MOOD_COUNT_KEY + str(QQ))
    finish = 0
    if int(info) >= int(mood_num):
        finish = 1
    return json.dumps(dict(num=info, finish=finish))


@app.route('/stop_spider/<QQ>/<password>')
def stop_spider(QQ, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
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
    return json.dumps(dict(num=num, finish=stop))


@app.route('/query_clean_data/<QQ>/<password>')
def query_clean_data(QQ, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish=-2), ensure_ascii=False)
    while True:
        key = conn.get(CLEAN_DATA_KEY + QQ)
        if key == '1':
            break
        else:
            sleep(0.1)
    return json.dumps(dict(finish=key), ensure_ascii=False)


@app.route('/download_excel/<QQ>/<password>')
def download_excel(QQ, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish="QQ号与识别码不匹配"), ensure_ascii=False)

    else:
        path = RESULT_BASE_DIR
        print(os.path.join(path, QQ + '_mood_data.xlsx'))
        if os.path.isfile(os.path.join(path, QQ + '_mood_data.xlsx')):
            print(os.path.join(path, QQ + '_mood_data.xlsx'))
            return send_from_directory(path, QQ + '_mood_data.xlsx', as_attachment=True)
        else:
            return json.dumps(dict(finish="文件不存在"), ensure_ascii=False)


@app.route('/clear_cache/<QQ>/<password>')
def clear_cache(QQ, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish="QQ号与识别码不匹配"), ensure_ascii=False)

    else:
        try:
            DATA_DIR_HEAD = BASE_DIR + 'data/' + QQ
            CONTENT_FILE_NAME = DATA_DIR_HEAD + '_QQ_content.json'
            LIKE_DETAIL_FILE_NAME = DATA_DIR_HEAD + '_QQ_like_detail' + '.json'
            LIKE_LIST_NAME_FILE_NAME = DATA_DIR_HEAD + '_QQ_like_list_name' + '.json'
            MOOD_DETAIL_FILE_NAME = DATA_DIR_HEAD + '_QQ_mood_detail' + '.json'
            conn.delete(CONTENT_FILE_NAME)
            conn.delete(LIKE_LIST_NAME_FILE_NAME)
            conn.delete(MOOD_DETAIL_FILE_NAME)
            conn.delete(LIKE_DETAIL_FILE_NAME)
            os.remove(os.path.join(RESULT_BASE_DIR, QQ + '_mood_data.xlsx'))
            os.remove(os.path.join(RESULT_BASE_DIR, QQ + '_mood_data.csv'))
            finish = 1
            return json.dumps(dict(finish=finish), ensure_ascii=False)
        except BaseException as e:
            finish = 0
            print(e)
            return json.dumps(dict(info="未知错误：" + str(e), finish=finish), ensure_ascii=False)


def init_redis_key(qq):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    conn.delete(WEB_SPIDER_INFO + qq)
    conn.set(MOOD_COUNT_KEY + qq, 0)
    # 设置标记位，以便停止爬虫的时候使用
    conn.set(STOP_SPIDER_KEY + qq, SPIDER_FLAG)
    conn.set(CLEAN_DATA_KEY + qq, 0)


def check_password(conn, QQ, password):
    redis_pass = conn.hget(USER_MAP_KEY, QQ)
    password = md5_password(password)
    return redis_pass == password


def check_waiting(conn, QQ):
    user_list = conn.llen(SPIDERING_USER_LIST)
    if user_list >= 10:
        conn.rpush(WAITING_USER_LIST, QQ)
    else:
        conn.rpush(SPIDERING_USER_LIST, QQ)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
