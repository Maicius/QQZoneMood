FROM python:3.6

MAINTAINER maicius
WORKDIR /qqzone
COPY requirements.txt /qqzone
RUN pip install -i https://mirrors.nju.edu.cn/pypi/web/simple/ -r requirements.txt
COPY . /qqzone
CMD python src/web/server.py
