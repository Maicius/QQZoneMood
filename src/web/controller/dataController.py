from flask import Flask, render_template, send_from_directory, Blueprint
import json
from src.util.constant import *
from time import sleep
import redis
import os

from src.web.entity.UserInfo import UserInfo
from src.web.web_util.web_util import get_pool, check_password
data = Blueprint('data',__name__)

@data.route('/download_file/<QQ>/<password>/<file_type>')
def download_excel(QQ, password, file_type):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)

    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish="QQ号与识别码不匹配"), ensure_ascii=False)

    else:
        if file_type == 'xlsx':
            path = RESULT_BASE_DIR
            if os.path.isfile(os.path.join(path, QQ + '_mood_data.xlsx')):
                print(os.path.join(path, QQ + '_mood_data.xlsx'))
                return send_from_directory(path, QQ + '_mood_data.xlsx', as_attachment=True)
            else:
                return json.dumps(dict(finish="文件不存在"), ensure_ascii=False)
        elif file_type == 'csv':
            path = FRIEND_BASE_DIR
            if os.path.isfile(os.path.join(path, QQ + '_friend_detail_list.xlsx')):
                return send_from_directory(path, QQ + '_friend_detail_list.xlsx', as_attachment=True)
            else:
                return json.dumps(dict(finish="文件不存在"), ensure_ascii=False)


@data.route('/clear_cache/<QQ>/<password>')
def clear_cache(QQ, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    if not check_password(conn, QQ, password):
        return json.dumps(dict(finish="QQ号与识别码不匹配"), ensure_ascii=False)
    else:
        try:
            DATA_DIR_HEAD = BASE_DIR + 'data/' + QQ
            FRIEND_DIR_HEAD = BASE_DIR + 'friend/' + QQ
            CONTENT_FILE_NAME = DATA_DIR_HEAD + '_QQ_content.json'
            LIKE_DETAIL_FILE_NAME = DATA_DIR_HEAD + '_QQ_like_detail' + '.json'
            LIKE_LIST_NAME_FILE_NAME = DATA_DIR_HEAD + '_QQ_like_list_name' + '.json'
            MOOD_DETAIL_FILE_NAME = DATA_DIR_HEAD + '_QQ_mood_detail' + '.json'
            FRIEND_DETAIL_FILE_NAME = FRIEND_DIR_HEAD + '_friend_detail.json'

            conn.delete(CONTENT_FILE_NAME)
            conn.delete(LIKE_LIST_NAME_FILE_NAME)
            conn.delete(MOOD_DETAIL_FILE_NAME)
            conn.delete(LIKE_DETAIL_FILE_NAME)
            os.remove(os.path.join(RESULT_BASE_DIR, QQ + '_mood_data.xlsx'))
            os.remove(os.path.join(RESULT_BASE_DIR, QQ + '_mood_data.csv'))
            os.remove(os.path.join(BASE_DIR + 'temp', QQ + '.json'))
            os.remove(os.path.join(BASE_DIR + 'log', QQ + '.log'))
            finish = 1
            return json.dumps(dict(finish=finish), ensure_ascii=False)
        except BaseException as e:
            finish = 0
            print(e)
            return json.dumps(dict(info="未知错误：" + str(e), finish=finish), ensure_ascii=False)

@data.route('/get_history/<QQ>/<name>/<password>')
def get_history(QQ, name, password):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    result = {}
    if not check_password(conn, QQ, password):
        result['finish'] = 0
        return json.dumps(result)

    history = conn.get(BASE_DIR + 'friend/' + QQ + '_history_like_list.json')
    if history:
        history_json = json.loads(history)
        result['finish'] = 1
        result['data'] = history_json
    else:
        result['finish'] = -1
    return json.dumps(result, ensure_ascii=False)

@data.route('/userinfo/<QQ>/<name>/<password>')
def userinfo(QQ, name, password):
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
