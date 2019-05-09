import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])

from flask import Flask, render_template

from src.web.controller.dataController import data
from src.web.controller.spiderController import spider

app = Flask(__name__)


@app.route('/')
def config():
    return render_template("config.html")


@app.route('/error')
def error():
    return render_template("error.html")

app.register_blueprint(spider, url_prefix='/spider')
app.register_blueprint(data, url_prefix='/data')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
