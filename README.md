# Interesting Crawler

![QQ空间说说历史曲线图](https://github.com/Maicius/InterestingCrawler/blob/master/QQZone/image/history.png)  
![QQ空间说说按点赞和评论数分类图](https://github.com/Maicius/InterestingCrawler/blob/master/QQZone/image/shuoshuoPie.png)  

- 目前包含两个个爬虫 
 
	> 1.爬取QQ空间说说内容（包括评论和点赞）     
	> 2.爬取微信好友列表  


## 抓取QQ空间说说内容并进行分析

### 爬虫文件

### QQZone.py

- python版本：3.6（推荐使用python3，因为本爬虫涉及大量文件交互，python3的编码管理比2中好很多）
- 登陆使用的是Selenium， 无法识别验证码，抓取使用requests
- 若出现验证码，则先尝试手动从浏览器登陆并退出再运行程序
- 已经抓取到的信息有：

	> 1. 所有说说信息
	> 2. 每条说说的详细信息（比1中的信息更全面，1中数据只显示每条说说的前10个评论）  
	> 3. 每条说说的点赞人列表
	> 4. 更加详细的点赞人列表（3中获取的数据有很多被清空了，这里能稳定获取到点赞的人数量、浏览量和评论量）
	> 5. 所有说说的缩略图

- 存在问题：
	
	> 评论数量超过20之后的评论信息(如评论人，评论文字)暂时无法获取，但是前20条数据是没问题的，且评论数量始终正确

- 存储方式：

	> 目前实现了两种存储方式（通过Spider中use_redis参数进行配置）:  
	> 1. 存储到json文件中   
	> 2. 存储到redis数据库中  
	> 如果安装了redis，建议存储到redis中  
	> 关于redis的安装和配置，请自行搜索  
	> Redis使用中常见问题可以参考这篇博客:[Redis 踩坑笔记](http://www.xiaomaidong.com/?p=308)

- 运行环境：
  
	> 建议使用PyCharm打开，  
	> 在PyCharm中根据import的报错可以自动安装相应模块  
	> *注意*selenium需要与chrome driver结合使用,可以查看这篇博客：  
	> [selenium之 chromedriver与chrome版本映射表（更新至v2.32）](http://blog.csdn.net/huilan_same/article/details/51896672)

#### QQZone运行方式 

- 1.安装依赖

	> pip3 install -r requirements.txt 

- 2.配置用户名和密码

	> 修改userinfo.json.example为文件userinfo.json，并填好QQ号和QQ密码
	
- 3.\_\_init\_\_函数参数说明，请根据需要修改	

	> use\_redis: 是否使用redis做数据存储和缓存，True表示使用，False表示不使用  
	> debug：是否开启debug模式，debug模式下会打印很多控制台信息，True表示启用，False表示不启用  
	> file\_name\_head: 存储数据的文件名前缀，用于多次下载时区分数据


- 4.根据需要修改核心方法 Spider.get\_mood\_list()函数参数，参数解释如下：
	
		 def get_mood_list(self, mood_begin=0, mood_num=100, recover=False, download_small_image=False,
                      download_big_image=False, download_mood_detail=True, download_like_detail=True,
                      download_like_names=True):

        """
         # 获取动态详情列表（一页20个）并存储到本地
        :param mood_begin: 开始下载的动态序号，0表示从第0条动态开始下载
        :param mood_num: 下载的动态数量，最好设置为20的倍数
        :param recover: 是否从redis或文件中恢复数据（主要用于爬虫意外中断之后的数据恢复）
        :param download_small_image: 是否下载缩略图，仅供预览用的小图，该步骤比较耗时，QQ空间提供了3中不同尺寸的图片，这里下载的是最小尺寸的图片
        :param download_big_image: 是否下载大图，QQ空间中保存的最大的图片，该步骤比较耗时
        :param download_mood_detail:是否下载动态详情
        :param download_like_detail:是否下载点赞的详情，包括点赞数量、评论数量、浏览量，该数据未被清除
        :param download_like_names:是否下载点赞的详情，主要包含点赞的人员列表，该数据有很多都被清空了
        :return:
        """ 

- 5.运行代码--获取数据

	> python3 QQZone.py

- 6.数据清理，导出csv结构数据

	> python3 QQZoneAnalysis.py

### 数据分析
### drawWordCloud.py

- python版本：3.6  
- 已经实现的分析有：

	> 1. 平均每条说说的点赞人数  
	> 2. 说说点赞的总人数
	> 3. 点赞最多的人物排名和点赞数
	> 4. 评论最多的人物排名和评论数
	> 5. 所有说说的内容分析（分词使用的是jieba）
	> 6. 所有评论的内容分析

- 待实现的目标有：

	> 发什么样的内容容易获得点赞和评论(自然语言处理)

	> 发什么样的图片容易获得点赞和评论(图像识别)

	> [可选]人物画像：分析出人物的性格特点、爱好(知识图谱)

	> [可选]历史事件抽取（自然语言处理、事件抽取）

- 运行结果：生成词云图
- 运行结果例图：

![Image](https://github.com/Maicius/wexinFriendInfo/blob/master/QQZone/image/final2.jpg)
![Image2](https://github.com/Maicius/wexinFriendInfo/blob/master/QQZone/image/comment.jpg)
![Image3](https://github.com/Maicius/wexinFriendInfo/blob/master/QQZone/image/comment_content.jpg)
![Image](https://github.com/Maicius/wexinFriendInfo/blob/master/QQZone/image/agree.jpg)
![Image](QQZone/image/bike2.png)

## 抓取微信好友信息
- 好友列表里所有好友，删除了公众号信息

### 爬虫文件
###  ReadWechatFrinedsInfo.py

- python版本： 3.6  
- 抓取到的信息格式如下：

>（用户名被加密过）   
{
"Uin": 0,  
"UserName": "@01535fb7d3f2626efda79395a24a281106c2094e987efb41b243337d9f4fbf46",  
"NickName": "HCG",  
"HeadImgUrl": "/cgi-bin/mmwebwx-bin/webwxgeticon?seq=659005699&username=@01535fb7d3f2626efda79395a24a281106c2094e987efb41b243337d9f4fbf46&skey=@crypt_731e3859_a77aa23f9d062c6d5c5fa3634412924a",  
"ContactFlag": 3,  
"MemberCount": 0,  
"MemberList": [],  
"RemarkName": "",  
"HideInputBarFlag": 0,  
"Sex": 1,  
"Signature": "",  
"VerifyFlag": 0,  
"OwnerUin": 0,  
"PYInitial": "HCG",  
"PYQuanPin": "HCG",  
"RemarkPYInitial": "",  
"RemarkPYQuanPin": "",  
"StarFriend": 0,  
"AppAccountFlag": 0,  
"Statues": 0,  
"AttrStatus":  36961,  
"Province": "广东",  
"City": "佛山",  
"Alias": "",  
"SnsFlag": 17,  
"UniFriend": 0,  
"DisplayName": "",  
"ChatRoomId": 0,  
"KeyWord": "",  
"EncryChatRoomId": "",  
"IsOwner": 0  
}

- 此外还下载了所有好友的头像

