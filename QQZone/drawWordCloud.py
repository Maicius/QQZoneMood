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

    name_dic = {}
    for item in name_list:
        if item in name_dic:
            name_dic[item] += 1
        else:
            name_dic[item] = 1
    print(str(sorted(name_dic.items(), key=lambda nameItem: nameItem[1], reverse=True)))
    name_text = " ".join(name_list)
    word_list = jieba.cut(word_list, cut_all=False)
    word_list2 = []
    for word in word_list:
        print(word)
        if len(word) >= 2 and word.find('e') == -1:
            word_list2.append(word)
    words_text = " ".join(word_list2)
    return name_text, words_text


# 获取每条说说的内容与点赞数、评论数、时间
# 用于分析说说的内容与点赞评论的关系
def get_comment_agree_list(word):
    json_text = json.loads(word)
    like_file = codecs.open('data/like.json', 'r', encoding='utf-8')
    agree_list = like_file.read()
    json_agree = json.loads(agree_list)
    print(len(json_agree))
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
        # 转发的说说字段略有不同，此处忽略
        # if conlist != None:
        #     for item in conlist:
        #         if 'con' in item:
        #             content += item['con']
        #         if 'ourl' in item:
        #             content += item['ourl']
        #    mylist.append([content, agree_num, comment_num])
        mylist.append([str(dt), content, agree_num, comment_num])
    with open('data/shuoshuoHistory.txt', 'w', encoding='utf-8') as mood_writer:
        mood_writer.write(str(mylist))

    moreThan200list = []
    moreThan100list = []
    moreThan50list = []
    moreThan30list = []
    lessThan30list = []
    moreThan40list = []
    moreThan20list = []
    moreThan10list = []
    moreThan5list = []
    lessThan5list = []
    count = 0
    length = 0
    for item in mylist:
        if item[2] >= 200:
            moreThan200list.append(item[1])
        elif item[2] >= 100:
            moreThan100list.append(item[1])
        elif item[2] >= 50:
            moreThan50list.append(item[1])
        elif item[2] >= 20:
            moreThan30list.append(item[1])
        else:
            lessThan30list.append(item[1])
        count += item[3]
        length += 1

        if item[3] >= 40:
            moreThan40list.append(item[1])
        elif item[3] >= 20:
            moreThan20list.append(item[1])
        elif item[3] >= 10:
            moreThan10list.append(item[1])
        elif item[3] >= 5:
            moreThan5list.append(item[1])
        else:
            lessThan5list.append(item[1])
    print("avg:" + str(count / length))
    print(len(moreThan200list))
    print(len(moreThan100list))
    print(len(moreThan50list))
    print(len(moreThan30list))
    print(len(lessThan30list))
    print("=====================")
    print(len(moreThan40list))
    print(len(moreThan20list))
    print(len(moreThan10list))
    print(len(moreThan5list))
    print(len(lessThan5list))

    hot_shuoshuo = ""
    for item in moreThan100list:
        hot_shuoshuo += item
    for item in moreThan20list:
        hot_shuoshuo += item
    low_shuoshuo = ""
    for item in lessThan5list:
        low_shuoshuo += item
    for item in lessThan30list:
        low_shuoshuo += item

    hot_content = get_jieba_words(hot_shuoshuo)
    low_content = get_jieba_words(low_shuoshuo)
    # print(str(mylist))
    # print("按点赞的人排序：")
    # print(str(sorted(mylist, key=lambda item: item[2], reverse=True)))
    # print("按评论的人排序：")
    # print(str(sorted(mylist, key=lambda item: item[3], reverse=True)))
    return hot_content, low_content

def get_jieba_words(content):
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
    words_text, low_content = get_comment_agree_list(words)
    drawWordCloud(low_content, 'pic/hot.png')
    f.close()
