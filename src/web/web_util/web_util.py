from src.util.check_redis import CheckUser
from src.util.constant import *
import redis
import hashlib
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
import time
# 共享redis连接池
def connect_redis():
    pool = redis.ConnectionPool(host=REDIS_HOST, port=6379, decode_responses=True)
    return pool


def connect_docker_redis():
    pool = redis.ConnectionPool(host=REDIS_HOST_DOCKER, port=6379, decode_responses=True)
    return pool

pool = connect_redis()
docker_pool = connect_docker_redis()
POOL_FLAG = -1

def get_pool():
    try:
        if pool:
            return pool
        else:
            return connect_redis()
    except BaseException as e:
        print(e)

def get_docker_pool():
    try:
        if docker_pool:
            return docker_pool
        else:
            return connect_docker_redis()
    except BaseException as e:
        print(e)

def get_redis_conn(pool_flag):
    if pool_flag == REDIS_HOST:
        pool = get_pool()
        conn = redis.Redis(connection_pool=pool)
        return conn

    else:
        docker_pool = get_docker_pool()
        conn = redis.Redis(connection_pool=docker_pool)
        return conn

# 因docker中的redis与直接访问redis的host不一致，所以在这里判断,并将结果保存在session中
def judge_pool():
    try:
        pool = get_pool()
        conn = redis.Redis(connection_pool=pool)
        conn.set('redis_success', 1)
        return REDIS_HOST
    except BaseException:
        try:
            docker_pool = get_docker_pool()
            conn = redis.Redis(connection_pool=docker_pool)
            conn.set('redis_success', 2)
            return REDIS_HOST_DOCKER
        except BaseException as e:
            print("Failed to connect redis:", e)
            raise e

def init_redis_key(conn, qq):
    if conn:
        conn.delete(WEB_SPIDER_INFO + qq)
        conn.set(MOOD_COUNT_KEY + qq, 0)
        # 设置标记位，以便停止爬虫的时候使用
        conn.set(STOP_SPIDER_KEY + qq, SPIDER_FLAG)
        conn.set(CLEAN_DATA_KEY + qq, 0)
        conn.set(FRIEND_INFO_COUNT_KEY + qq, 0)
        conn.set(MOOD_FINISH_KEY + qq, 0)
        conn.set(FORCE_STOP_SPIDER_FLAG + qq, 0)
        return 1
    else:
        return 0


def check_password(conn, QQ, password):
    if conn is not None:
        redis_pass = conn.hget(USER_MAP_KEY, QQ)
    else:
        host = judge_pool()
        conn = get_redis_conn(host)
        redis_pass = conn.hget(USER_MAP_KEY, QQ)
    password = md5_password(password)
    return redis_pass == password



def md5_password(password):
    md5 = hashlib.md5()
    md5.update(password.encode("utf8"))
    return md5.hexdigest()

def check_waiting(conn, QQ):
    user_list = conn.llen(SPIDERING_USER_LIST)
    if user_list >= 10:
        conn.rpush(WAITING_USER_LIST, QQ)
    else:
        conn.rpush(SPIDERING_USER_LIST, QQ)

def begin_check_redis():
    host = judge_pool()
    cu = CheckUser(host)
    print("begin to check:", host)
    while True:
        cu.check_exist()
        time.sleep(60)