from src.util.constant import BASE_DIR
from src.util.util import check_dir_exist
import json

from src.web.web_util.web_constant import USER_INFO_KEY
from src.web.web_util.web_util import judge_pool, get_redis_conn


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

    single_friend = 0

    most_date = ''
    most_date_like = 0
    most_date_cmt = 0
    most_time_state = ''
    most_date_prd = 0
    most_date_content = ''

    early_mood_date = ''
    early_mood_time = 0
    early_mood_content = ''
    early_mood_cmt = ''
    early_mood_friend = ''

    is_night = ''

    most_friend = ''
    most_common_friend_num = 0

    most_group = ''
    most_group_member = 0


    total_like_num = 0
    total_cmt_num = 0
    avg_like_num = 0

    cmt_friend_num = 0
    cmt_msg_num = 0
    like_friend_num = 0
    non_activate_friend_num = 0

    non_activate_time = 0

    total_like_list = []
    my_top_words = []
    friend_top_words = []

    total_word_num = 0

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
                    cmt_friend_name=self.cmt_friend_name, single_friend=self.single_friend, most_date = self.most_date,
                    most_time_state=self.most_time_state, is_night = self.is_night, most_friend=self.most_friend,
                    most_common_friend_num=self.most_common_friend_num, most_group=self.most_group,
                    most_group_member=self.most_group_member, total_like_num=self.total_like_num, total_cmt_num=self.total_cmt_num,
                    avg_like_num = self.avg_like_num, cmt_friend_num = self.cmt_friend_num, cmt_msg_num = self.cmt_msg_num,
                    like_friend_num = self.like_friend_num, non_activate_friend_num = self.non_activate_friend_num,
                    total_like_list = json.dumps(self.total_like_list, ensure_ascii=False), my_top_words = json.dumps(self.my_top_words, ensure_ascii=False),
                    friend_top_words = json.dumps(self.friend_top_words, ensure_ascii=False), non_activate_time=self.non_activate_time,
                    most_date_cmt = self.most_date_cmt, most_date_like = self.most_date_like, most_date_prd = self.most_date_prd,
                    total_word_num = self.total_word_num, most_date_content = self.most_date_content,
                    early_mood_time = self.early_mood_time, early_mood_cmt = self.early_mood_cmt, early_mood_content = self.early_mood_content,
                    early_mood_friend = self.early_mood_friend, early_mood_date = self.early_mood_date
        )

    def save_user(self):
        data = self.to_dict()
        with open(self.temp_dir + "user_info.json", 'w', encoding='utf-8') as w:
            json.dump(data, w, ensure_ascii=False)
        serial_data = json.dumps(data, ensure_ascii=False)
        conn = self.get_redis_conn()
        conn.set(USER_INFO_KEY + self.QQ, serial_data)
        print("user info result file was saved to:", self.temp_dir + "user_info.json")

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

    def load_from_redis(self, qq):
        try:
            conn = self.get_redis_conn()
            data = json.loads(conn.get(USER_INFO_KEY + qq))

            self.change_dict_to_object(data)
            self.is_none = False
        except:
            print("从redis中加载数据失败...")
            return None

    def get_redis_conn(self):
        host = judge_pool()
        conn = get_redis_conn(host)
        return conn

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
        self.single_friend = data['single_friend']
        self.most_date = data['most_date']
        self.most_time_state = data['most_time_state']
        self.is_night = data['is_night']
        self.most_friend = data['most_friend']
        self.most_common_friend_num = data['most_common_friend_num']
        self.most_group = data['most_group']
        self.most_group_member = data['most_group_member']
        self.total_like_num = data['total_like_num']
        self.total_cmt_num = data['total_cmt_num']
        self.avg_like_num = data['avg_like_num']
        self.cmt_friend_num = data['cmt_friend_num']
        self.cmt_msg_num = data['cmt_msg_num']
        self.like_friend_num = data['like_friend_num']
        self.non_activate_friend_num = data['non_activate_friend_num']

        data['total_like_list'] = json.loads(data['total_like_list'])
        data['my_top_words'] = json.loads(data['my_top_words'])
        data['friend_top_words'] = json.loads(data['friend_top_words'])

        self.total_like_list = data['total_like_list']
        self.my_top_words = data['my_top_words']
        self.friend_top_words = data['friend_top_words']
        self.non_activate_time = data['non_activate_time']
        self.most_date_like = data['most_date_like']
        self.most_date_cmt = data['most_date_cmt']
        self.most_date_prd = data['most_date_prd']
        self.total_word_num = data['total_word_num']
        self.most_date_content = data['most_date_content']

        self.early_mood_time = data['early_mood_time']
        self.early_mood_content = data['early_mood_content']
        self.early_mood_cmt = data['early_mood_cmt']
        self.early_mood_friend = data['early_mood_friend']
        self.early_mood_date = data['early_mood_date']