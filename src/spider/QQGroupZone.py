from src.spider.QQZoneSpider import QQZoneSpider
from urllib import parse


class QQGroupZone(QQZoneSpider):
  """
  针对QQ群空间进行操作，主要是为下载群相册
  """

  def __init__(self, use_redis=False, debug=False, analysis=True, recover=False,
               username='', mood_begin=0, mood_num=-1, stop_time='-1', from_web=False, nickname='', no_delete=True,
               cookie_text='',
               export_excel=False, export_csv=True, pool_flag='127.0.0.1',
               download_small_image=False, download_big_image=False,
               download_mood_detail=True, download_like_detail=True, download_like_names=True):
    QQZoneSpider.__init__(self, use_redis, debug, recover=recover, username=username, mood_num=mood_num,
                          mood_begin=mood_begin, stop_time=stop_time, from_web=from_web, nickname=nickname,
                          no_delete=no_delete, cookie_text=cookie_text, pool_flag=pool_flag,
                          download_small_image=download_small_image, download_big_image=download_big_image,
                          download_mood_detail=download_mood_detail, download_like_detail=download_like_detail,
                          download_like_names=download_like_names)
    self.login_with_qr_code()
    # QQ群号
    self.qunId = '456467857'
    print(self.qunId)

  def parse_album_list_url(self):
    photo_url = 'https://h5.qzone.qq.com/proxy/domain/u.photo.qzone.qq.com/cgi-bin/upp/qun_list_album_v2?'
    params = {
      'uin': self.username,
      'g_tk': self.g_tk,
      'qzonetoken': '',
      'qunid': self.qunId,
      'qunId': self.qunId,
      'getMemberRole': 1,
      'source': 'qzone',
      'cmd': 'qunGetAlbumList',
      'format': 'jsonp',
      'platform': 'qzone',
      'inCharset': 'utf-8',
      'outCharset': 'utf-8',
      'start': 0,
      # 相册数量，可以直接填最大
      'num': 100
    }
    url = photo_url + parse.urlencode(params)
    print(url)
    return url

  def parse_album_url(self):
    url = 'https://h5.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2?g_tk=1305240398&qzonetoken=897245c1c431d3e721e49dc576f797c9ad052e97f1e34211fdc201cea34c5c58360e331995d685e5b88e82e31dbb6a85a1e0cd&callback=_Callback&t=964089143&format=jsonp&platform=qzone&inCharset=utf-8&outCharset=utf-8&source=qzone&unikey=421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G3vI*lgiqzUy%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G3rI*lje4NEY%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G3nI*lhXGz40%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G3jI*ljvWKwE%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G3fI*lj9cuAI%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G3bI*lh4*2Iq%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G3XI*ljEsuQA%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2*I*lgjGBks%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2vI*lj4ZmUs%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2rI*lhg0vgB%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2bI*lgof*YM%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2XI*lgwmIYB%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2PI*ljIKfgL%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2LI*linzaEW%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2HI*liqLMQg%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G2DI*ljWPOcD%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G1*I*liYKpU0%3C%7C%3E421_1_0_456467857%7CV139H4VC18NYlE%7CV3tkSU1G17I*lh7kJcM&_stp=1670949266251&uin=1272082503&_=1670949261177'
    params = {
      
    }
    return url + parse.urlencode(params)

  def download_group_image(self):
    album_url = self.parse_album_list_url()
    group_album_content = self.get_json(self.req.get(url=album_url, headers=self.h5_headers, timeout=20).content.decode('utf-8'))
    print(group_album_content)
    album_list = group_album_content['data']['album']
    for album in album_list:
      title = album['title']
      create_time = album['createtime']
      create_nickname = album['createnickname']
      album_id = album['id']



if __name__ == '__main__':
  qq = QQGroupZone(use_redis=False)
  qq.download_group_image()
