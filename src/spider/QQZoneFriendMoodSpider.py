from src.spider.QQZoneSpider import QQZoneSpider
import json
from urllib import parse
from src.util.constant import BASE_DIR

class QQZoneFriendMoodSpider(QQZoneSpider):
    """
    爬取指定好友的动态
    """
    def __init__(self, use_redis=False, debug=False, mood_begin=0, mood_num=-1, stop_time='-1',
                 download_small_image=False, download_big_image=False,
                 download_mood_detail=True, download_like_detail=True, download_like_names=True, recover=False):
        QQZoneSpider.__init__(self, use_redis=use_redis, debug=debug,
                              mood_begin=mood_begin, mood_num=mood_num, stop_time=stop_time,
                              download_small_image=download_small_image, download_big_image=download_big_image,
                              download_mood_detail=download_mood_detail, download_like_detail=download_like_detail,
                              download_like_names=download_like_names,
                              recover=recover)
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

    def change_username(self, friend_qq):
        self.username = friend_qq
        self.mood_host = self.http_host + '/' + self.username + '/mood/'


    # 构造点赞的人的URL
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

    def get_friend_mood(self):
        self.login()
        for friend in self.friend_name_list:
            print("begin to capture:", friend['friend_qq'])
            self.change_username(friend['friend_qq'])
            # 重新初始化参数
            self.init_parameter()

            self.init_file_name()

            self.get_mood_list()


if __name__ == '__main__':
    qqfriend = QQZoneFriendMoodSpider(use_redis=True, debug=False, mood_begin=0, mood_num=500,
                                      stop_time='2014-06-01',
                                      download_small_image=False, download_big_image=False,
                                      download_mood_detail=True, download_like_detail=True, download_like_names=True,
                                      recover=False)
    qqfriend.get_friend_mood()
