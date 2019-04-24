from flask import Flask, render_template
from src.analysis.QQZoneAnalysis import get_mood_df
import os
import pandas as pd
import json
from src.util.constant import BASE_DIR
app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route('/user/<username>')
def profile(username):
    return '{}\'s profile'.format(username)

@app.route('/get_history/<name>')
def get_history(name):
    RESULT_BASE_DIR = BASE_DIR + "data/result/" + name + '_mood_data.csv'
    if os.path.exists(RESULT_BASE_DIR):
        mood_df = pd.read_csv(RESULT_BASE_DIR)
    else:
        mood_df = get_mood_df(name)
    history_df = mood_df.loc[:, ['cmt_total_num', 'like_num', 'content', 'time']]
    history_json = history_df.to_json(orient='records', force_ascii=False)
    return json.dumps(history_json, ensure_ascii=False)

if __name__ == '__main__':
    app.run(debug=True)