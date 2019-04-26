from flask import Flask, render_template

import json
from src.web.entity.QQUser import QQUser
from src.web.entity.UserInfo import UserInfo
app = Flask(__name__)

@app.route('/data')
def data():
    user = UserInfo()
    user.load("1272082503")
    return render_template("data.html", user=user)

@app.route('/')
def config():
    return render_template("config.html")

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