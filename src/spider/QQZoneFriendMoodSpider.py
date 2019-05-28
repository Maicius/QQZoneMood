from src.spider.QQZoneFriendSpider import QQZoneFriendSpider
import json
from urllib import parse
from src.util.constant import BASE_DIR
from copy import deepcopy

class QQZoneFriendMoodSpider(QQZoneFriendSpider):
    """
    爬取指定好友的动态
    """
    def __init__(self, use_redis=False, debug=False, analysis=True, recover=False,
                 username='', mood_begin=0, mood_num=-1, stop_time='-1', from_web=False, nickname='', no_delete=True, cookie_text='',
                 export_excel=False, export_csv = True, pool_flag='127.0.0.1',
                 download_small_image=False, download_big_image=False,
                 download_mood_detail=True, download_like_detail=True, download_like_names=True):
        QQZoneFriendSpider.__init__(self, use_redis=use_redis, debug=debug, username=username, export_csv=export_csv,
                              mood_begin=mood_begin, mood_num=mood_num, stop_time=stop_time, from_web=from_web,
                              download_small_image=download_small_image, download_big_image=download_big_image,
                              download_mood_detail=download_mood_detail, download_like_detail=download_like_detail,
                              download_like_names=download_like_names, nickname=nickname, no_delete=no_delete, cookie_text=cookie_text,
                              recover=recover, export_excel=export_excel, pool_flag=pool_flag, analysis=analysis)
        self.friend_name_list = self.get_friend_username()
        self.base_dir = ''

    def get_friend_username(self):
        config_path = BASE_DIR + 'config/friend_info.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as r:
                friend_info = json.load(r)
            return friend_info
        except BaseException as e:
            self.format_error(e, "friend_info.json does not exist!")
            exit(1)

    def change_username(self, friend_qq, nick_name):
        self.username = friend_qq
        self.nickname = nick_name
        self.mood_host = self.http_host + '/' + self.username + '/mood/'

    # 构造点赞的人的URL，好友的点赞url与自己的url不一样
    def get_aggree_url(self, unikey):
        url = 'https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app?'
        params = {
            "uin": self.raw_username,
            "unikey": unikey,
            "begin_uin": 0,
            "query_count": 60,
            "if_first_page": 1,
            "g_tk": self.g_tk,
        }
        url = url + parse.urlencode(params)
        return url

    def get_friend_mood(self, friend_qq='', nick_name='佚名'):
        """
        获取好友动态
        :param friend_qq:
        :param nick_name:
        :return:
        """
        if self.g_tk == 0:
            self.login()
        if friend_qq != '':
            print("因传入参数不为空，所以舍弃配置文件friend_info.json的内容")
            self.friend_name_list.clear()
            self.friend_name_list.append(dict(friend_qq=friend_qq, nick_name=nick_name))
        for friend in self.friend_name_list:
            print("begin to capture:", friend['friend_qq'])
            self.change_username(friend['friend_qq'], friend['nick_name'])
            # 重新初始化参数
            self.init_parameter()

            self.init_file_name()

            self.get_mood_list()
            # 重置
            self.reset_username()

    def reset_username(self):
        self.username = deepcopy(self.raw_username)
        self.nickname = deepcopy(self.raw_nickname)
        self.mood_host = self.http_host + '/' + self.username + '/mood/'


if __name__ == '__main__':
    qqfriend = QQZoneFriendMoodSpider(use_redis=True, debug=False, mood_begin=0, mood_num=500,
                                      stop_time='2014-06-01',
                                      download_small_image=False, download_big_image=False,
                                      download_mood_detail=True, download_like_detail=True, download_like_names=True,
                                      recover=False)
    qqfriend.get_friend_mood()
