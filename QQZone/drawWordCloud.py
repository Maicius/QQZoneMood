# coding:utf-8

import jieba
import time
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
from scipy.misc import imread
import codecs
import matplotlib.pyplot as plt
import json


def splitWords(word):
    print('begin')
    word_list = jieba.cut(word, cut_all=False)
    # print("/".join(word_list))
    word_dict = {}
    # for word in word_list:
    #     # print word
    #     if len(word) >= 2 and word.find('e') == -1:
    #         if word in word_dict:
    #             word_dict[word] += 1
    #         else:
    #             word_dict[word] = 1
    word_list2 = []
    for word in word_list:
        print(word)
        if len(word) >= 2 and word.find('e') == -1:
            word_list2.append(word)

    # for item in word_dict.keys():
    #     print item
    #     item = item.encode('utf-8')
    #     print item
    print(word_list2)
    word_text = " ".join(word_list2)
    print(word_text)

    # dicts = sorted(word_dict.items(), key= lambda item2: item2[1], reverse=True)
    # for item in dicts:
    #     print item[0], item[1]
    # print " ".join(word_list)
    # return " ".join(word_list)
    return word_text


def get_comment_names(word):
    json_word = json.loads(word)
    name_list = []
    word_list = ""
    for item in json_word:
        if 'commentlist' in item:
            item = json.loads(item)
            for comment in item['commentlist']:
                name_list.append(comment['name'])
                word_list += comment['content']
    name_text = " ".join(name_list)
    word_list = jieba.cut(word_list, cut_all=False)
    word_list2 = []
    for word in word_list:
        print(word)
        if len(word) >= 2 and word.find('e') == -1:
            word_list2.append(word)
    words_text = " ".join(word_list2)
    return name_text, words_text


# 获取每条说说的内容与点赞数、评论数
# 用于分析说说的内容与点赞评论的关系
def get_comment_agree_list(word):
    json_text = json.loads(word)
    like_file = codecs.open('data/like.json', 'r', encoding='utf-8')
    agree_list = like_file.read()
    json_agree = json.loads(agree_list)
    mylist = []
    for i in range(len(json_text)):

        comment_num = 0
        comment = json.loads(json_text[i])

        # if 'commentlist' in comment:
        #     # 评论数
        #     comment_num = len(comment['commentlist'])
        comment_num = comment['msgTotal']
        agree = json.loads(json_agree[i])
        agree_data = agree['data']
        agree_num = int(agree_data['total_number'])
        conlist = comment['conlist']
        content = ""

        content = comment['content']
        time_local = time.localtime(comment['created_time'])
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        #转发的说说字段略有不同，此处忽略
        # if conlist != None:
        #     for item in conlist:
        #         if 'con' in item:
        #             content += item['con']
        #         if 'ourl' in item:
        #             content += item['ourl']
        #    mylist.append([content, agree_num, comment_num])
        mylist.append([str(dt), content, agree_num, comment_num])
    print(str(mylist))
    print("按点赞的人排序：")
    print(str(sorted(mylist, key= lambda item: item[2], reverse=True)))
    print("按评论的人排序：")
    print(str(sorted(mylist, key=lambda item: item[3], reverse=True)))




def get_agree_names(agree_names):
    json_word = json.loads(agree_names)
    name_list = []
    for item in json_word:
        item = json.loads(item)
        data = item['data']
        print(data)
        if 'like_uin_info' in data:
            for info in data['like_uin_info']:
                name_list.append(info['nick'])
    return " ".join(name_list)


def drawWordCloud(word_text, filename):
    mask = imread('pic copy.png')
    my_wordcloud = WordCloud(
        background_color='white',  # 设置背景颜色
        mask=mask,  # 设置背景图片
        max_words=2000,  # 设置最大现实的字数
        stopwords=STOPWORDS,  # 设置停用词
        font_path='/System/Library/Fonts/Hiragino Sans GB W6.ttc',  # 设置字体格式，如不设置显示不了中文
        max_font_size=50,  # 设置字体最大值
        random_state=30,  # 设置有多少种随机生成状态，即有多少种配色方案
        scale=.5
    ).generate(word_text)
    image_colors = ImageColorGenerator(mask)
    my_wordcloud.recolor(color_func=image_colors)
    # 以下代码显示图片
    plt.imshow(my_wordcloud)
    plt.axis("off")
    plt.show()
    # 保存图片
    my_wordcloud.to_file(filename=filename)
    print()


if __name__ == '__main__':
    # f = codecs.open('data/mood_details.txt', 'r', encoding='utf-8')
    # words = f.read()
    # print(words)
    # word_text = splitWords(words)
    # drawWordCloud(words, 'pic\content.png')s
    # f.close()
    #
    # f = codecs.open('data/mood_detail.json', 'r', encoding='utf-8')
    # words = f.read()
    # comment_text, word_text = get_comment_names(words)
    # drawWordCloud(comment_text, 'pic/comment.png')
    #
    # drawWordCloud(word_text, 'pic/comment_content.png')
    # f.close()
    #
    # f = codecs.open('data/like.json', 'r', encoding='utf-8')
    # words = f.read()
    # comment_text = get_agree_names(words)
    # drawWordCloud(comment_text, 'pic/like.png')
    # f.close()

    f = codecs.open('data/mood_detail.json', 'r', encoding='utf-8')
    words = f.read()
    get_comment_agree_list(words)