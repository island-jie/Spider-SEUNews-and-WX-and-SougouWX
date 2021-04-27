import requests
from bs4 import BeautifulSoup
import json
import re
import lxml
import pandas as pd
import time
import pymongo

from gne import GeneralNewsExtractor
from utils import readConfig
from utils import mongoDB
import urllib3
import configparser
urllib3.disable_warnings()
#所有新闻板块的zoneId
# zoneIDList = ["5487", "5486", "5485",         "5513", "5528", "5527", "hzjl",
#               "5496", "5530"         , "5495",                    ]
zoneIDList = ["5487", "5486", "5485",          "5528", "5527", "hzjl",
              "5496", "5530"         , "5495",                    ]
zoneIDListTest = [ "hzjl",
              "5496", "5530"         , "5495"]
#"5537" 视频
sleepTime = 0
configPath = '../config.ini'
dbConn = readConfig.read_conf_mongoDB_news(configPath)
print(dbConn)
class News:
    def __init__(self, zoneId):
        """
        :param zoneId: 官网新闻分为多个板块，每个板块具有其ID
        """
        self.head = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
            "Cookie": "gr_user_id=8b06eef3-604b-479a-8ab3-be9511d0cd9e; zg_8da79c30992d48dfaf63d538e31b0b27=%7B%22sid%22%3A%201601427446718%2C%22updated%22%3A%201601428155554%2C%22info%22%3A%201600870464745%2C%22superProperty%22%3A%20%22%7B%7D%22%2C%22platform%22%3A%20%22%7B%7D%22%2C%22utm%22%3A%20%22%7B%7D%22%2C%22referrerDomain%22%3A%20%22%22%2C%22zs%22%3A%200%2C%22sc%22%3A%200%2C%22firstScreen%22%3A%201601427446718%7D; zg_did=%7B%22did%22%3A%20%22174a1f2626c599-056043056e3763-3d634d00-144000-174a1f2626d958%22%7D; zg_=%7B%22sid%22%3A%201601517211095%2C%22updated%22%3A%201601517211100%2C%22info%22%3A%201601100558399%2C%22superProperty%22%3A%20%22%7B%7D%22%2C%22platform%22%3A%20%22%7B%7D%22%2C%22utm%22%3A%20%22%7B%7D%22%2C%22referrerDomain%22%3A%20%22ehall.seu.edu.cn%22%2C%22cuid%22%3A%20%22220205053%22%2C%22zs%22%3A%200%2C%22sc%22%3A%200%2C%22firstScreen%22%3A%201601517211095%7D; NSC_xfcqmvt-03-iuuqt=ffffffff0948651c45525d5f4f58455e445a4a423660"
        }
        self.zoneId = zoneId
        self.urls = []            #每个板块的链接集合
        self.allnews = {}        #每个板块的所有新闻
        self.sourceUrl = 'https://news.seu.edu.cn/'+ zoneId +"/list.htm"    #源链接，第一页


    def StrToInt(self, s):
        """
        string 2 int
        :param s:
        :return:
        """
        try:
            return int(s)
        except:
            return 0
    def getLinksList(self, url):
        """
        given a sourceUrl,get all news urls
        :param url:新闻源链接，及各个板块新闻首页
        :return: linksList
        """
        urls = []
        response = requests.get(url, headers = self.head, verify=False)
        html = response.text
        soup = BeautifulSoup(html,"html.parser")
        time.sleep(sleepTime)
        page_num = int(soup.select('.all_pages')[0].text)            #总页数
        news_num = int(re.findall(r"\d+\.?\d*",soup.select('.all_count')[0].text)[0])    #新闻总数
        per_count = int(soup.select('.per_count')[0].text)            #每页多少条新闻
        #print(page_num,news_num,per_count)
        #news_zone = soup.find('div', id='wp_news_w6').select()
        news_list = soup.select(".news_title a")

        for news_item in news_list:
            urls.append(news_item["href"])                #该页的所有新闻链接集合
        return page_num,news_num,per_count,urls


    def getNewsDetail(self, url):
        """
        自己分析网页结构
        :param url:
        :return:
        """
        urlPrefix = "https://news.seu.edu.cn/"
        urlComplete = urlPrefix + url                #具体新闻链接
        response = requests.get(urlComplete, headers=self.head, verify=False)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        time.sleep(sleepTime)
        if len(soup.select('.arti_title')) > 0:
            title = soup.select('.arti_title')[0].text        #新闻标题
        else:
            title = "无"
        if len(soup.select('.arti_update')) > 0:            #新闻时间
            newsTime = soup.select('.arti_update')[0].text
        else:
            newsTime = "无"
        if len(soup.select('.WP_VisitCount')) > 0:
            viewCountUrl = soup.select('.WP_VisitCount')[0]["url"]
        else:
            viewCountUrl = "0"
        article = ""
        passages = soup.select('.p_text_indent_2')
        if(len(passages) != 0):                    #新闻正文  包含新旧两种网页结构 分别判断
            for passage in passages:
                article += passage.text
        else:
            if len(soup.select('.wp_articlecontent')) > 0:
                passages = soup.select('.wp_articlecontent')[0].text
                article = passages
        #新闻浏览次数  动态的，通过js获取
        viewCount = requests.get("https://news.seu.edu.cn/"+viewCountUrl, headers = self.head, verify = False).text
        return title, newsTime, self.StrToInt(viewCount), article
    def getNewsDetailByGNE(self, url):
        """
        GNE分析网页结构
        :param url:
        :return:
        """
        urlPrefix = "https://news.seu.edu.cn/"
        urlComplete = urlPrefix + url                #具体新闻链接
        response = requests.get(urlComplete, headers=self.head, verify=False)
        html = response.text
        extractor = GeneralNewsExtractor()
        result = extractor.extract(html)
        title = result['title']
        newsTime = result['publish_time']
        article = result['content']
        #新闻浏览次数  动态的，通过js获取
        # soup = BeautifulSoup(html, "html.parser")
        # viewCount = 0
        # if len(soup.select('.WP_VisitCount')) > 0:
        #     viewCountUrl = soup.select('.WP_VisitCount')[0]["url"]
        #     viewCount = self.StrToInt(requests.get("https://news.seu.edu.cn/"+viewCountUrl, headers = self.head, verify = False).text)
        return title, newsTime , article

