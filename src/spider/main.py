from src.spider.QQZoneSpider import QQZoneSpider


def capture_data():
    cookie_text = 'pgv_pvi=452072448; RK=+o+S14A/VT; tvfe_boss_uuid=7c5128d923ccdd6b; pac_uid=1_1272082503; ptcz=807bc32de0d90e8dbcdc3613231e3df03cb3ccfbf9013edf246be81ff3e0f51c; QZ_FE_WEBP_SUPPORT=1; pgv_pvid=4928238618; o_cookie=1272082503; __Q_w_s__QZN_TodoMsgCnt=1; _ga=amp-Iuo327Mw3_0w5xOcJY0tIA; zzpaneluin=; zzpanelkey=; pgv_si=s6639420416; ptisp=ctc; pgv_info=ssid=s5183597124; __Q_w_s_hat_seed=1; ptui_loginuin=458546290; uin=o1272082503; skey=@75zEGXDpq; p_uin=o1272082503; pt4_token=iZsuFaop-9xgKzmH*PutQD-7a53lK4QXxLtuqmo45*w_; p_skey=XfSZBQvgcy4NZ1UXwWcYX8OCkt8m8zMqUg25Y2bxdMQ_; x-stgw-ssl-info=518753a70b1a27f6bbecf101009fb3cf|0.150|1556213105.488|15|r|I|TLSv1.2|ECDHE-RSA-AES128-GCM-SHA256|43500|h2|0; qz_screen=2560x1440; cpu_performance_v8=1'
    sp = QQZoneSpider(use_redis=True, debug=True, mood_begin=0, mood_num=-1,
                      stop_time='-1',
                      download_small_image=False, download_big_image=False,
                      download_mood_detail=True, download_like_detail=True,
                      download_like_names=True, recover=False, cookie_text=None)
    sp.login()
    sp.get_main_page_info()
    sp.get_mood_list()
    sp.user_info.save_user(sp.username)

def get_user_basic_info():
    sp = QQZoneSpider(use_redis=True, debug=True, mood_begin=0, mood_num=-1,
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

if __name__ == '__main__':
    capture_data()
