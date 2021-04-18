import sys
import os
from datetime import timedelta
import threading

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
from src.web.web_util.web_util import judge_pool, get_redis_conn, begin_check_redis
from flask import Flask, render_template, session
from src.web.controller.dataController import data, POOL_FLAG
from src.web.controller.spiderController import spider
from src.util.constant import WAITING_USER_LIST
from flask_cors import *

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 设置跨域

app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
host = judge_pool()
conn = get_redis_conn(host)
conn.delete(WAITING_USER_LIST)


@app.route('/')
def config():
  session[POOL_FLAG] = judge_pool()
  print("pool flag:", session.get(POOL_FLAG))
  return render_template("config.html")


@app.route('/error')
def error():
  return render_template("error.html")


@app.route('/cookie')
def cookie():
  return render_template("cookie.html")


app.register_blueprint(spider, url_prefix='/spider')
app.register_blueprint(data, url_prefix='/data')

if __name__ == '__main__':
  t = threading.Thread(target=begin_check_redis)
  t.start()

  app.run(host='0.0.0.0', port=5000, debug=False)
