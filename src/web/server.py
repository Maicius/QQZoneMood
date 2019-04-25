from flask import Flask, render_template

import os
import pandas as pd
import json
from src.util.constant import BASE_DIR
app = Flask(__name__)

@app.route('/')
def data():
    return render_template("index.html", user="maicius")

@app.route('/user/<username>')
def profile(username):
    return '{}\'s profile'.format(username)

@app.route('/get_history/<name>')
def get_history(name):

    history_df = mood_df.loc[:, ['cmt_total_num', 'like_num', 'content', 'time']]
    history_json = history_df.to_json(orient='records', force_ascii=False)
    return json.dumps(history_json, ensure_ascii=False)

if __name__ == '__main__':
    app.run(debug=True)