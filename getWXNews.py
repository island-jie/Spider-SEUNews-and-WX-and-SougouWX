import requests
import time
import json
from pymongo import MongoClient
import pymongo
import urllib3
import random
import re
urllib3.disable_warnings()
from bs4 import BeautifulSoup
from gne import GeneralNewsExtractor
from utils import readConfig
from utils import mongoDB
import configparser

sleepTime = random.randint(1,3)
configPath = '../config.ini'
# dbConn = readConfig.read_conf_mongoDB_wx(configPath)
"""
爬取微信公众号文章的正文、阅读数、点赞数、发布时间、url、正文、封面图片、评论
写入json文件、数据库中
参考文献：https://blog.csdn.net/qq_41686130/article/details/88296981
"""

def getWechatMessageUrlList(begin=0):
    """
    从微信公众号订阅平台获得某个公众号的所有历史文章url
    :param begin: 开始页数，一页5篇文章，第二页5开始
    :return: 所有历史文章链接集合
    """
    #
    url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
    token = "329648913"
    Cookie="noticeLoginFlag=1; remember_acct=1162008006@qq.com; appmsglist_action_3867517163=card; RK=ir4BjYWzE9; ptcz=6d1d39d5593df9fe0aa1c98a6ef93b0c778bf2d68fd7df31772ec5f1ee23f503; pgv_pvi=3058238464; pgv_pvid=903954968; o_cookie=1162008006; pac_uid=1_1162008006; ua_id=ABh4oVZmSYUDufjvAAAAAHqdfN2AQ0p78pGvcDN-1hs=; mm_lang=zh_CN; eas_sid=g1H6Q0C4F744m649G9c363f0h3; iip=0; tvfe_boss_uuid=e3d8f8edd1a91f0c; AMCV_248F210755B762187F000101@AdobeOrg=-1712354808|MCIDTS|18641|MCMID|70080189729058804053698528229078979229|MCAAMLH-1611118156|11|MCAAMB-1611118156|RKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y|MCOPTOUT-1610520556s|NONE|MCAID|NONE|vVersion|4.3.0; wxuin=16915514061474; openid2ticket_o66CF5vnGm9rkGw_M5lzMJ7l1vbk=; noticeLoginFlag=1; remember_acct=linjie19980421@163.com; openid2ticket_oiID25TZlact2XRcKFlpWtNItUyg=4O7HQ+7Etx1vdeeOLrZNnVXCu5EYymYTZW6Nj6l3UcU=; luin=o1162008006; lskey=000100002aacea5284dd71795b0c18b11d9f52abdf63a8061553769bfee796585870b1e5922a6f88b1e41692; uid=144115210410646911; ptui_loginuin=3392033822; uuid=c010fdd6ed86870a3349bfa9e7b4cbf0; rand_info=CAESIHHGDzuPQn5dL9111/9PB39AxRlxuCJ07IInrCJQmY65; slave_bizuin=3867517163; data_bizuin=3867517163; bizuin=3867517163; data_ticket=Zl+YFWT1QTBt1E9OwsdSscI8xvIOVC7ju6RTSrcTQWxvtFLOkngTxZ55u5+ycwQH; slave_sid=NHVwQWliQ3NrYU0xMkFfYk9XRHFVMGVNZUFHUjZja2s0cHp3QmFpR0RHYmxHbXNyOWE1X19YM3FWeUx6bGpNWWRaNjR2RUNBQlFyUTFqeWZWTW9jS2RESXJrN0ZUUF9jWTk5ZDlQQm9LQ0t2ZURGb2NPRkc3Ujk5SkkxVHlxT2hoVzdOZlJHYTJudURjamNM; slave_user=gh_e590ec3e0d05; xid=800af1fb459b3eb27e854fb362c9c9ad; rewardsn=; wxtokenkey=777"
    headers = {
        "Cookie": Cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    }
    # fakeid是公众号独一无二的一个id，等同于后面的__biz
    # 局座召忠 fakeid = "MzIxNDEzNzI4Mg=="
    # 烽火戏诸侯MzA5OTEwMTExMg==

    fakeid = 'MzU3MTIyOTA0Nw=='
    type = '9'  # type在网页中会是10，但是无法取到对应的消息link地址，改为9就可以了

    data1 = {
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
        "random": random.random(),
        "action": "list_ex",
        "begin": begin,  # begin字段表示页数 第一页0，第二页5.。。。
        "count": "5",
        "query": "",
        "fakeid": fakeid,
        "type": type,
    }
    UrlList_json = requests.get(url, headers=headers, params=data1, verify=False).json()
    print("UTLLIST")
    print(UrlList_json)
    messageSeveralInfo = []
    if "app_msg_list" in UrlList_json:
        for item in UrlList_json["app_msg_list"]:
            # 提取每页文章的标题及对应的url
            url = item['link']
            info = {   #字典
                "url": item['link'],  # 每篇公众号的链接
                "title": item['title'],
                "digest": item['digest'],
                "create_time": getDate(item['create_time']),
                "update_time": getDate(item['update_time']),
                "cover_image": item['cover'],
                "aid": item['aid'],
                "appmsgid": item['appmsgid'],
            }
            #print("\ntitle: " + info["title"] + ' ' + info["update_time"] )
            messageSeveralInfo.append(info)
    print(messageSeveralInfo)
    time.sleep(sleepTime)
    return messageSeveralInfo
