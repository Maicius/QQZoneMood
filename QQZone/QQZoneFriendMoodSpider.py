from QQZone.QQZoneSpider import QQZoneSpider
import json
from copy import deepcopy
from urllib import parse

class QQZoneFriendMoodSpider(QQZoneSpider):
    """
    爬取指定好友的动态
    """
    def __init__(self, use_redis=False, debug=False, file_name_head='', mood_begin=0, mood_num=-1, stop_time='-1',
                 download_small_image=False, download_big_image=False,
                 download_mood_detail=True, download_like_detail=True, download_like_names=True, recover=False):
        QQZoneSpider.__init__(self, use_redis=use_redis, debug=debug, file_name_head=file_name_head,
                              mood_begin=mood_begin, mood_num=mood_num, stop_time=stop_time,
                              download_small_image=download_small_image, download_big_image=download_big_image,
                              download_mood_detail=download_mood_detail, download_like_detail=download_like_detail,
                              download_like_names=download_like_names,
                              recover=recover)
        self.friend_name_list = self.get_friend_username()


    def get_friend_username(self):
        with open('friend_info.json', 'r', encoding='utf-8') as r:
            friend_info = json.load(r)
        return friend_info

    def change_username(self, friend_name):
        self.username = friend_name
        self.mood_host = self.http_host + '/' + self.username + '/mood/'

    # 构造点赞的人的URL
    def get_aggree_url(self, unikey):
        url = 'https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app?'
        params = {
            "uin": self.raw_username,
            "unikey": self.unikey,
            "begin_uin": 0,
            "query_count": 60,
            "if_first_page": 1,
            "g_tk": self.g_tk,
        }
        url = url + parse.urlencode(params)
        return url

    def get_friend_mood(self):
        self.login()
        for name in self.friend_name_list:
            self.change_username(name['friend_name'])
            self.get_mood_list()


if __name__ == '__main__':
    qqfriend = QQZoneFriendMoodSpider(use_redis=True, debug=True, file_name_head='xxt', mood_begin=0, mood_num=-1,
                                      stop_time='-1',
                                      download_small_image=False, download_big_image=False,
                                      download_mood_detail=True, download_like_detail=True, download_like_names=True,
                                      recover=True)
    qqfriend.get_friend_mood()
