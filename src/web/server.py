from flask import Flask, render_template
from src.util.constant import WEB_SPIDER_INFO, FINISH_ALL_INFO
import json
from src.web.entity.QQUser import QQUser
from src.web.entity.UserInfo import UserInfo
from flask import request
from src.spider.main import web_interface
import multiprocessing
import threading

import redis

pool = redis.ConnectionPool(host="127.0.0.1", port=6379, decode_responses=True)

def get_pool():
    try:
        if pool:
            return pool
        else:
            return redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True, max_connections=1000)
    except BaseException as e:
        print(e)

app = Flask(__name__)

@app.route('/data')
def data():
    user = UserInfo()
    user.load("1272082503")
    return render_template("data.html", user=user)

@app.route('/')
def config():
    return render_template("config.html")

@app.route('/start_spider', methods=['GET','POST'])
def start_spider():
    if request.method == 'POST':
        nick_name = request.form['nick_name']
        qq = request.form['qq']
        stop_time = str(request.form['stop_time'])
        mood_num = int(request.form['mood_num'])
        cookie = request.form['cookie']
        no_delete = False if request.form['no_delete'] == 'false' else True
        print("begin spider:", qq)

        try:
            t = threading.Thread(target=web_interface, args=(qq, nick_name, stop_time, mood_num, cookie, no_delete))
            t.start()
            result = dict(result=1)
            return json.dumps(result, ensure_ascii=False)
        except BaseException as e:
            result = dict(result=e)
            return json.dumps(result, ensure_ascii=False)
        # web_interface(qq, nick_name, stop_time=stop_time, mood_num=mood_num, cookie=cookie, no_delete=no_delete)
    else:
        return "test"


@app.route('/get_history/<QQ>/<name>')
def get_history(QQ, name=''):
    user = QQUser(QQ=QQ, name=name)
    mood_df = user.get_mood_df()
    history_df = mood_df.loc[:, ['cmt_total_num', 'like_num', 'content', 'time']]
    history_json = history_df.to_json(orient='records', force_ascii=False)
    return json.dumps(history_json, ensure_ascii=False)

@app.route('/get_basic_info/<QQ>/<name>')
def get_basic_info(QQ, name):
    user = UserInfo()
    user.load(QQ)
    return render_template("index.html", user=user)

@app.route('/query_spider_info/<QQ>')
def query_spider_info(QQ):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    info = conn.lpop(WEB_SPIDER_INFO + QQ)
    if FINISH_ALL_INFO in info:
        finish = 1
    else:
        finish = 0
    result = dict(info=info, finish=finish)
    return json.dumps(result, ensure_ascii=False)

if __name__ == '__main__':
    app.run(debug=True)