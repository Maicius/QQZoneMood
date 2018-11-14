from aip import AipNlp
import json
class SentimentClassify(object):
    def __init__(self):
        APP_ID, API_KEY, SECRET_KEY = self.get_api_keys()
        self.client = AipNlp(APP_ID, API_KEY, SECRET_KEY)
        self.sc_url = 'https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify'

    def get_api_keys(self):
        with open('api_key.json', 'r', encoding='utf-8') as r:
            keys = json.load(r)
        return keys['AppId'], keys['ApiKey'], keys['SecretKey']

    def test_sentiment(self):
        text_list = ['没错没错，迷倒万千少女就是我!男友力要爆表了', '南京的夏天只有两所大学，一所是河海大学，剩下都是河海分校', '为什么穿了棉裤，程序还是编不出来[em]e141[/em]']
        for text in text_list:
            print(self.client.sentimentClassify(text=text))

if __name__ =='__main__':
    sc = SentimentClassify()
    sc.test_sentiment()
