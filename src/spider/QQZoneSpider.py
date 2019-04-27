# coding:utf-8
# QQ空间动态爬虫
# 包括动态内容、点赞的人、评论的人、评论的话
# 登陆使用的是Selenium， 无法识别验证码
# 若出现验证码，则先尝试手动从浏览器登陆并退出再运行程序

from selenium import webdriver
import requests
import time
from urllib import parse
import re
import json
import copy
import datetime
import logging
from src.spider.BaseSpider import BaseSpider
from src.util import util
from src.util.constant import qzone_jother2
import math
import execjs
import threading
from src.util.constant import WEB_SPIDER_INFO, FINISH_ALL_INFO, MOOD_COUNT_KEY, STOP_SPIDER_KEY, STOP_SPIDER_FLAG

class QQZoneSpider(BaseSpider):
    def __init__(self, use_redis=False, debug=False, mood_begin=0, mood_num=-1, stop_time='-1',
                 download_small_image=False, download_big_image=False,
                 download_mood_detail=True, download_like_detail=True, download_like_names=True, recover=False,
                 cookie_text=None, from_web=False, username='', nick_name='', no_delete=True):
        """
        init method
        :param use_redis: If true, use redis and json file to save data, if false, use json file only.
        :param debug: If true, print info in console
        :param mood_begin: 开始下载的动态序号，0表示从第0条动态开始下载
        :param mood_num: 下载的动态数量，最好设置为20的倍数
        :param stop_time: 停止下载的时间，-1表示全部数据；注意，这里是倒序，比如，stop_time="2016-01-01",表示爬取当前时间到2016年1月1日前的数据
        :param recover: 是否从redis或文件中恢复数据（主要用于爬虫意外中断之后的数据恢复）
        :param download_small_image: 是否下载缩略图，仅供预览用的小图，该步骤比较耗时，QQ空间提供了3中不同尺寸的图片，这里下载的是最小尺寸的图片
        :param download_big_image: 是否下载大图，QQ空间中保存的最大的图片，该步骤比较耗时
        :param download_mood_detail:是否下载动态详情
        :param download_like_detail:是否下载点赞的详情，包括点赞数量、评论数量、浏览量，该数据未被清除
        :param download_like_names:是否下载点赞的详情，主要包含点赞的人员列表，该数据有很多都被清空了
        """
        BaseSpider.__init__(self, use_redis=use_redis, debug=debug, mood_begin=mood_begin, mood_num=mood_num, stop_time=stop_time,
                            download_small_image=download_small_image, download_big_image=download_big_image,
                            download_mood_detail=download_mood_detail, download_like_detail=download_like_detail,
                            download_like_names=download_like_names, recover=recover, cookie_text=cookie_text,
                            from_web=from_web, username=username, nick_name=nick_name, no_delete=no_delete)


        self.req = requests.Session()
        self.cookies = {}
        self.qzonetoken = ""
        self.g_tk = 0
        self.init_file_name(self.file_name_head)
        self.init_parameter()

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
        print("finish to calculate g_tk")
        self.headers['cookie'] = self.cookies

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
        qzonetoken = re.findall(re.compile("g_qzonetoken = \(function\(\)\{ try\{return \"(.*)?\""), content)[0]
        self.qzonetoken = qzonetoken
        cookie = ''
        # 获取cookie
        for elem in self.web.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + ";"
        self.cookies = cookie
        print(cookie)
        print("Login success")
        logging.info("login_success")
        self.web.quit()

    # 手动添加cookie完成登陆
    def manu_get_cookie(self, cookie_text):
        self.cookies = cookie_text
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
        url_mood = self.get_mood_url()
        url_mood = url_mood + '&uin=' + str(self.username)
        pos = self.mood_begin
        recover_index_split = 0
        if self.recover:
            recover_index = self.do_recover_from_exist_data()
            if recover_index is not None:
                pos = recover_index // 20 * 20
                recover_index_split = recover_index % 20
        url = url_mood + '&pos=' + str(pos)
        print("url", url)
        res = self.req.get(url=url, headers=self.headers, timeout=20)
        mood = res.content.decode('utf-8')
        if self.debug:
            print(res.status_code)
        # print(mood)
        mood_json = json.loads(self.get_json(mood))
        mood_num = mood_json['usrinfo']['msgnum']
        self.get_first_mood(mood_num, url_mood)
        # 如果mood_num为-1，则下载全部的动态
        if self.mood_num == -1:
            self.mood_num = mood_num

        step = self.find_best_step(self.mood_num, self.thread_num)

        for i in range(0, self.thread_num):
            # pos必须为20的倍数
            start_pos = i * step
            stop_pos = (i + 1) * step if i + 1 < self.thread_num else self.mood_num
            t = threading.Thread(target=self.get_mood_in_range, args=(start_pos, stop_pos, recover_index_split, url_mood, True))
            self.thread_list.append(t)

        for t in self.thread_list:
            t.setDaemon(False)
            t.start()
            print("开始线程:", t.getName())

        # 等待全部子线程结束
        for t in self.thread_list:
            t.join()

        # 保存所有数据到指定文件
        print('保存最终数据中...')
        self.re.set(STOP_SPIDER_KEY + self.username, FINISH_ALL_INFO)
        if (self.debug):
            print('Error Unikeys Num:', len(self.error_like_detail_unikeys))
            print('Retry to get them...')
        self.retry_error_unikey()
        self.save_all_data_to_json()
        self.result_report()
        print("finish===================")

    def find_best_step(self, mood_num, thread_num):
        step = int(mood_num / thread_num // 20 * 20)
        print("Best Step:", step)
        return step

    def get_mood_in_range(self, pos, mood_num, recover_index_split, url_mood, until_stop_time):
        print("进入线程:", mood_num, until_stop_time)
        while pos < mood_num and until_stop_time:
            print('正在爬取', pos, '...')
            # self.re.lpush(WEB_SPIDER_INFO + self.username, "正在爬取" + str(pos) + "...")
            try:
                url = url_mood + '&pos=' + str(pos)
                mood_list = self.req.get(url=url, headers=self.headers, timeout=20)
                # print(mood_list.content)
                try:
                    json_content = self.get_json(str(mood_list.content.decode('utf-8')))
                except BaseException as e:
                    json_content = self.get_json(mood_list.text)
                self.content.append(json_content)

                # 获取每条动态的unikey
                unikeys = self.get_unilikeKey_tid_and_smallpic(json_content)
                if len(unikeys) != 0:
                    # 从数据中恢复后，避免重复爬取相同数据
                    if recover_index_split != 0:
                        unikeys = unikeys[recover_index_split:]
                        recover_index_split = 0
                    # 获取数据
                    until_stop_time = self.do_get_infos(unikeys, until_stop_time)
                    until_stop_time = False if self.re.get(STOP_SPIDER_KEY+ str(self.username)) == STOP_SPIDER_FLAG else True
                pos += 20
                # 每抓100条保存一次数据
                if pos % 100 == 0:
                    self.save_data_to_redis(final_result=False)
            except BaseException as e:
                print("ERROR===================")
                logging.error('位置错误')
                logging.error(e)
                print("因错误导致爬虫终止....现在临时保存数据")
                self.save_all_data_to_json()
                print('已爬取的数据页数(20条一页):', pos)
                print("保存临时数据成功")
                print("ERROR===================")
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
        url = 'https://h5.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_getcmtreply_v6?'
        params = {
            'format':'jsonp',
            'g_tk':self.g_tk,
            'hostUin':self.username,
            'inCharset':'',
            'need_private_comment':1,
            'num':20,
            'order':0,
            'outCharset':'',
            'qzonetoken':'',
            'random':'',
            'ref':'',
            'start':start,
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
                like_content = json.loads(self.get_json(self.req.get(like_url, headers=self.headers, timeout=20).content.decode('utf-8')))
                # like_content是所有的点赞信息，其中like字段为点赞数目，list是点赞的人列表，有的数据中list为空
                like_content['tid'] = tid
                return like_content
            except BaseException as e:
                # 因为这里错误较多，所以进行一次retry，如果不行则保留unikey
                self.format_error(e, 'Retry to get like_url:' + unikeys)
                try:
                    like_content = json.loads(self.get_json(self.req.get(like_url, headers=self.headers).content.decode('utf-8')))
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
    def get_first_mood(self, mood_num, url_mood):
        """
        获取用户最早的一条动态的发表时间
        :param mood_num:
        :param url_mood:
        :return:
        """
        try:
            last_page = math.ceil(mood_num / 20) - 1
            pos = 20 * last_page
            url = url_mood + '&pos=' + str(pos)
            mood_list = self.req.get(url=url, headers=self.headers, timeout=20)
            if self.debug:
                print("第一次动态发表时间:", mood_list.status_code)
            json_content = json.loads(self.get_json(str(mood_list.content.decode('utf-8'))))
            last_mood = json_content['msglist'][-1]
            self.user_info.first_mood_time = last_mood['createTime']

        except BaseException as e:
            self.format_error(e, "获取第一次发表动态时间出错")

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
            content = self.req.get(url, headers=self.headers).content
            try:
                content_json = self.get_json(content.decode('utf-8'))
                content_json = json.loads(content_json)
                comments = content_json['data']['comments']

                cmt_list.extend(comments)
            except BaseException as e:
                print(content)
                self.format_error(e, content)
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
                self.re.set(MOOD_COUNT_KEY + str(self.username), self.mood_count)

            except BaseException as e:
                self.format_error(e, 'continue to capture...')
                if self.debug:
                    raise e
                continue

        return until_stop_time

    def retry_error_unikey(self):
        """
        重新下载第一次下载中失败的数据
        :param download_image:
        :return:
        """
        # 深拷贝
        error_detail_unikeys = copy.deepcopy(self.error_like_detail_unikeys)
        self.error_like_detail_unikeys = []
        for error_detail_unikey in error_detail_unikeys:
            like_detail = self.get_like_detail(error_detail_unikey)
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
    def get_unilikeKey_tid_and_smallpic(self, mood_detail):
        unikey_tid_list = []
        jsonData = json.loads(mood_detail)
        try:
            for item in jsonData['msglist']:
                tid = item['tid']
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
                    dict(unikey=unikey, tid=tid, small_pic_list=pic_list, curlikekey=curlikekey,
                         big_pic_list=big_pic_list))

        except BaseException as e:
            self.format_error(e)
            pass
        return unikey_tid_list

    def get_main_page_url(self):
        base_url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/main_page_cgi?'
        params = {
            "uin": self.raw_username,
            "g_tk": self.g_tk,
            "param": "3_" + self.raw_username + "_0|8_8_" + self.raw_username + "_0_1_0_0_1|16",
            "qzonetoken":""
        }
        url = base_url + parse.urlencode(params)

        base_url2 = 'https://user.qzone.qq.com/proxy/domain/g.qzone.qq.com/fcg-bin/cgi_emotion_list.fcg?'
        params2 = {
            "uin": self.raw_username,
            "g_tk": self.g_tk,
            "login_uin": self.raw_username,
            "rd":'',
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

            if self.debug:
                print(self.user_info.mood_num)
                print("Finish to get main page info")
        except BaseException as e:
            self.format_error(e, "获取主页信息失败")
        try:
            self.headers['referer'] = 'https://user.qzone.qq.com/1272082503/main'
            res = self.req.get(url=url2, headers=self.headers)
            if self.debug:
                print("获取登陆时间状态:", res.status_code)
            content = json.loads(self.get_json(res.content.decode("utf-8")))
            data = content['data']
            self.user_info.first_time = util.get_standard_time_from_mktime(data['firstlogin'])
            today = int(datetime.datetime.now().year)
            first_year = int(self.user_info.first_time.split('-')[0])
            years = today - first_year
            self.user_info.years = years
            if self.debug:
                print("Finish to get first time")

        except BaseException as e:
            self.format_error(e, "获取第一次登陆时间失败")

    def calculate_qzone_token(self):
        ctx = execjs.compile(
            '''function qzonetoken(){ location = 'http://user.qzone.qq.com/%s'; return %s}''' % (self.raw_username, qzone_jother2))
        return ctx.call("qzonetoken")

    def get_qzone_token(self):
        url = 'https://user.qzone.qq.com/' + self.raw_username + '/main'
        if self.debug:
            print(url)
        res = self.req.get(url=url, headers=self.headers)
        if self.debug:
            print("qzone token main page:", res.status_code)
        content = res.content.decode("utf-8")
        qzonetoken = re.findall(re.compile("g_qzonetoken = \(function\(\)\{ try\{return \"(.*)?\""), content)[0]
        self.qzonetoken = qzonetoken
        print("qzone_token:", qzonetoken)

    def download_image(self, url, name):
        image_url = url
        try:
            r = self.req.get(url=image_url, headers=self.headers, timeout=20)
            image_content = (r.content)
            file_image = open(name + '.jpg', 'wb+')
            file_image.write(image_content)
            file_image.close()
        except BaseException as e:
            self.format_error(e, 'Failed to download image:' + name)
