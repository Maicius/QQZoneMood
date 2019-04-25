from flask import Flask, render_template

import json
from src.web.entity.QQUser import QQUser
app = Flask(__name__)

@app.route('/')
def data():
    return render_template("index.html", user="maicius")

@app.route('/get_history/<QQ>/<name>')
def get_history(QQ, name=''):
    user = QQUser(QQ=QQ, name=name)
    mood_df = user.get_mood_df()
    history_df = mood_df.loc[:, ['cmt_total_num', 'like_num', 'content', 'time']]
    history_json = history_df.to_json(orient='records', force_ascii=False)
    return json.dumps(history_json, ensure_ascii=False)

if __name__ == '__main__':
    app.run(debug=True)