def rmHtmlTags(html):
    """
    去除html标签
    :param html: html页面
    :return: 文章正文（去除标签）
    """
    soup = BeautifulSoup(html, 'html.parser')
    contentWithNoTags = soup.get_text()
    return contentWithNoTags

def getContent(link):
    """
    get the content of a passage link
    :param passage link:
    :return:
    """
    #   从微信公众号订阅平台获得某个公众号的所有历史文章url
    _biz, mid, sn, idx = getInfoForConstructRequests(link)
    url = "https://mp.weixin.qq.com/s"
    token = "134178110"
    # Cookie = "appmsglist_action_3867517163=card; RK=ir4BjYWzE9; ptcz=6d1d39d5593df9fe0aa1c98a6ef93b0c778bf2d68fd7df31772ec5f1ee23f503; pgv_pvi=3058238464; pgv_pvid=903954968; luin=o1162008006; lskey=00010000d5da4e4ae65c0540c18b79c4d8a3725b1040ec487a302f01d0e3a446743d0800ebda3faecce7730e; o_cookie=1162008006; pac_uid=1_1162008006; ua_id=ABh4oVZmSYUDufjvAAAAAHqdfN2AQ0p78pGvcDN-1hs=; pgv_si=s7109054464; cert=Ir2ohz9dhviPNXAwYatiVlcr60OwZ8NW; openid=oiID25TZai_v8e8jjxumFhaIaCiY; uuid=42c2af4953b44d8a59508b68783efbff; media_ticket=7afef3b1178da3643692af4eddce9e608cfbee48; media_ticket_id=gh_54344a971abb; noticeLoginFlag=1; pgv_info=ssid=s5570298260; sig=h01ebc14621ccde8a31b20273ad0c4f35622a9e33e2a55a0dd1aeb32b1f1d453fd60039ba4744f8e4e1; data_bizuin=3867517163; data_ticket=oGlDXvRYqhAeqFFDdfibRkKhCpR06mL4GAg1XcMp4fDzbgXLW11OxhLz1mZKBIqR; master_key=UUJwyqZCwlRmZ0dL9BicKQj2J6xDklpe8P0nHI/JEZU=; master_user=gh_e590ec3e0d05; master_sid=ZFJKbmR5cTdLTGtjNGdCYzFCY2xBYVB5X0dCanU3R2FhRDM3XzhwNXp1WG03X0RIRnpUSGN6Q2QxUGFDNUZhbVJTMTRXSVFYZVRTbGVZZ2Y1T2VRWWFlUHQ0dWx4SEhJQWF4NXoyYjA1T09DaXRmaEwya3dhTUNYMXc0YUQ5ekRtcnNNeHdzcUg4WHJmVjhO; master_ticket=33b6e7024d5f3c6ba4f1ca4b48c6deb3; bizuin=3867517163; slave_user=gh_e590ec3e0d05; slave_sid=UEQ4SWt6Vno5RnF2ZXRLV2w1OTd0Vnp1ejhkbmJKRVFNWUlHMzE0MHRwWktaaUFvTmxFSzdUXzk4RXpxWVhxazUzQ3hPUUtQd1I5dGo4M1VGb3lzZ0dSRDdBaldrejN5WUNLWUVqMXc2emdZa3pId04zUkxLV3JjNnRkbWc0QThRZ2c4ZExvVng3bFdoeURj"
    Cookie="remember_acct=1162008006@qq.com; noticeLoginFlag=1; appmsglist_action_3867517163=card; RK=ir4BjYWzE9; ptcz=6d1d39d5593df9fe0aa1c98a6ef93b0c778bf2d68fd7df31772ec5f1ee23f503; pgv_pvi=3058238464; pgv_pvid=903954968; o_cookie=1162008006; pac_uid=1_1162008006; ua_id=ABh4oVZmSYUDufjvAAAAAHqdfN2AQ0p78pGvcDN-1hs=; mm_lang=zh_CN; eas_sid=g1H6Q0C4F744m649G9c363f0h3; iip=0; tvfe_boss_uuid=e3d8f8edd1a91f0c; AMCV_248F210755B762187F000101@AdobeOrg=-1712354808|MCIDTS|18641|MCMID|70080189729058804053698528229078979229|MCAAMLH-1611118156|11|MCAAMB-1611118156|RKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y|MCOPTOUT-1610520556s|NONE|MCAID|NONE|vVersion|4.3.0; wxuin=16915514061474; openid2ticket_o66CF5vnGm9rkGw_M5lzMJ7l1vbk=; noticeLoginFlag=1; remember_acct=linjie19980421@163.com; openid2ticket_oiID25TZlact2XRcKFlpWtNItUyg=4O7HQ+7Etx1vdeeOLrZNnVXCu5EYymYTZW6Nj6l3UcU=; luin=o1162008006; lskey=000100002aacea5284dd71795b0c18b11d9f52abdf63a8061553769bfee796585870b1e5922a6f88b1e41692; uid=144115210410646911; ptui_loginuin=3392033822; uuid=c010fdd6ed86870a3349bfa9e7b4cbf0; rand_info=CAESIHHGDzuPQn5dL9111/9PB39AxRlxuCJ07IInrCJQmY65; slave_bizuin=3867517163; data_bizuin=3867517163; bizuin=3867517163; data_ticket=Zl+YFWT1QTBt1E9OwsdSscI8xvIOVC7ju6RTSrcTQWxvtFLOkngTxZ55u5+ycwQH; slave_sid=NHVwQWliQ3NrYU0xMkFfYk9XRHFVMGVNZUFHUjZja2s0cHp3QmFpR0RHYmxHbXNyOWE1X19YM3FWeUx6bGpNWWRaNjR2RUNBQlFyUTFqeWZWTW9jS2RESXJrN0ZUUF9jWTk5ZDlQQm9LQ0t2ZURGb2NPRkc3Ujk5SkkxVHlxT2hoVzdOZlJHYTJudURjamNM; slave_user=gh_e590ec3e0d05; xid=800af1fb459b3eb27e854fb362c9c9ad"

    headers = {
        "Cookie": Cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    }

    #   局座召忠
    # fakeid = "MzIxNDEzNzI4Mg=="  # fakeid是公众号独一无二的一个id，等同于后面的__biz
    fakeid = 'MzU3MTIyOTA0Nw=='
    type = '9'  # type在网页中会是10，但是无法取到对应的消息link地址，改为9就可以了

    data1 = {
        "__biz": _biz,
        "mid": mid,
        "f": "json",
        "idx": idx, #idx会变，不能简单设为1就可以了
        "sn": sn,
        "scene": "21",
        "token": "5",
        "lang": "zh_CN",
    }
    content_json = requests.get(url, headers=headers, params=data1, verify=False).json()
    '''
    有用的字段："round_head_img": "title": "desc": "content_noencode": "create_time": "comment_id": 
    '''
    messageContent = {}
    if  "round_head_img" in content_json:
        messageContent["content_roundHeadImg"] = content_json["round_head_img"]
        messageContent["content_title"] = content_json["title"]
        messageContent["content_desc"] = content_json["desc"]
        messageContent["content_createtime"] = content_json["create_time"]
        messageContent["content_commentid"] = content_json["comment_id"]
        messageContent["content_noencode"] = rmHtmlTags(content_json["content_noencode"])
        print(messageContent["content_noencode"])
    #print(messageContent)
    return messageContent

