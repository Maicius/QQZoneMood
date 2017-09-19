#coding:utf-8

import jieba
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
import numpy as np
from PIL import  Image
from scipy.misc import imread
import codecs
import matplotlib.pyplot as plt
import json

def splitWrds(word):
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
        print word
        if len(word) >= 2 and word.find('e') == -1:
            word_list2.append(word)

    # for item in word_dict.keys():
    #     print item
    #     item = item.encode('utf-8')
    #     print item
    print word_list2
    word_text = " ".join(word_list2)
    print word_text

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
        print word
        if len(word) >= 2 and word.find('e') == -1:
            word_list2.append(word)
    words_text = " ".join(word_list2)
    return name_text, words_text

def get_agree_names(word):
    json_word = json.loads(words)
    name_list = []
    for item in json_word:
        item = json.loads(item)
        data = item['data']
        print data
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
    f = codecs.open('mood_details.txt', 'r', encoding='utf-8')
    words = f.read()
    # print words
    # word_text = splitWords(words)
    # drawWordCloud(words, 'content.png')
    f.close()

    f = codecs.open('mood_detail.json', 'r', encoding='utf-8')
    words = f.read()
    comment_text, word_text = get_comment_names(words)
    # drawWordCloud(comment_text, 'comment.png')

    drawWordCloud(word_text, 'comment_content.png')
    f.close()

    # f = codecs.open('agree.json', 'r', encoding='utf-8')
    # words = f.read()
    # comment_text = get_agree_names(words)
    # drawWordCloud(comment_text, 'agree.png')
    # f.close()