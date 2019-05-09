from src.util.constant import BASE_DIR
from src.util.util import check_dir_exist
import json


class UserInfo(object):
    QQ = ''
    nickname = ''
    mood_num = 0
    rz_num = 0
    photo_num = 0
    friend_num = 0
    first_time = 0
    years = 0

    first_mood_time = ''

    first_friend_time = ''
    first_friend = ''
    first_friend_header = ''

    like_friend_name = ''
    like_friend_header = ''

    cmt_friend_name_header = ''
    cmt_friend_name = ''

    is_none = True
    def __init__(self, username):
        self.temp_dir = BASE_DIR + username + '/temp/'
        check_dir_exist(self.temp_dir)

    def to_dict(self):
        return dict(QQ=self.QQ, nickname=self.nickname, mood_num=self.mood_num, rz_num=self.rz_num,
                    photo_num=self.photo_num, friend_num=self.friend_num, first_time=self.first_time,
                    first_friend=self.first_friend, first_friend_time=self.first_friend_time,
                    years=self.years, first_friend_header = self.first_friend_header,
                    like_friend_name=self.like_friend_name, like_friend_header=self.like_friend_header,
                    cmt_friend_name_header=self.cmt_friend_name_header, first_mood_time=self.first_mood_time,
                    cmt_friend_name=self.cmt_friend_name)

    def save_user(self):
        data = self.to_dict()
        with open(self.temp_dir + "user_info.json", 'w', encoding='utf-8') as w:
            json.dump(data, w, ensure_ascii=False)

    def load(self):
        try:
            with open(self.temp_dir + "user_info.json", 'r', encoding='utf-8') as r:
                user = json.load(r)
            self.change_dict_to_object(user)
            self.is_none = False
            return self
        except FileNotFoundError:
            return None
        except BaseException as e:
            print(e)
            return None


    def change_dict_to_object(self, data):
        self.QQ = data['QQ']
        self.nickname = data['nickname']
        self.mood_num = data['mood_num']
        self.rz_num = data['rz_num']
        self.photo_num = data['photo_num']
        self.friend_num = data['friend_num']
        self.first_time = data['first_time']
        self.first_friend = data['first_friend']
        self.first_friend_time = data['first_friend_time']
        self.years = data['years']
        self.first_friend_header = data['first_friend_header']
        self.like_friend_name = data['like_friend_name']
        self.like_friend_header = data['like_friend_header']
        self.cmt_friend_name_header = data['cmt_friend_name_header']
        self.cmt_friend_name = data['cmt_friend_name']
        self.first_mood_time = data['first_mood_time']