# 毫秒数转日期
def getDate(times):
    timearr = time.localtime(times)
    date = time.strftime("%Y-%m-%d %H:%M:%S", timearr)
    return date


def getInfoForConstructRequests(link):
    """
    get some params of a passage link
    :param link:
    :return params:_biz, mid, sn, idx
    """
    # 获得mid,_biz,idx,sn 这几个在link中的信息
    _biz = link.split("&")[0].split("_biz=")[1]
    mid = link.split("&")[1].split("=")[1]
    sn = link.split("&")[3].split("=")[1]
    idx = link.split("&")[2].split("=")[1]
    return _biz, mid, sn, idx




# 写入数据库
def putIntoMogo(InfoList):
    localhost = "127.0.0.1"
    port = 27017

    # 连接数据库
    client = pymongo.MongoClient(host = "localhost", port = port)
    # 建库
    db= client.seuNews
    # 建表
    wx_message_sheet = db.wx_message_oneYear_graduate

    # 存
    for message in InfoList:
        insert_id = wx_message_sheet.insert_one(message)
        print(insert_id)


# 最大值365，所以range中就应该是73,15表示前3页
#test_link = "https://mp.weixin.qq.com/s?__biz=MjM5NjQxMDE2MQ==&mid=2650873492&idx=1&sn=b386e88d6ab6ed093d38bfd137c8ec61&chksm=bd1c18ca8a6b91dcf7fd89026bd507449176f33846373055650a7b8809c35a1355bbcc760045&token=1010720944&lang=zh_CN#rd"
#print(getComments(test_link))
#getReadLikeNum(test_link)
messageAllInfo = []