# 写入数据库
def putIntoMogo(InfoList):

    localhost = "127.0.0.1"
    port = 27017
    # 连接数据库
    client = pymongo.MongoClient(host = "localhost", port = port)
    # 建库
    db= client.seuNews
    # 建表
    wx_message_sheet = db.newsOneYear

    # 存
    for message in InfoList:
        insert_id = wx_message_sheet.insert_one(message)
        print(insert_id)

def save_json(fname, data):
    """
    存json文件
    :param fname: 文件位置
    :param data: 数据
    :return:
    """
    assert isinstance(fname, str)
    if ".json" not in fname:
        raise IOError("fname must be json", fname)
    with open(fname, "a+", encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
        f.write("\n")

#print(news.getNewsDetail("https://news.seu.edu.cn/_s95/2014/0409/c5486a58043/page.htm"))

if __name__ == '__main__':
    #读取上次爬到哪里
    lastOfficialTime = readConfig.read_conf_lastScrapy(configPath)
    print(lastOfficialTime)
    for id in zoneIDListTest:
        flag = 1
        news = News(id)
        print("当前源链接：", news.sourceUrl)
        page_num,news_num,per_count,urls = news.getLinksList(news.sourceUrl)
        #news.urls.extend(urls)
        #print(news.urls)
        allSourceUrl = []
        for index in range(page_num): #14  0-13
            print("目前在第" + str(index) + "页")
            cur_url = 'https://news.seu.edu.cn/' + news.zoneId + "/list" + str(index+1) + ".htm"
            allSourceUrl.append(cur_url)
        print("所有源链接集合：")
        print(allSourceUrl)
        print("获取所有新闻中：...")
        for index in range(0, len(allSourceUrl)):
            if flag == 0:
                break
            print("第"+str(index)+"源链接")
            getfromSourceUrl = news.getLinksList(allSourceUrl[index])[3]
            messageAllInfo = []
            for url in getfromSourceUrl:
                print(url)
                title, newsTime, article = news.getNewsDetailByGNE(url)
                print(title, newsTime, article)

                temple ={
                    "id":id,
                    "title": title,
                    "newsTime": newsTime,
                    "article": article,
                    "url": "https://news.seu.edu.cn/"+url
                }
                if newsTime < lastOfficialTime:
                    flag = 0
                    break
                if not(article==""):
                    messageAllInfo.append(temple)
                # print(temple)
                #save_json("seu_dndx_october.json", temple)
                temple = {}
            putIntoMogo(messageAllInfo)
            print(str(id) +"第"+str(index)+"个源链接"+"存入数据库成功！")

    #找到当前的最大时间，更新config
    db = mongoDB.MongoDB(dbConn['host'], int(dbConn['port']), dbConn['db'], dbConn['table'])
    my_cursor = db.find({}).sort([("newsTime", -1)]).limit(1)
    latest_news_time = my_cursor[0]["newsTime"]

    conf = configparser.ConfigParser()
    conf.read(configPath)  # 文件路径
    conf.set("lastScrapy", "officialTime", latest_news_time)  # 修改指定section 的option
    conf.write(open(configPath, 'w'))

