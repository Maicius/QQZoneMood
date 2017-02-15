import requests
import chardet
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
def qqzone_data():
    url='http://user.qzone.qq.com/1272082503'
    head={
        'Connection':'keep-alive',
        'Cookie':'zzpaneluin=; zzpanelkey=; pgv_pvi=5924405248; pgv_si=s3300252672; ptisp=ctc; RK=ao+Sw6AvWR; ptcz=25c2af45a157324d5939ce4510b05d828086df27eb5890a8bb7edc39f9df9926; __Q_w_s__appDataSeed=1; __Q_w_s_hat_seed=1; pgv_pvid=242646819; pgv_info=ssid=s2763182108; pt2gguin=o1272082503; uin=o1272082503; skey=@NXeYUVn4m; p_uin=o1272082503; p_skey=Nyse35Y7R7ysx-wlwOfbIu6Qqw2R6auzHxP8VejRczY_; pt4_token=GaSxir0-TAUYcLTXrtR0GFtBqbU*trr0mRs0aKkQbrc_; __Q_w_s__QZN_TodoMsgCnt=1; Loading=Yes; qzspeedup=sdch; qz_screen=1920x1080; QZ_FE_WEBP_SUPPORT=1; cpu_performance_v8=12',
        'If-Modified-Since':'Wed, 15 Feb 2017 05:06:19 GMT',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/52.0.2743.116 Safari/537.36'
    }

    resp = requests.get(url, headers=head)
    print(chardet.detect(resp.content))
    resp.encoding = 'utf-8'
    content = resp.text
    print('请求完成！')
    #print(content)

    soup = BeautifulSoup(content, 'html.parser')
    names = soup.select('.f-nick')
    times = soup.select('.info-detail')#class = info -detail
    info = soup.select('.f-info') #class=f-info
    print("Finished")
    #with open('I:\\ReadQQFrinedsInfo\\QQDATA.txt','a') as fp:
    x = 0
    while x < 6:
        print('昵称:'+names[x].text +'时间:'+ times[x].text + '发表了:' + info[x].text+'\t'+'\n')
        x += 1


if __name__ == '__main__':
    qqzone_data()