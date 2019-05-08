from flask import Flask, render_template, send_from_directory

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
    app.run(host='localhost', port=5000)