if __name__ == '__main__':
    #第一页 0  0-4
    #第二页 5  5-9
    #第三页 10 10-14
    #东南大学 一共423页
    #436 12-06
    #324继续
    flag = 1
    # lastWXTime = readConfig.read_conf_lastScrapy_wx(configPath)
    lastWXTime = "2020-01-01"
    print(lastWXTime)
    for i in range(0, 100):
        if flag == 0:
            break
        print("Page: ",i)
        messageAllInfo = []
        UrlInfoList = getWechatMessageUrlList(i * 5)
        for item in UrlInfoList:
            _biz, mid, sn, idx = getInfoForConstructRequests(item["url"])
            print("\n题目:" + item['title'] + "\t时间："+ item["update_time"] +"\n"+ item["digest"])
            if item["create_time"].split(" ")[0] < lastWXTime:
                flag = 0
                break
            temple = {
                "title": item['title'],
                "newsTime": item['create_time'].split(" ")[0],
                "url": item['url']
            }
            #得到评论
            content = getContent(item['url'])
            #往dict里加入键值对
            temple = dict(temple, **content)

            messageAllInfo.append(temple)
            #print(temple)
            #save_json("seu_dndx.json",temple)
            temple = {}
        putIntoMogo(messageAllInfo)
        print("第"+ str(i + 1) + "页存入数据库成功！")

    # db = mongoDB.MongoDB(dbConn['host'], int(dbConn['port']), dbConn['db'], "wx_message_add")
    # my_cursor = db.find({}).sort([("newsTime", -1)]).limit(1)
    # latest_news_time = my_cursor[0]["newsTime"]
    #
    # conf = configparser.ConfigParser()
    # conf.read(configPath)  # 文件路径
    # conf.set("lastScrapy", "wxtime", latest_news_time)  # 修改指定section 的option
    # conf.write(open(configPath, 'w'))
