from QQZone.QQZoneSpider import QQZoneSpider
from urllib import parse
import requests
import json

class QQZoneFriendSpider(QQZoneSpider):
    def __init__(self, use_redis=False, debug=False, file_name_head=""):
        QQZoneSpider.__init__(self, use_redis=use_redis, debug=debug, file_name_head=file_name_head)
        if self.g_tk == 0:
            self.login()
        self.FRIEND_LIST_FILE_NAME = 'friend/' + file_name_head + '_friend_list.json'
        self.FRIEND_DETAIL_FILE_NAME = 'friend/' + file_name_head + '_friend_detail.json'
        self.friend_detail = []


    def get_friend_list(self):
        friend_list_url = self.get_friend_list_url()
        friend_content = self.get_json(self.req.get(url=friend_list_url, headers=self.headers).content.decode('utf-8'))
        self.friend_list = json.loads(friend_content)['data']['items']
        if self.use_redis:
            self.re.set('friend_list', self.friend_list)
        self.save_data_to_json(self.friend_list, self.FRIEND_LIST_FILE_NAME)
        print('获取好友列表信息完成')


    def get_friend_detail(self):
        self.get_friend_list()
        i= 0
        for friend in self.friend_list:
            uin = friend['uin']
            i = i + 1
            print(i)
            print('正在爬取:',uin,'...')
            url = self.get_friend_detail_url(uin)
            content = self.get_json(self.req.get(url, headers=self.headers).content.decode('utf-8'))

            data = json.loads(content)
            try:
                data = data['data']
            except BaseException as e:
                self.format_error(e, '失败')
                print(data)
                continue
            self.friend_detail.append(data)

        if self.use_redis:
            self.re.set(self.FRIEND_DETAIL_FILE_NAME, self.friend_detail)
        self.save_data_to_json(self.friend_detail, self.FRIEND_DETAIL_FILE_NAME)


    def get_friend_list_url(self):
        friend_url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/friend_show_qqfriends.cgi?'
        params = {
            'uin': self.username,
            'follow_flag': 0,
            'groupface_flag': 0,
            'fupdate': 1,
            'g_tk': self.g_tk,
            'qzonetoken': ''
        }
        friend_url = friend_url + parse.urlencode(params)
        return friend_url

    def get_friend_detail_url(self, uin):
        detail_url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/friendship/cgi_friendship?'
        params = {
            'activeuin': self.username,
            'passiveuin': uin,
            'situation': 1,
            'isCalendar': 1,
            'g_tk': self.g_tk
        }
        return detail_url + parse.urlencode(params)

if __name__ == '__main__':
    friend_spider = QQZoneFriendSpider(use_redis=True, debug=True, file_name_head="maicius")
    friend_spider.get_friend_detail()

