# coding:utf-8
# QQ空间动态爬虫
# 包括动态内容、点赞的人、评论的人、评论的话
# 登陆使用的是Selenium， 无法识别验证码
# 若出现验证码，则先尝试手动从浏览器登陆并退出再运行程序
from requests.adapters import HTTPAdapter
from selenium import webdriver
import requests
import time
from urllib import parse
import re
import json
import copy
import datetime
import random
from src.spider.BaseSpider import BaseSpider
from src.util import util
from src.util.constant import qzone_jother2, SPIDER_USER_NUM_LIMIT, EXPIRE_TIME_IN_SECONDS, MOOD_NUM_KEY, \
    WEB_SPIDER_INFO, GET_MAIN_PAGE_FAILED, MOOD_NUM_PRE, GET_FIRST_LOGIN_TIME, LOGIN_SUCCESS, LOGIN_FAILED, \
    LOGIN_NOT_MATCH, FORCE_STOP_SPIDER_FLAG
import math
import execjs
import threading
from src.util.constant import FINISH_ALL_INFO, MOOD_COUNT_KEY, STOP_SPIDER_KEY, STOP_SPIDER_FLAG
import os
from http import cookiejar
import subprocess
import sys
import pandas as pd

from src.util.util import remove_special_tag


class QQZoneSpider(BaseSpider):
    def __init__(self, use_redis=False, debug=False, mood_begin=0, mood_num=-1, stop_time='-1',
                 download_small_image=False, download_big_image=False,
                 download_mood_detail=True, download_like_detail=True, download_like_names=True, recover=False,
                 cookie_text=None, from_web=False, username='', nickname='', no_delete=True, pool_flag='127.0.0.1',
                 from_client=False, get_visit=False):
        """
        init method
        :param use_redis: If true, use redis and json file to save data, if false, use json file only.
        :param debug: If true, print info in console
        :param mood_begin: 开始下载的动态序号，0表示从第0条动态开始下载
        :param mood_num: 下载的动态数量，最好设置为20的倍数
        :param stop_time: 停止下载的时间，-1表示全部数据；注意，这里是倒序，比如，stop_time="2016-01-01",表示爬取当前时间到2016年1月1日前的数据
        :param recover: 是否从redis或文件中恢复数据（主要用于爬虫意外中断之后的数据恢复），注意，此功能在多线程中不可用
        :param download_small_image: 是否下载缩略图，仅供预览用的小图，该步骤比较耗时，QQ空间提供了3中不同尺寸的图片，这里下载的是最小尺寸的图片
        :param download_big_image: 是否下载大图，QQ空间中保存的最大的图片，该步骤比较耗时
        :param download_mood_detail:是否下载动态详情
        :param download_like_detail:是否下载点赞的详情，包括点赞数量、评论数量、浏览量，该数据未被清除
        :param download_like_names:是否下载点赞的详情，主要包含点赞的人员列表，该数据有很多都被清空了
        :param from_web: 表示是否来自web接口，如果为True，将该请求来自web接口，则不会读取配置文件
        :param username: 在web模式中，传递过来的用户QQ号
        :param nickname: 在web模式中，传递过来的用户昵称
        :param no_delete: 是否在redis中缓存数据，如果为True,则不会删除，如果为False，则设置24小时的缓存时间
        :param pool_flag: redis的连接池host，因为docker中host与外部不同，所以在启动程序时会自动判断是不是处于docker中
        """
        BaseSpider.__init__(self, use_redis=use_redis, debug=debug, mood_begin=mood_begin, mood_num=mood_num,
                            stop_time=stop_time,
                            download_small_image=download_small_image, download_big_image=download_big_image,
                            download_mood_detail=download_mood_detail, download_like_detail=download_like_detail,
                            download_like_names=download_like_names, recover=recover, cookie_text=cookie_text,
                            from_web=from_web, username=username, nickname=nickname, no_delete=no_delete,
                            pool_flag=pool_flag, from_client=from_client, get_visit=get_visit)

        self.cookies = cookiejar.CookieJar()
        self.req.cookies = self.cookies
        connection_num = 20 * SPIDER_USER_NUM_LIMIT
        # 设置连接池大小
        self.req.mount('https://', HTTPAdapter(pool_connections=5, pool_maxsize=connection_num))
        self.req.mount('http://', HTTPAdapter(pool_connections=5, pool_maxsize=connection_num))
        self.qzonetoken = ""
        self.g_tk = 0
        self.init_parameter()
        self.qzone_login_url = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?proxy_url=https%3A//qzs.qq.com/qzone/v6/portal/proxy.html&daid=5&&hide_title_bar=1&low_login=0&qlogin_auto_login=1&no_verifyimg=1&link_target=blank&appid=549000912&style=22&target=self&s_url=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&pt_qr_app=%E6%89%8B%E6%9C%BAQQ%E7%A9%BA%E9%97%B4&pt_qr_link=https%3A//z.qzone.com/download.html&self_regurl=https%3A//qzs.qq.com/qzone/v6/reg/index.html&pt_qr_help_link=https%3A//z.qzone.com/download.html&pt_no_auth=0'

    def login(self):
        """
        提供两种登陆的方法，一是使用selenium自动模拟点击登陆，二是手动登陆后添加cookie文件
        :return:
        """
        if self.cookie_text:
            self.manu_get_cookie(self.cookie_text)
            self.get_qzone_token()
        else:
            self.auto_get_cookie()
        # 根据cookie计算g_tk值
        self.get_g_tk()
        if self.debug:
            print("finish to calculate g_tk")
        self.headers['cookie'] = self.cookies
        self.h5_headers['cookie'] = self.cookies

    def login_with_qr_code(self):
        """
        扫描二维码登陆
        :return:
        """
        cookies = cookiejar.Cookie(version=0, name='_qz_referrer', value='qzone.qq.com', port=None,
                                   port_specified=False,
                                   domain='qq.com',
                                   domain_specified=False, domain_initial_dot=False, path='/', path_specified=True,
                                   secure=False, expires=None, discard=True, comment=None, comment_url=None,
                                   rest={'HttpOnly': None}, rfc2109=False)
        self.cookies.set_cookie(cookies)
        self.headers['host'] = 'ssl.ptlogin2.qq.com'
        self.headers['referer'] = 'https://qzone.qq.com/'
        start_time = util.date_to_millis(datetime.datetime.utcnow())
        wait_time = 0
        login_url = 'https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.{0}6252926{1}2285{2}86&daid=5'.format(
            random.randint(0, 9), random.randint(0, 9), random.randint(0, 9))
        qr_res = self.req.get(url=login_url, headers=self.headers, timeout=20)
        self.save_image_single(qr_res.content, self.QR_CODE_PATH)

        if not self.from_web:
            # for mac os
            if sys.platform.find('darwin') >= 0:
                # Fix issue 50: https://github.com/Maicius/QQZoneMood/issues/50
                # subprocess.call(['open', self.QR_CODE_PATH + '.jpg'])
                try:
                    os.system("open " + self.QR_CODE_PATH + '.jpg')
                    self.logging_info("打开二维码图片成功")
                except:
                    self.logging_info("打开二维码图片失败")

            # for linux
            elif sys.platform.find('linux') >= 0:
                subprocess.call(['xdg-open', self.QR_CODE_PATH + '.jpg'])
            # for windows
            elif sys.platform.find('win32') >= 0:
                # subprocess.call(['open', QRImagePath])
                os.startfile(self.QR_CODE_PATH + '.jpg')
            else:
                subprocess.call(['xdg-open', self.QR_CODE_PATH + '.jpg'])
        print('请使用微信扫描二维码登陆')
        print("若二维码未自动弹出，请手动到以下路径寻找二维码图片:")
        print(self.QR_CODE_PATH + '.jpg')
        print('-------------------------')
        while wait_time < 60:
            wait_time += 1

            login_sig = self.get_cookie('pt_login_sig')
            qr_sig = self.get_cookie('qrsig')

            if self.debug:
                print("success to download qr code")
            self.logging_info("success to download qr code")
            # 如果不是从网页发来的请求，就本地展示二维码
            if not self.from_web and wait_time <= 1:
                self.show_image(self.QR_CODE_PATH + '.jpg')
            elif self.from_web and wait_time <= 1 and self.use_redis:
                self.re.lpush(WEB_SPIDER_INFO + self.username, self.random_qr_name + ".jpg")
            while True:
                self.headers['referer'] = self.qzone_login_url
                res = self.req.get(
                    'https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptqrtoken={0}&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-{1}&js_ver=10220&js_type=1&login_sig={2}&pt_uistyle=40&aid=549000912&daid=5&'.format(
                        self.get_qr_token(qr_sig), util.date_to_millis(datetime.datetime.utcnow()) - start_time,
                        login_sig), headers=self.headers)
                content = res.content.decode("utf-8")

                ret = content.split("'")
                if ret[1] == '65':  # 65: QRCode 失效, 0: 验证成功, 66: 未失效, 67: 验证中
                    if self.use_redis:
                        self.re.lpush(WEB_SPIDER_INFO + self.username, LOGIN_FAILED)
                    break
                elif ret[1] == '0':
                    break
                time.sleep(2)
            if ret[1] == '0':
                break

        # 删除QRCode文件
        self.remove_qr_code()

        # 登陆失败
        if ret[1] != '0':
            self.re.lpush(WEB_SPIDER_INFO + self.username, LOGIN_FAILED)
            self.logging_info("Failed to login with qr code")
            return False
        self.logging_info("scan qr code success")

        self.nickname = ret[11]
        self.req.get(url=ret[5])
        username = re.findall(r'uin=([0-9]+?)&', ret[5])[0]

        # 避免获取别人信息
        if username != self.username and not self.from_client:
            if self.use_redis:
                self.re.lpush(WEB_SPIDER_INFO + self.username, LOGIN_NOT_MATCH)
            return False
        self.username = username
        self.init_user_info()
        self.headers['host'] = 'user.qzone.qq.com'
        skey = self.get_cookie('p_skey')
        self.g_tk = self.get_GTK(skey)
        self.headers['host'] = 'user.qzone.qq.com'
        self.headers.pop('referer')
        # self.init_user_info()
        self.get_qzone_token()
        if self.use_redis:
            self.re.lpush(WEB_SPIDER_INFO + self.username, LOGIN_SUCCESS)
        if not self.from_client:
            print("用户" + self.username + "登陆成功！")
        return True

    def remove_qr_code(self):
        if os.path.exists(self.QR_CODE_PATH + '.jpg'):
            os.remove(self.QR_CODE_PATH + '.jpg')
            if self.debug:
                print("success to delete qr code")

    def get_cookie(self, key):
        for c in self.cookies:
            if c.name == key:
                return c.value
        return ''

    def get_GTK(self, skey):
        hash = 5381
        for i in range(0, len(skey)):
            hash += (hash << 5) + self.utf8_unicode(skey[i])
        return hash & 0x7fffffff

    def utf8_unicode(self, c):
        if len(c) == 1:
            return ord(c)
        elif len(c) == 2:
            n = (ord(c[0]) & 0x3f) << 6
            n += ord(c[1]) & 0x3f
            return n
        elif len(c) == 3:
            n = (ord(c[0]) & 0x1f) << 12
            n += (ord(c[1]) & 0x3f) << 6
            n += ord(c[2]) & 0x3f
            return n
        else:
            n = (ord(c[0]) & 0x0f) << 18
            n += (ord(c[1]) & 0x3f) << 12
            n += (ord(c[2]) & 0x3f) << 6
            n += ord(c[3]) & 0x3f
            return n

    def change_dict_to_cookie(self, cookie):
        cookies = ''
        for key, val in cookie.items():
            cookies += key + '=' + str(val) + '; '
        return cookies

    def get_qr_token(self, qrsig):
        e = 0
        for i in qrsig:
            e += (e << 5) + ord(i)
        return 2147483647 & e

    # 核心加密字段
    def get_g_tk(self):
        p_skey = self.cookies[self.cookies.find('p_skey=') + 7: self.cookies.find(';', self.cookies.find('p_skey='))]
        h = 5381
        for i in p_skey:
            h += (h << 5) + ord(i)
        print('g_tk', h & 2147483647)
        self.g_tk = h & 2147483647

    # 使用selenium自动登陆并获取cookie
    def auto_get_cookie(self):
        self.web = webdriver.Chrome()
        self.web.get(self.host)
        self.web.switch_to.frame('login_frame')
        log = self.web.find_element_by_id("switcher_plogin")
        log.click()
        time.sleep(1)
        username = self.web.find_element_by_id('u')
        username.send_keys(self.username)
        ps = self.web.find_element_by_id('p')
        ps.send_keys(self.password)
        btn = self.web.find_element_by_id('login_button')
        time.sleep(1)
        btn.click()
        time.sleep(10)
        print("begin...")
        self.web.get('https://user.qzone.qq.com/{}/main'.format(self.username))
        time.sleep(3)
        content = self.web.page_source
        self.logging_info(content)
        qzonetoken = re.findall(re.compile("g_qzonetoken = \(function\(\)\{ try\{return \"(.*)?\""), content)[0]
        self.qzonetoken = qzonetoken
        cookie = ''
        # 获取cookie
        for elem in self.web.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + ";"
        self.cookies = cookie
        print(cookie)
        print("Login success")
        self.logging.info("login_success")
        self.web.quit()

    # 手动添加cookie完成登陆
    def manu_get_cookie(self, cookie_text):
        self.cookies = cookie_text
        self.headers['cookie'] = self.cookies
        self.headers['cookie'] = self.cookies

    # 构造获取动态的URL
    def get_mood_url(self):
        url = 'https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6?'
        params = {
            "sort": 0,
            "start": 0,
            "num": 20,
            "cgi_host": "http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6",
            "replynum": 100,
            "callback": "_preloadCallback",
            "code_version": 1,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "notice": 0,
            "format": "jsonp",
            "need_private_comment": 1,
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken
        }
        url = url + parse.urlencode(params)
        return url

    # 获取动态详情列表
    def get_mood_list(self):
        """
         # 获取动态详情列表（一页20个）并存储到本地
        :return:
        """
        url_mood = self.get_mood_url() + '&uin=' + str(self.username)
        pos = self.mood_begin
        recover_index_split = 0
        if self.recover:
            recover_index = self.do_recover_from_exist_data()
            if recover_index is not None:
                pos = recover_index // 20 * 20
                recover_index_split = recover_index % 20
        url = url_mood + '&pos=' + str(pos)
        print("url", url)
        try:
            mood_num = self.get_mood_num()
        except:
            # 这个数据很重要，所以重复一次
            time.sleep(1)
            try:
                mood_num = self.get_mood_num()
            except:
                print("Failed to get mood num")
                mood_num = 0

        if not self.from_client and mood_num > 0:
            self.get_first_mood(mood_num)

        # 如果mood_num为-1或指定的mood_num大于实际的动态数量，则下载全部的动态
        if self.mood_num == -1 or self.mood_num > mood_num:
            self.mood_num = mood_num
        # 根据mood_num分配线程个数
        if self.mood_num < 20 * self.thread_num:
            self.thread_num = round(self.mood_num / 20)
        if self.thread_num < 1:
            self.thread_num = 1
        if not self.from_client:
            print("获取QQ动态的线程数量:", self.thread_num)
        step = self.find_best_step(self.mood_num, self.thread_num)

        for i in range(0, self.thread_num):
            # pos必须为20的倍数
            start_pos = i * step
            stop_pos = (i + 1) * step if i + 1 < self.thread_num else self.mood_num
            t = threading.Thread(target=self.get_mood_in_range,
                                 args=(start_pos, stop_pos, recover_index_split, url_mood, True))
            self.thread_list.append(t)

        for t in self.thread_list:
            t.setDaemon(False)
            t.start()
            if not self.from_client:
                print("开始线程:", t.getName())

        # 等待全部子线程结束
        for t in self.thread_list:
            t.join()

        # 如果不是强制停止的，就保存数据
        if self.use_redis:
            force_key = self.re.get(FORCE_STOP_SPIDER_FLAG + self.username)
            if not force_key or (force_key != FORCE_STOP_SPIDER_FLAG and not self.from_client):
                # 保存所有数据到指定文件

                print('保存最终数据中...')
                if self.use_redis:
                    self.re.set(STOP_SPIDER_KEY + self.username, FINISH_ALL_INFO)
                if (self.debug):
                    print('Error Unikeys Num:', len(self.error_like_detail_unikeys))
                    print('Retry to get them...')
                self.retry_error_unikey()
                self.save_data_to_redis(final_result=True)
                print("finish===================")
            else:
                self.re.delete(FORCE_STOP_SPIDER_FLAG + self.username)
        self.save_all_data_to_json()
        self.result_report()


    def find_best_step(self, mood_num, thread_num):
        step = int(mood_num / thread_num // 20 * 20)
        if self.debug:
            print("Best Step:", step)
        return step

    def get_mood_num(self):
        url_mood = self.get_mood_url() + '&uin=' + str(self.username)
        url = url_mood + '&pos=0'
        res = self.req.get(url=url, headers=self.h5_headers, timeout=20)
        try:
            mood = res.content.decode('utf-8')
        except BaseException as e:
            if self.debug:
                print("该用户信息存在乱码")
                self.format_error(e, "Bad decode exists in user info")
            mood = remove_special_tag(res.text)
        if self.debug:
            print("获取主页动态数量的状态码:", res.status_code)
        mood_json = json.loads(self.get_json(mood))
        mood_num = mood_json['usrinfo']['msgnum']
        return mood_num

    def get_json_content(self, url):
        mood_list = self.req.get(url=url, headers=self.h5_headers, timeout=20)
        # print(mood_list.content)
        try:
            json_content = self.get_json(str(mood_list.content.decode('utf-8')))
        except BaseException as e:
            json_content = self.get_json(remove_special_tag(mood_list.text))
        return json_content

    def get_mood_in_range(self, pos, mood_num, recover_index_split, url_mood, until_stop_time):
        if not self.from_client:
            print("进入线程:", mood_num, until_stop_time)
        while pos < mood_num and until_stop_time:
            if not self.from_client:
                print('正在爬取', pos, '...')
            # self.re.lpush(WEB_SPIDER_INFO + self.username, "正在爬取" + str(pos) + "...")
            try:
                try:
                    url = url_mood + '&pos=' + str(pos)
                    json_content = self.get_json_content(url)
                    repeat_time = 1
                    while json_content.find("使用人数过多，请稍后再试") != -1 and repeat_time < 5:
                        time.sleep(repeat_time)
                        json_content = self.get_json_content(url)
                        repeat_time += 1
                    if json_content.find("使用人数过多，请稍后再试") != -1:
                        print("Failed to parse mood content for index:{}".format(pos))
                        self.format_error("Failed to parse mood content for index:{}".format(pos))
                        continue
                    self.content.append(json_content)
                    if not self.from_client:
                        # 获取每条动态的unikey
                        unikeys = self.get_unilikeKey_tid_and_smallpic(json_content)
                        if len(unikeys) != 0:
                            # 从数据中恢复后，避免重复爬取相同数据
                            if recover_index_split != 0:
                                unikeys = unikeys[recover_index_split:]
                                recover_index_split = 0
                            # 获取数据
                            until_stop_time = self.do_get_infos(unikeys, until_stop_time)
                            if self.use_redis:
                                until_stop_time = False if self.re.get(
                                    STOP_SPIDER_KEY + str(self.username)) == STOP_SPIDER_FLAG else True
                except BaseException as e:
                    self.format_error("unexpected error in parse mood content, index:{}".format(pos), e)

                pos += 20
                # 每抓100条保存一次数据
                if pos % 100 == 0 and self.use_redis:
                    force_key = self.re.get(FORCE_STOP_SPIDER_FLAG + self.username)
                    if force_key != FORCE_STOP_SPIDER_FLAG:
                        self.save_data_to_redis(final_result=False)
            except BaseException as e:
                print("ERROR===================")
                self.logging.error('wrong place')
                self.logging.exception(e)
                print("因错误导致爬虫终止....现在临时保存数据")
                self.save_all_data_to_json()
                self.save_data_to_redis(final_result=True)
                print('已爬取的数据页数(20条一页):', pos)
                print("保存临时数据成功")
                print("ERROR===================")
                exit(1)
                # raise e
        pass

    # 构造点赞的人的URL
    def get_aggree_url(self, unikey):
        url = 'https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app?'
        params = {
            "uin": self.username,
            "unikey": unikey,
            "begin_uin": 0,
            "query_count": 60,
            "if_first_page": 1,
            "g_tk": self.g_tk,
        }
        url = url + parse.urlencode(params)
        return url

    # 构造获取动态详情的url
    def get_mood_detail_url(self, unikey, tid):
        url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6?'
        params = {
            "uin": self.username,
            "unikey": unikey,
            "tid": tid,
            "t1_source": 1,
            "ftype": 0,
            "sort": 0,
            "pos": 0,
            "num": 20,
            "callback": "_preloadCallback",
            "code_version": 1,
            "format": "jsonp",
            "need_private_comment": 1,
            "g_tk": self.g_tk
        }
        url = url + parse.urlencode(params)
        return url

    # 由于有的比较老旧的说说的点赞信息被清空了，需要从这里获取点赞的数目
    def get_like_detail_url(self, unikey):
        """
        :param unikeys:
        :return:
        """
        like_url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2?'
        params = {
            "_stp": '',
            "unikey": unikey,
            # 'face': '0<|>0<|>0<|>0<|>0<|>0<|>0<|>0<|>0<|>0',
            'face': 0,
            'fupdate': 1,
            'g_tk': self.g_tk,
            'qzonetoken': ''
        }
        like_url = like_url + parse.urlencode(params)
        return like_url

    # 获取评论详情
    def get_cmt_detail_url(self, start, top_id):
        url = 'https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_getcmtreply_v6?'
        params = {
            'format': 'jsonp',
            'g_tk': self.g_tk,
            'hostUin': self.username,
            'inCharset': '',
            'need_private_comment': 1,
            'num': 20,
            'order': 0,
            'outCharset': '',
            'qzonetoken': self.qzonetoken,
            'random': '',
            'ref': '',
            'start': start,
            'topicId': top_id,
            'uin': self.raw_username
        }
        return url + parse.urlencode(params)

    # 获取点赞的人的详情
    def get_like_detail(self, curlikekey, tid):
        # unikeys = "<|>".join(curlikekey)
        unikeys = curlikekey
        like_url = self.get_like_detail_url(unikeys)
        if unikeys != '':
            try:
                like_content = json.loads(
                    self.get_json(self.req.get(like_url, headers=self.headers, timeout=20).content.decode('utf-8')))
                # like_content是所有的点赞信息，其中like字段为点赞数目，list是点赞的人列表，有的数据中list为空
                like_content['tid'] = tid
                return like_content
            except BaseException as e:
                # 因为这里错误较多，所以进行一次retry，如果不行则保留unikey
                self.format_error(e, 'Retry to get like_url:' + unikeys)
                try:
                    like_content = json.loads(
                        self.get_json(self.req.get(like_url, headers=self.headers, timeout=20).content.decode('utf-8')))
                    like_content['tid'] = tid
                    return like_content
                except BaseException as e:
                    self.error_like_detail_unikeys.append(unikeys)
                    self.format_error(e, 'Failed to get like_url:' + unikeys)
                    return dict(unikey=tid)
        else:
            self.error_like_detail_unikeys.append(unikeys)
            return dict(tid=tid)

    # 获取第一条动态
    def get_first_mood(self, mood_num):
        """
        获取用户最早的一条动态的发表时间
        :param mood_num:
        :param url_mood:
        :return:
        """
        try:
            last_page = math.ceil(mood_num / 20) - 1
            pos = 20 * last_page
            url_mood = self.get_mood_url() + '&uin=' + str(self.username)
            url = url_mood + '&pos=' + str(pos)
            mood_list = self.req.get(url=url, headers=self.h5_headers, timeout=20)
            if self.debug:
                print("第一次动态发表时间:", mood_list.status_code)
            try:
                json_content = json.loads(self.get_json(str(mood_list.content.decode('utf-8'))))
            except:
                json_content = json.loads(self.get_json(str(remove_special_tag(mood_list.text))))
            last_mood = json_content['msglist'][-1]
            self.user_info.first_mood_time = last_mood['createTime']
        except BaseException as e:
            self.user_info.first_mood_time = ''
            self.format_error(e, "Failed to get first send mood time")
        finally:
            self.user_info.save_user()

    # 评论数量超过20的说说需要再循环爬取
    def get_all_cmt_num(self, cmt_num, tid):
        top_id = self.username + '_' + tid
        # 向上取整
        page = math.ceil(cmt_num / 20)
        cmt_list = []
        for i in range(1, page):
            start = i * 20
            url = self.get_cmt_detail_url(start=start, top_id=top_id)
            if self.debug:
                print(start)
                print('获取超过20的评论的人信息:', cmt_num, url)
            # 20200807备注：QQ空间抽风，获取超过20的评论会显示未登陆
            content = self.req.get(url, headers=self.headers).content
            try:
                content_json = self.get_json(content.decode('utf-8'))
                content_json = json.loads(content_json)
                comments = content_json['data']['comments']

                cmt_list.extend(comments)
            except BaseException as e:
                # print(content)
                print("获取数量超过20的评论失败")
                self.format_error(e, content.decode("utf-8"))
                if self.debug:
                    raise e
        return cmt_list

    def do_get_infos(self, unikeys, until_stop_time):
        for unikey in unikeys:

            if (self.debug):
                print('unikey:' + unikey['unikey'])
            key = unikey['unikey']
            tid = unikey['tid']
            # 获取动态详情
            try:
                if self.download_mood_detail:
                    mood_detail = self.get_mood_detail(key, tid)
                    mood = json.loads(mood_detail)
                    # 如果达到了设置的停止日期，退出循环
                    until_stop_time = self.check_time(mood, self.stop_time, until_stop_time)
                    if self.stop_time != -1 and until_stop_time == False:
                        break
                    cmt_num = self.check_comment_num(mood)
                    if cmt_num != -1:
                        extern_cmt = self.get_all_cmt_num(cmt_num, tid)
                        mood['commentlist'].extend(extern_cmt)
                    self.mood_details.append(mood)
                # 获取点赞详情（方法一）
                # 此方法有时候不能获取到点赞的人的昵称，但是点赞的数量这个数据一直存在
                if self.download_like_detail:
                    like_detail = self.get_like_detail(unikey['curlikekey'], tid)
                    self.like_detail.append(like_detail)

                # 获取点赞详情（方法二）
                # 此方法能稳定获取到点赞的人的昵称，但是有的数据已经被清空了
                if self.download_like_names:
                    like_list_name = self.get_like_list(key, tid)
                    self.like_list_names.append(like_list_name)

                if self.download_small_image:
                    for pic_url in unikey['small_pic_list']:
                        file_name = self.tid + '--' + pic_url.split('/')[-1]
                        self.download_image(pic_url, self.SMALL_IMAGE_DIR + file_name)

                if self.download_big_image:
                    for big_pic_url in unikey['big_pic_list']:
                        if self.debug:
                            print('大图地址:', big_pic_url)
                        file_name = self.tid + '--' + big_pic_url.split('/')[-1]
                        self.download_image(big_pic_url, self.BIG_IMAGE_DIR + file_name)

                # 计数，反馈给前端
                self.mood_count += 1
                if self.use_redis:
                    self.re.set(MOOD_COUNT_KEY + str(self.username), self.mood_count)

            except BaseException as e:
                self.format_error(e, 'meet some error, but continue to capture...')
                if self.debug:
                    raise e
                continue

        return until_stop_time

    def extract_tid_from_unikey(self, unikey):
        tid = re.findall(re.compile('mood/(.*?)\.1'), unikey)
        if len(tid) > 0:
            return tid[0]
        else:
            return ''

    def get_mood_all_cmt(self, key, tid):
        mood_detail = self.get_mood_detail(key, tid)
        mood = json.loads(mood_detail)
        # 超过20的评论要继续获取
        cmt_num = self.check_comment_num(mood)
        if 'commentlist' in mood:
            if cmt_num != -1:
                extern_cmt = self.get_all_cmt_num(cmt_num, tid)
                mood['commentlist'].extend(extern_cmt)
            return mood['commentlist']
        return []

    def retry_error_unikey(self):
        """
        重新下载第一次下载中失败的数据
        :return:
        """
        # 深拷贝
        error_detail_unikeys = copy.deepcopy(self.error_like_detail_unikeys)
        self.error_like_detail_unikeys = []
        for error_detail_unikey in error_detail_unikeys:
            tid = self.extract_tid_from_unikey(unikey=error_detail_unikey)
            like_detail = self.get_like_detail(error_detail_unikey, tid)
            self.error_like_detail[error_detail_unikey] = like_detail

        error_mood_unikeys = copy.deepcopy(self.error_mood_unikeys)
        self.error_mood_unikeys = []
        for error_mood_unikey in error_mood_unikeys:
            mood_detail = self.get_mood_detail(error_mood_unikey[0], error_mood_unikey[1])
            self.error_mood[error_mood_unikey] = mood_detail

        error_like_list_unikeys = copy.deepcopy(self.error_like_list_unikeys)
        self.error_like_list_unikeys = []
        for error_like_list_unikey in error_like_list_unikeys:
            like_list = self.get_like_list(error_like_list_unikey)
            self.error_like_list[error_like_list_unikey] = like_list

    # 获得点赞的人
    def get_like_list(self, unikey, tid):
        url = self.get_aggree_url(unikey)
        if (self.debug):
            print('获取点赞的人', url)
        try:
            like_list = self.req.get(url=url, headers=self.headers)
            like_list_detail = json.loads(self.get_json(like_list.content.decode('utf-8')))
            like_list_detail['tid'] = tid
            return like_list_detail
        except BaseException:
            try:
                like_list = self.req.get(url=url, headers=self.headers)
                like_list_detail = json.loads(self.get_json(like_list.content.decode('utf-8')))
                like_list_detail['tid'] = tid
                return like_list_detail
            except BaseException as e:
                self.format_error(e, 'Failed to get agree:' + url)
                self.error_like_list_unikeys.append(unikey)
                return dict(tid=tid)

    # 获得每一条说说的详细内容
    def get_mood_detail(self, unikey, tid):
        url_detail = self.get_mood_detail_url(unikey, tid)
        if (self.debug):
            print('获取说说动态详情:', url_detail)
        try:
            mood_detail = self.req.get(url=url_detail, headers=self.headers)
            json_mood = self.get_json(str(mood_detail.content.decode('utf-8')))

            return json_mood
        except BaseException:
            try:
                mood_detail = self.req.get(url=url_detail, headers=self.headers)
                json_mood = self.get_json(str(mood_detail.content.decode('utf-8')))
                return json_mood
            except BaseException as e:
                self.format_error(e, 'Failed to get mood_detail:' + url_detail)
                self.error_mood_unikeys.append((unikey, tid))
                return {}

    # 根据unikey 获得tid
    def get_tid(self, unikey):
        # unikey是链接，形如：http://user.qzone.qq.com/1272082503/mood/4770d24bc5bb7459cc140200.1
        # 其中，4770d24bc5bb7459cc14020是tid
        tids = unikey.split("/")
        tid = tids[5].split(".")
        return tid[0]

    # unikey 是用于辨别每条说说的唯一识别码
    # unikey eg: http://user.qzone.qq.com/1272082503/mood/4770d24b81eba85b0b110800.1
    def get_unilikeKey_tid_and_smallpic(self, mood_detail, count=0):
        unikey_tid_list = []
        jsonData = json.loads(mood_detail)
        try:
            count = count
            for item in jsonData['msglist']:
                count += 1
                tid = item['tid']
                content = item['content']
                unikey = self.mood_host + tid + '.1'
                if (self.debug):
                    print('unikey:' + unikey)
                # 如果存在图片
                pic_list = []
                big_pic_list = []

                if 'pic' in item:
                    item_key = item['pic']
                    # 保存所有图片的预览图下载地址
                    for i in range(len(item_key)):
                        if 'smallurl' in item_key[i]:
                            smallurl = item_key[i]['smallurl']
                            pic_list.append(smallurl)
                        if 'url2' in item_key[i]:
                            big_url = item_key[i]['url2']
                            big_pic_list.append(big_url)

                    # 如果存在多张图片或没有图片
                    if len(item_key) != 1:
                        curlikekey = unikey + "<.>" + unikey
                    else:
                        curlikekey = item_key[0]['curlikekey']
                    # curlikekey_list.append(curlikekey)
                else:
                    curlikekey = unikey + "<.>" + unikey

                unikey_tid_list.append(
                    dict(order=count, unikey=unikey, tid=tid, small_pic_list=pic_list, curlikekey=curlikekey,
                         big_pic_list=big_pic_list, content=content))

        except BaseException as e:
            self.logging_info("faield to parse msglist, ")
            self.logging_info(jsonData)
            self.format_error(e)

        return unikey_tid_list

    def get_main_page_url(self):
        base_url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/main_page_cgi?'
        params = {
            "uin": self.raw_username,
            "g_tk": self.g_tk,
            "param": "3_" + self.raw_username + "_0|8_8_" + self.raw_username + "_0_1_0_0_1|16",
            "qzonetoken": self.qzonetoken
        }
        url = base_url + parse.urlencode(params)

        base_url2 = 'https://user.qzone.qq.com/proxy/domain/g.qzone.qq.com/fcg-bin/cgi_emotion_list.fcg?'
        params2 = {
            "uin": self.raw_username,
            "g_tk": self.g_tk,
            "login_uin": self.raw_username,
            "rd": '',
            "num": 3,
            "noflower": 1,
            "qzonetoken": self.qzonetoken
        }
        url2 = base_url2 + parse.urlencode(params2)
        return url, url2

    def get_main_page_info(self):
        """获取主页信息"""
        url, url2 = self.get_main_page_url()
        # self.headers['host'] = 'user.qzone.qq.com'
        try:
            res = self.req.get(url=url, headers=self.headers)
            if self.debug:
                print("主页信息状态:", res.status_code)
            content = json.loads(self.get_json(res.content.decode("utf-8")))
            data = content['data']['module_16']['data']
            self.user_info.mood_num = data['SS']
            self.user_info.photo_num = data['XC']
            self.user_info.rz_num = data['RZ']
            self.mood_num = self.user_info.mood_num if self.mood_num == -1 else self.mood_num
            if self.use_redis:
                self.re.set(MOOD_NUM_KEY + self.username, self.mood_num)
                self.re.rpush(WEB_SPIDER_INFO + self.username, "获取主页信息成功")
                self.re.rpush(WEB_SPIDER_INFO + self.username, MOOD_NUM_PRE + ":" + str(self.mood_num))
                if not self.no_delete:
                    self.re.expire(MOOD_NUM_KEY + self.username, EXPIRE_TIME_IN_SECONDS)

            if self.debug:
                print(self.user_info.mood_num)
                print("Finish to get main page info")

        except BaseException as e:
            self.format_error(e, "Failed to get main page info")
            if self.use_redis:
                self.re.rpush(WEB_SPIDER_INFO + self.username, GET_MAIN_PAGE_FAILED)
        try:
            self.headers['referer'] = 'https://user.qzone.qq.com/' + self.raw_username + '/main'
            res = self.req.get(url=url2, headers=self.headers)
            if self.debug:
                print("获取登陆时间状态:", res.status_code)
            content = json.loads(self.get_json(res.content.decode("utf-8")))
            data = content['data']
            first_time = util.get_standard_time_from_mktime(data['firstlogin'])
            today = int(datetime.datetime.now().year)
            first_year = int(first_time.split('-')[0])
            years = today - first_year
            self.user_info.years = years
            self.user_info.first_time = util.get_standard_time_with_name(first_time)
            if self.debug:
                print("Finish to get first time")
            print("Success to Get Main Page Info!")
        except BaseException as e:
            self.format_error(e, "Failed to get first login time")
            if self.use_redis:
                self.re.rpush(WEB_SPIDER_INFO + self.username, GET_FIRST_LOGIN_TIME)

    def calculate_qzone_token(self):
        ctx = execjs.compile(
            '''function qzonetoken(){ location = 'http://user.qzone.qq.com/%s'; return %s}''' % (
                self.raw_username, qzone_jother2))
        return ctx.call("qzonetoken")

    def get_qzone_token(self):
        url = 'https://user.qzone.qq.com/' + self.raw_username + '/main'
        if self.debug:
            print(url)
        res = self.req.get(url=url, headers=self.headers, timeout=20)
        # if self.debug:
        print("qzone token main page:", res.status_code)
        content = res.content.decode("utf-8")
        self.logging_info(content)
        qzonetoken = re.findall(re.compile("g_qzonetoken = \(function\(\)\{ try\{return \"(.*)?\""), content)[0]
        self.qzonetoken = qzonetoken
        if self.debug:
            print("qzone_token:", qzonetoken)

    def parse_recent_visit(self, file_path, time_step):
        # 必须新开线程执行
        while True:
            try:
                url, _ = self.get_main_page_url()
                res = self.req.get(url=url, headers=self.headers)
                content = json.loads(self.get_json(res.content.decode("utf-8")))
                visit_data = content['data']['module_3']['data']
                if 'items' in visit_data:
                    visit_list = visit_data['items']
                    for item in visit_list:
                        self.visit_list.append(
                            dict(qq=item['uin'], time=util.get_full_time_from_mktime(item['time']), name=item['name']))

                visit_df = pd.DataFrame(self.visit_list)
                visit_df.drop_duplicates(inplace=True)
                visit_df.to_excel(file_path, index=False)
                time.sleep(time_step)
            except BaseException:
                print("获取最近访客出错")
                exit(3)