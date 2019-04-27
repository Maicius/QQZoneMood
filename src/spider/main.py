from src.analysis.QQZoneAnalysis import get_mood_df
from src.spider.QQZoneSpider import QQZoneSpider
from src.util.constant import WEB_SPIDER_INFO, MOOD_NUM_PRE, CLEAN_DATA_KEY
import multiprocessing

def capture_data():
    cookie_text = 'pgv_pvi=452072448; RK=+o+S14A/VT; tvfe_boss_uuid=7c5128d923ccdd6b; pac_uid=1_1272082503; ptcz=807bc32de0d90e8dbcdc3613231e3df03cb3ccfbf9013edf246be81ff3e0f51c; QZ_FE_WEBP_SUPPORT=1; pgv_pvid=4928238618; o_cookie=1272082503; __Q_w_s__QZN_TodoMsgCnt=1; _ga=amp-Iuo327Mw3_0w5xOcJY0tIA; zzpaneluin=; zzpanelkey=; pgv_si=s6639420416; ptisp=ctc; pgv_info=ssid=s5183597124; __Q_w_s_hat_seed=1; ptui_loginuin=458546290; Loading=Yes; qz_screen=1680x1050; uin=o1272082503; skey=@Zk9eLB4j3; p_uin=o1272082503; pt4_token=eBFNsKN*j6lVpXCbI0-QrlQqZTYr6Epvj9RnyDD7zhc_; p_skey=3ZsWdJ6j-bvIBFpN31E78aKG06MVSG6WQRKQ5f7X7*U_; cpu_performance_v8=2'
    sp = QQZoneSpider(use_redis=True, debug=True, mood_begin=0, mood_num=-1,
                      stop_time='-1',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=cookie_text)
    sp.login()
    sp.get_main_page_info()
    sp.get_mood_list()
    sp.user_info.save_user(sp.username)

def web_interface(username, nick_name, stop_time, mood_num, cookie, no_delete):
    # 多线程情况下不能用recover
    recover = False
    sp = QQZoneSpider(use_redis=True, debug=False, mood_begin=0, mood_num=mood_num,
                      stop_time=stop_time,
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=recover, cookie_text=cookie,
                      from_web=True, username=username, nick_name=nick_name, no_delete=no_delete)
    try:
        sp.login()
        sp.re.rpush(WEB_SPIDER_INFO + username, "用户" + str(sp.username) + "登陆成功")
    except BaseException as e:
        sp.re.rpush(WEB_SPIDER_INFO + username, "登陆失败，请检查QQ号和cookie是否正确")
    try:
        sp.get_main_page_info()
        sp.re.rpush(WEB_SPIDER_INFO + username, "获取主页信息成功")
        sp.re.rpush(WEB_SPIDER_INFO + username, MOOD_NUM_PRE + ":" + str(sp.mood_num))
    except BaseException as e:
        sp.re.rpush(WEB_SPIDER_INFO + username,  "获取主页信息失败")
    sp.get_mood_list()
    sp.user_info.save_user(username)
    # 清洗数据
    get_mood_df(username)
    sp.re.set(CLEAN_DATA_KEY + username, 1)


def get_user_basic_info():
    sp = QQZoneSpider(use_redis=True, debug=False, mood_begin=0, mood_num=-1,
                      stop_time='2015-06-01',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)


    return sp.user_info

def array_test():
    step = 1102 // 4
    for i in range(0, 4):
        print(i * step)

def test_step():
    sp = QQZoneSpider(use_redis=True, debug=True, mood_begin=0, mood_num=1000,
                      stop_time='-1',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)
    sp.find_best_step(1100, 5)
    sp.find_best_step(1222, 5)
    sp.find_best_step(2222, 10)


if __name__ == '__main__':
    capture_data()
    # test_step()

