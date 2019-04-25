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
    first_friend = ''
    years = 0
    like_friend_name = ''
    cmt_friend_name = ''
    temp_dir = BASE_DIR + 'temp/'

    def __init__(self):
        check_dir_exist(self.temp_dir)

    def to_dict(self):
        return dict(QQ=self.QQ, nickname=self.nickname, mood_num=self.mood_num, rz_num = self.rz_num,
                    photo_num=self.photo_num, friend_num=self.friend_num, first_time=self.first_time,
                    first_friend=self.first_friend, years=self.years, like_friend_nam=self.like_friend_name,
                    cmt_friend_name=self.cmt_friend_name)

    def save(self):
        info = self.to_dict()
        with open(self.temp_dir + self.QQ + ".json", 'w', encoding='utf-8') as w:
            json.dump(info, w)
