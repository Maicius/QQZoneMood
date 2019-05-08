FROM python:3.6

MAINTAINER maicius

ADD . /qqzone
WORKDIR /qqzone
RUN pip install -r requirements.txt
CMD python src/web/server.py
