FROM python:3.6

MAINTAINER maicius
WORKDIR /qqzone
COPY requirements.txt /qqzone
COPY Songti.ttc /usr/share/fonts
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
COPY . /qqzone
CMD python src/web/server.py
