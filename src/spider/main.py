import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
from src.analysis.QQZoneAnalysis import QQZoneAnalysis
from src.spider.QQZoneSpider import QQZoneSpider
from src.util.constant import WEB_SPIDER_INFO, CLEAN_DATA_KEY, LOGIN_FAILED, \
    USER_MAP_KEY, GET_MOOD_FAILED, MOOD_FINISH_KEY, WAITING_USER_LIST, FINISH_USER_NUM_KEY
import threading

# 使用selenium自动登陆，获取空间全部说说内容，不下载图片
# 比较完整的一个接口，可直接调用
def capture_main_data():
    sp = QQZoneSpider(use_redis=True, debug=True, download_small_image=False, download_big_image=False)
    sp.login_with_qr_code()
    sp.get_main_page_info()
    sp.get_mood_list()
    sp.user_info.save_user(sp.username)

# 提供给web的接口
def web_interface(username, nickname, stop_time, mood_num, cookie_text, no_delete, password, pool_flag):
    sp = QQZoneAnalysis(use_redis=True, debug=False, username=username, analysis_friend=True, from_web=True,
                        nickname=nickname, stop_time=stop_time, mood_num=mood_num, no_delete=no_delete, cookie_text=cookie_text, pool_flag=pool_flag)

    # 存储用户和校验码
    sp.re.hset(USER_MAP_KEY, username, password)
    sp.logging_info(username + "init success")
    state = sp.login_with_qr_code()
    if not state:
        exit(1)
    try:
        sp.logging_info(username + "logging success")
        sp.re.rpush(WEB_SPIDER_INFO + username, "用户" + str(sp.username) + "登陆成功")
    except BaseException as e:
        sp.format_error(e, "logging failed")
        sp.re.rpush(WEB_SPIDER_INFO + username, LOGIN_FAILED)
        # 删除用户密码
        sp.re.hdel(USER_MAP_KEY, username)
    sp.get_main_page_info()
    sp.logging_info("get main page success")
    try:
        # 获取动态的数据
        t1 = threading.Thread(target=sp.get_mood_list)
        # 获取好友数据
        t2 = threading.Thread(target=sp.get_friend_detail)
        t1.setDaemon(False)
        t2.setDaemon(False)
        t1.start()
        t2.start()
        # 等待两个线程都结束
        t1.join()
        t2.join()
        # sp.user_info.save_user(username)
    except BaseException:
        sp.re.rpush(WEB_SPIDER_INFO + username, GET_MOOD_FAILED)
        exit(1)

    # 清洗好友数据
    sp.clean_friend_data()
    # 获取第一位好友数据
    sp.get_first_friend_info()
    # 清洗说说数据并计算点赞最多的人和评论最多的人
    sp.get_most_people()
    # 计算发送动态的时间
    sp.calculate_send_time()
    # 计算共同好友最多的人
    sp.get_most_common_friend()
    # 计算共同群组
    sp.get_most_group()
    sp.user_info.save_user()

    sp.draw_cmt_cloud(sp.mood_data_df)
    sp.draw_like_cloud(sp.mood_data_df)
    # 说说中的关键字，这个比较花时间
    # sp.draw_content_cloud(sp.mood_data_df)

    # 保存说说数据
    sp.export_mood_df()
    sp.re.set(MOOD_FINISH_KEY + str(username), 1)
    sp.calculate_history_like_agree()
    sp.re.set(CLEAN_DATA_KEY + username, 1)
    now_user = sp.re.get(FINISH_USER_NUM_KEY)
    if now_user is None:
        now_user = 0
    sp.re.set(FINISH_USER_NUM_KEY, now_user + 1)
    # 对排队list中删除当前用户，注意该指令的传参方式与redis-cli中不同
    sp.re.lrem(WAITING_USER_LIST, username)

def get_user_basic_info():
    sp = QQZoneSpider(use_redis=True, debug=False, mood_begin=0, mood_num=-1,
                      stop_time='2015-06-01',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)
    return sp.user_info

if __name__ == '__main__':
    capture_main_data()
