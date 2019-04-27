from flask import Flask, render_template

import json
from src.web.entity.QQUser import QQUser
from src.web.entity.UserInfo import UserInfo
from flask import request
from src.spider.main import web_interface
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
        stop_time = request.form['stop_time']
        mood_num = int(request.form['mood_num'])
        cookie = request.form['cookie']
        print("begin spider:", qq)
        web_interface(qq, nick_name, stop_time=stop_time, mood_num=mood_num, cookie=cookie)
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

if __name__ == '__main__':
    app.run(debug=True)