from src.util.constant import *
import redis
import hashlib

# 共享redis连接池
pool = redis.ConnectionPool(host="redis", port=6379, decode_responses=True)
def get_pool():
    try:
        if pool:
            return pool
        else:
            return redis.ConnectionPool(host='redis', port=6379, decode_responses=True, max_connections=1000)
    except BaseException as e:
        print(e)

def init_redis_key(qq):
    pool = get_pool()
    conn = redis.Redis(connection_pool=pool)
    conn.delete(WEB_SPIDER_INFO + qq)
    conn.set(MOOD_COUNT_KEY + qq, 0)
    # 设置标记位，以便停止爬虫的时候使用
    conn.set(STOP_SPIDER_KEY + qq, SPIDER_FLAG)
    conn.set(CLEAN_DATA_KEY + qq, 0)
    conn.set(FRIEND_INFO_COUNT_KEY + qq, 0)


def check_password(conn, QQ, password):
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
