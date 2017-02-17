import requests
import chardet
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
def qqzone_data():
    url='http://users.qzone.qq.com/cgi-bin/likes/get_like_list_app?uin=1272082503&unikey=http%3A%2F%2Fuser.qzone.qq.com%2F1272082503%2Fmood%2F4770d24b7e0aa358cb210700.1%5E%7C%7C%5Ehttp%3A%2F%2Fuser.qzone.qq.com%2F1272082503%2Fphoto%2F91b7c939-e3c7-41d8-a450-626a11d7ce19%2FNDR0R3DSS38Ko1j2TNMRVgEAAAAAAAA!%5E%7C%7C%5E0&begin_uin=0&query_count=60&if_first_page=1&g_tk=1549424880'
    head={
        'Connection':'keep-alive',
        'Cookie':'pgv_pvid=9811567020; pgv_info=ssid=s938558904; ptisp=ctc; RK=2g+S16AeVx; ptcz=12e83fc3eb11f4f254e9862bd8449ce67e98594b8f75d6d1491515679e809aae; pt2gguin=o1272082503; uin=o1272082503; skey=@gO3UzmS5e; p_uin=o1272082503; p_skey=Q5rjqjWUMQeBYeuNwRpzF45QbywjMzwq82SIPoG1a2o_; pt4_token=SLPIzoXVuEsCGc6v-2RwnUi5cp8OfWRZnxFRauYgeCc_; Loading=Yes; qzspeedup=sdch; QZ_FE_WEBP_SUPPORT=1; cpu_performance_v8=5; __Q_w_s__QZN_TodoMsgCnt=1; __Q_w_s_hat_seed=1',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/52.0.2743.116 Safari/537.36'
    }

    resp = requests.get(url, headers=head)
    print(chardet.detect(resp.content))
    resp.encoding = 'utf-8'
    content = resp.text
    print('请求完成！')
    print(content)

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