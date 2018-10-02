import redis
from QQZone.QQZoneSpider import QQZoneSpider
import re
import json
import pandas as pd
import jieba
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
from scipy.misc import imread
import matplotlib.pyplot as plt


class QQZoneAnalysis(QQZoneSpider):
    def __init__(self, use_redis=False, debug=False, file_name_head=''):
        QQZoneSpider.__init__(self, use_redis, debug, file_name_head)
        self.mood_data = []
        self.MOOD_DATA_FILE_NAME = 'data/' + file_name_head + '_mood_data.csv'

    def load_file_from_redis(self):
        self.do_recover_from_exist_data()

    def  check_data_shape(self):
        if len(self.mood_details) == len(self.like_list_names) == len(self.like_detail):
            return True
        else:
            print(len(self.mood_details), len(self.like_list_names), len(self.like_detail))
            return False

    def save_data_to_csv(self):
        self.mood_data_df = pd.DataFrame(self.mood_data)
        self.mood_data_df.to_csv(self.MOOD_DATA_FILE_NAME)

    def get_useful_info_from_json(self):
        self.load_file_from_redis()
        for i in range(len(self.mood_details)):
            total_num, uin_list = self.parse_like_names(self.like_list_names[i])
            key, like_num, prd_num = self.parse_like_and_prd(self.like_detail[i])
            if total_num != like_num:
                print('点赞数据有丢失:', total_num, like_num)
            like_num = max(total_num, like_num)
            self.parse_mood_detail(self.mood_details[i], key=key, uin_list=uin_list, like_num=like_num, prd_num=prd_num)

    def parse_mood_detail(self, mood, key, uin_list, like_num, prd_num):
        msglist = json.loads(mood)
        tid = msglist['tid']
        if key == tid:
            print('Correct')
        else:
            print('Wrong tid and key:', tid, key)
        content = msglist['content']
        time = msglist['createTime']
        time_stamp = msglist['created_time']
        secret = msglist['secret']
        if 'pictotal' in msglist:
            pic_num = msglist['pictotal']
        else:
            pic_num = 0
        cmt_num = msglist['cmtnum']
        cmt_list = []
        cmt_total_num = cmt_num
        if 'commentlist' in msglist:
            comment_list = msglist['commentlist']

            for comment in comment_list:
                comment_content = comment['content']
                comment_name = comment['name']
                comment_time = comment['createTime2']
                comment_reply_num = comment['replyNum']
                cmt_total_num += comment_reply_num
                comment_reply_list = []
                if comment_reply_num > 0:
                    for comment_reply in comment['list_3']:
                        comment_reply_content = comment_reply['content']
                        # 去掉 @{uin:117557,nick:16,who:1,auto:1} 这种文字
                        comment_reply_content = re.subn(re.compile('\@\{.*?\}'), '', comment_reply_content)[0].strip()
                        comment_reply_name = comment_reply['name']
                        comment_reply_time = comment_reply['createTime2']
                        comment_reply_list.append(dict(comment_reply_content=comment_reply_content,
                                                       comment_reply_name=comment_reply_name,
                                                       comment_reply_time=comment_reply_time))
                cmt_list.append(
                    dict(comment_content=comment_content, comment_name=comment_name, comment_time=comment_time,
                         comment_reply_num=comment_reply_num, comment_reply_list=comment_reply_list))


        self.mood_data.append(dict(tid=tid, content=content, time=time, time_stamp=time_stamp, pic_num=pic_num,
                                   cmt_num=cmt_num, like_num=like_num, prd_num=prd_num, uin_list=uin_list, cmt_total_num=cmt_total_num,
                                   cmt_list=cmt_list, secret=secret))

    def parse_like_and_prd(self, like):
        try:
            data = json.loads(like)['data'][0]
            current = data['current']
            key = current['key'].split('/')[-1]
            newdata = current['newdata']
            # 点赞数
            if 'LIKE' in newdata:
                like_num = newdata['LIKE']
                # 浏览数
                prd_num = newdata['PRD']
                return key, like_num, prd_num
            else:
                return key, 0, 0
        except BaseException as e:
            print(like)
            self.format_error(e, 'Error in like, return 0')
            return 0, 0, 0


    def parse_like_names(self, like):
        data = json.loads(like)['data']
        total_num = data['total_number']
        like_uin_info = data['like_uin_info']
        uin_list = []
        for uin in like_uin_info:
            nick = uin['nick']
            gender = uin['gender']
            uin_list.append(dict(nick=nick, gender=gender))
        return total_num, uin_list

    def drawWordCloud(self, word_text, filename):
        mask = imread('bike.jpg')
        my_wordcloud = WordCloud(
            background_color='white',  # 设置背景颜色
            mask=mask,  # 设置背景图片
            max_words=2000,  # 设置最大现实的字数
            stopwords=STOPWORDS,  # 设置停用词
            font_path='/System/Library/Fonts/Hiragino Sans GB W6.ttc',  # 设置字体格式，如不设置显示不了中文
            max_font_size=50,  # 设置字体最大值
            random_state=30,  # 设置有多少种随机生成状态，即有多少种配色方案
            scale=1.3
        ).generate(word_text)
        image_colors = ImageColorGenerator(mask)
        my_wordcloud.recolor(color_func=image_colors)
        # 以下代码显示图片
        plt.imshow(my_wordcloud)
        plt.axis("off")
        # 保存图片
        my_wordcloud.to_file(filename=filename)
        plt.show()

    def get_jieba_words(self, content):
        word_list = jieba.cut(content, cut_all=False)
        word_list2 = []
        waste_words = "现在 时候 这里 那里 今天 明天 非常 出去 各种 其实 真是 有点 只能 有些 只能 小时 baidu 还好 回到 好多 好的 继续 不会 起来 虽然 然饿 幸好一个 一些 一下 一样 一堆 所有 这样 那样 之后 只是 每次 所以 为了 还有 这么 那么 个人 因为 每次 但是 不想 出来 的话 这种 那种 开始 觉得 这个 那个 几乎 最后 自己 这些 那些 总之 " \
                      "有没有 没有 并且 然后 随便 可以 太大 应该 uin nick  真的 真好 可以 不要是不是 真的或者 可以之前 不能突然最近颇极十分就都马上立刻曾经居然重新" \
                      "不断已已经曾曾经刚刚正在将要、就、就要、马上、立刻、顿时、终于、常、常常、时常、时时、往往、渐渐、早晚、从来、终于、一向、向来、从来、总是、始终、" \
                      "水、赶紧、仍然、还是、屡次、依然、重新、还、再、再三、偶尔都、总、共、总共、统统、只、仅仅、单、净、光、一齐、一概、一律、单单、就大肆、肆意、特意、" \
                      "亲自、猛然、忽然、公然、连忙、赶紧、悄悄、暗暗、大力、稳步、阔步、单独、亲自难道、岂、究竟、偏偏、索性、简直、就、可、也许、难怪、大约、幸而、幸亏、" \
                      "反倒、反正、果然、居然、竟然、何尝、何必、明明、恰恰、未免、只好、不妨"
        for word in word_list:
            print(word)
            if len(word) >= 2 and word.find('e') == -1 and waste_words.find(word) == -1:
                word_list2.append(word)
        words_text = " ".join(word_list2)
        return words_text


if __name__ == '__main__':
    analysis = QQZoneAnalysis(use_redis=True, debug=False, file_name_head='maicius')
    print(analysis.check_data_shape())
    analysis.get_useful_info_from_json()
    analysis.save_data_to_csv()
