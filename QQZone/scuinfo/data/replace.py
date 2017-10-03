import codecs
import json

f = codecs.open('message.json', 'r', encoding='utf-8')
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
for item in jsonArr:
    for data in item['data']:
        content += data['content']
        print(data['content'])
        print(data['nickname'])
print(len(jsonArr))

