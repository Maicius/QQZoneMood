import sys
import os
from datetime import timedelta

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
from src.web.web_util.web_util import judge_pool

from flask import Flask, render_template,session
from src.web.controller.dataController import data, UNDEFINE_HOST, POOL_FLAG
from src.web.controller.spiderController import spider

app = Flask(__name__)
app.config['SECRET_KEY']=os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME']=timedelta(days=7)
@app.route('/')
def config():
    session[POOL_FLAG] = judge_pool()
    return render_template("config.html")


@app.route('/error')
def error():
    return render_template("error.html")

app.register_blueprint(spider, url_prefix='/spider')
app.register_blueprint(data, url_prefix='/data')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
