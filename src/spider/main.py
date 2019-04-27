from src.spider.QQZoneSpider import QQZoneSpider


def capture_data():
    cookie_text = 'pt4_token=Z*nb-cKKnns9yRPYW2QmxoqmyUoeyoxIBlaX3F633fk_; qz_screen=1680x1050;p_uin=o1272082503; skey=@o2SNoJaYR;ptcz=5a97b8fad1cb09b348872c553606d62b5cfc844e90821792e7d5fd6256a868d7; uin=o1272082503;pgv_info=ssid=s5126892128;p_skey=6ceHegv*zTS43EQ*ojrE8e5*DfVp4Vt2IFeXzcPnT*Y_;pgv_si=s8873467904;pgv_pvid=2724037632;QZ_FE_WEBP_SUPPORT=1;ptui_loginuin=1272082503;pgv_pvi=1374842880;zzpanelkey=;RK=wg7Q0YANVz;zzpaneluin=;'
    sp = QQZoneSpider(use_redis=True, debug=True, mood_begin=0, mood_num=-1,
                      stop_time='-1',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=cookie_text)
    sp.login()
    sp.get_main_page_info()
    sp.get_mood_list()
    sp.user_info.save_user(sp.username)

def web_interface(username, nick_name, mood_num, stop_time, cookie):
    sp = QQZoneSpider(use_redis=True, debug=False, mood_begin=0, mood_num=mood_num,
                      stop_time=stop_time,
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=cookie,
                      from_web=True, username=username, nick_name=nick_name)
    sp.login()
    sp.get_main_page_info()
    sp.get_mood_list()
    sp.user_info.save_user(sp.username)
    pass

def get_user_basic_info():
    sp = QQZoneSpider(use_redis=True, debug=False, mood_begin=0, mood_num=-1,
                      stop_time='2015-06-01',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)

    if sp.user_info.is_none:
        sp.login()
        sp.get_main_page_info()
        sp.user_info.save_user(sp.username)
        return sp.user_info
    else:
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

