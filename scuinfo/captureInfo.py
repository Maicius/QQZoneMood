#encoding = utf-8
import codecs

import requests
import json
import jieba
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
import matplotlib.pyplot as plt
from scipy.misc import imread


def spider():
    headers = {
        'host': 'scuinfo.com',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.8',
        'cookie': 'connect.sid=s%3Af7PhSwFGphgew6ysF5kyt_OALuOe_CvP.o7lNHsnivwIdE%2FjTqJZsjQ6FFsBga%2Bixnk0JgpQwnVI',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'http://scuinfo.com/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'connection': 'keep-alive'
    }

    req = requests.Session()
    url = "http://scuinfo.com/api/posts?pageSize=15"
    fromId = 219980
    info = []
    count = 0
    while fromId <= 229980:
        reply = req.get(url + "&fromId=" + str(fromId), headers=headers)

        data = reply.content.decode('utf-8')
        info.append(data)
        if count % 10 == 0 or count == 229980:
            with open('data/info' + str(fromId) + '.json', 'w', encoding='utf-8') as w:
                json.dump(info, w, ensure_ascii=False)

        jsonData = json.loads(data)
        fromId += 15
        count += 1
        print(data)
        print(fromId)
        # for item in jsonData['data']:
        #
        #     print(item['nickname'])
        #     print(item['content'])


def getWordText():
    f = codecs.open('data/message.json', 'r', encoding='utf-8')
    words = f.read()

    word_list = words.split("====")

    jsonArr = []
    for item in word_list:
        try:
            jsonData = json.loads(item)
            jsonArr.append(jsonData)
            print(jsonData)
        except:
            print("null")
            pass
    content = ""
    nickname = []
    for item in jsonArr:
        for data in item['data']:
            content += data['content']
            # print(data['content'])
            if data['nickname'] != '某同学':
                nickname.append(data['nickname'])
    return content, nickname

def splitWords(word):
    print('begin')
    word_list = jieba.cut(word, cut_all=False)
    word_list2 = []
    waste_words = "有没有 没有 可以 真的 真好 可以 不要是不是 真的或者 可以之前 不能突然最近颇极十分就都马上立刻曾经居然重新不断已已经曾曾经刚刚正在将要、就、就要、马上、立刻、顿时、终于、常、常常、时常、时时、往往、渐渐、早晚、从来、终于、一向、向来、从来、总是、始终、水、赶紧、仍然、还是、屡次、依然、重新、还、再、再三、偶尔都、总、共、总共、统统、只、仅仅、单、净、光、一齐、一概、一律、单单、就大肆、肆意、特意、亲自、猛然、忽然、公然、连忙、赶紧、悄悄、暗暗、大力、稳步、阔步、单独、亲自难道、岂、究竟、偏偏、索性、简直、就、可、也许、难怪、大约、幸而、幸亏、反倒、反正、果然、居然、竟然、何尝、何必、明明、恰恰、未免、只好、不妨"
    for word in word_list:
        print(word)
        if len(word) >= 2 and word.find('e') == -1 and waste_words.find(word) == -1:
            word_list2.append(word)

    # print(word_list2)
    word_text2 = " ".join(word_list2)
    print(word_text2)
    return word_text2

def drawWordCloud(word_text, filename):
    mask = imread('hello.jpg')
    my_wordcloud = WordCloud(
        background_color='white',  # 设置背景颜色
        mask=mask,  # 设置背景图片
        max_words=2000,  # 设置最大现实的字数
        stopwords=STOPWORDS,  # 设置停用词
        font_path='/System/Library/Fonts/Hiragino Sans GB W6.ttc',  # 设置字体格式，如不设置显示不了中文
        max_font_size=50,  # 设置字体最大值
        random_state=30,  # 设置有多少种随机生成状态，即有多少种配色方案
        scale=1
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

print("finish")

if __name__ == '__main__':
    word, nickname = getWordText()
    word_text = splitWords(word)
    print(nickname)
    drawWordCloud(word_text, 'info2.jpg')

