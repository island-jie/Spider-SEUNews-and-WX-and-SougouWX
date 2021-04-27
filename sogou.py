import requests
from bs4 import BeautifulSoup
import json
import re
import time
import pandas as pd
from pyquery import PyQuery as pq
from lxml import etree
from gne import GeneralNewsExtractor
import pymongo
#headers
head = {
    # 'SUID':"BFD3223842468299A52D372D43DA45A5",
    "Host": "weixin.sogou.com",
    "Connection": "close",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://weixin.sogou.com/weixin",
    'User-Agent' :"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    }
head1 = {
    # 'SUID':"BFD3223842468299A52D372D43DA45A5",
            'User-Agent' :"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
            'Cookie' : "ssuid=679021649; IPLOC=CN3201; SUID=8290607A2C18960A000000005F828AFB; SUV=004BE9CC7A6090825F9AB484D9571227; GOTO=; ABTEST=4|1619248660|v1; weixinIndexVisited=1; SNUID=9DCF001A6065A0D2EA384BB36056BF36; ld=Fkllllllll2kzEi5lllllpjReA7lllllWujy@yllll9lllllpllll5@@@@@@@@@@; ppinf=5|1619248737|1620458337|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTo5OiVFNiU5RCVCMHxjcnQ6MTA6MTYxOTI0ODczN3xyZWZuaWNrOjk6JUU2JTlEJUIwfHVzZXJpZDo0NDpvOXQybHVFcFFfSkp1RVVpTXdRcnpmYUlfQjJzQHdlaXhpbi5zb2h1LmNvbXw; pprdig=Lmgo27v2XurPa9CrQMJXfZ3fBTSLRxg7MbsPdk_oep6EdUDGzIMVRa-s6JGnfhWo1zDkXlD8NJvplOfCBfnM7bl01v1AUjtyr5zsCRlchqoU9Ggx7r5p8dqP4HRJrLRZQh6lMfF3wQ7ISCCIur5y0Zori_kM0uWAD18-gWIZXFQ; ppinfo=2d45318f63; passport=5|1619248737|1620458337|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTo5OiVFNiU5RCVCMHxjcnQ6MTA6MTYxOTI0ODczN3xyZWZuaWNrOjk6JUU2JTlEJUIwfHVzZXJpZDo0NDpvOXQybHVFcFFfSkp1RVVpTXdRcnpmYUlfQjJzQHdlaXhpbi5zb2h1LmNvbXw|cb2f7f7ab3|Lmgo27v2XurPa9CrQMJXfZ3fBTSLRxg7MbsPdk_oep6EdUDGzIMVRa-s6JGnfhWo1zDkXlD8NJvplOfCBfnM7bl01v1AUjtyr5zsCRlchqoU9Ggx7r5p8dqP4HRJrLRZQh6lMfF3wQ7ISCCIur5y0Zori_kM0uWAD18-gWIZXFQ; sgid=31-50416479-AWCDxmHK4OSFsv4o5oibHkH4; JSESSIONID=aaazZr84BU3Gc5F1sTIGx; ppmdig=1619442065000000744aaa15a6fcb40649eb0c2cc225fddf"
}

#给一个搜索结果页面 输出 10条链接
def getListLinks(url):
    urls = []
    response = requests.get(url, headers=head1)
    # response.encoding = 'utf-8'
    html = response.text
    # 得到的网页，判断是否有找到news
    soup = BeautifulSoup(html, 'html.parser')
    try:
        reg = soup.select('h3 a')
        for eachone in reg:
            urls.append("https://weixin.sogou.com"+eachone['href'])
    except Exception as e:
        print(e)
    return urls

def rmHtmlTags(html):
    """
    去除html标签
    :param html: html页面
    :return: 文章正文（去除标签）
    """
    soup = BeautifulSoup(html, 'html.parser')
    contentWithNoTags = soup.get_text()
    return contentWithNoTags

#获取新闻正文文章
def getArticle(news_url):
    res = requests.get(news_url)
    res.encoding = 'utf-8'
    article = res.text
    soup = BeautifulSoup(article, "html.parser")
    #发布的公众号
    publisher=""
    publish_time=""
    title=""
    content=""
    contents=""
    try:
        publisher = soup.find('a', id="js_name").get_text().strip()
    except Exception as e:
        print(e)
    # print(publisher)
    # publish_time = soup.find('em',id="publish_time").get_text().strip()
    # ppp = soup.find_all("em", attrs={"class": "rich_media_meta rich_media_meta_text"})
    #发布时间
    pattern = r'i=(.*?);'
    publish_times = re.findall(pattern, article)
    try:
        publish_time = eval(publish_times[3])
    except Exception as e:
        publish_time = ""
        print(e)
    #标题
    try:
        title = soup.find('h2', id="activity-name").get_text().strip()
    except Exception as e:
        print(e)

    #正文
    try:
        contents = soup.find('div', id="js_content").get_text().strip()
    except Exception as e:
        print(e)
    chinese = u"([\u4e00-\u9fff]+)"
    pattern = re.compile(chinese)
    content = pattern.findall(contents)
    content = ' '.join(content)
    print(content)
    return publisher,publish_time,title,content


# 请求发送时必须得带上
def get_snuid(ua):
    first_urls = [
        "https://weixin.sogou.com/weixin?query=东南大学&type=2&page=1"
    ]
    headers = {'User-Agent': ua}
    url = first_urls[0]
    rst = requests.get(url=url, headers=headers)
    pattern = r'SNUID=(.*?);'
    # snuid为发送请求时必带参数
    snuid = re.findall(pattern, str(rst.headers))
    return snuid

# 获取临时链接
def get_real_url(url):
    try:
        snuid = get_snuid("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")
        if snuid != None and len(snuid) > 0:
            print("进来")
            time.sleep(0.5)
            # Headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"
            head['Cookie'] = "SNUID={}".format(snuid[0])
            # print(head)
            # requests.packages.urllib3.disable_warnings()
            res = requests.get(url, headers=head,  timeout=5, verify=False)
            # print(res.text)
            url_text = re.findall("\'(\S+?)\';", res.text, re.S)
            # print(url_text)
            base_url = ''.join(url_text)
            # print(base_url)
            i = base_url.find("http://mp.weixin.qq.com")
            if i > 0:
                res.close()
                article_url = base_url[i:len(base_url)]
                print(article_url)
                print("打印完了真实链接")
                return article_url
            else:
                return None
        else:
            print('get snuid is none')
            return None
    except Exception as e:
        print(str(e.message))
        print(time.strftime('%Y-%m-%d %H:%M:%S'))
        return None
# 写入数据库
def putIntoMogo(InfoList):

    localhost = "127.0.0.1"
    port = 27017
    # 连接数据库
    client = pymongo.MongoClient(host = "localhost", port = port)
    # 建库
    db= client.seuNews
    # 建表
    wx_message_sheet = db.searchWXOneYear

    # 存
    for message in InfoList:
        insert_id = wx_message_sheet.insert_one(message)
        print(insert_id)
if __name__=='__main__':
    keyword = "东南大学"
    total_urls = []
    total_news = []
    page = 100
    sum = 0
    for i in range(73,page):
        cur_url = "https://weixin.sogou.com/weixin?query=东南大学&type=2&page=" + str(i)
        print("当前页面链接为："+cur_url)
        urls = getListLinks(cur_url)
        print("当前页面链接数目为："+str(len(urls)))
        # print(urls)
        messageAllInfo = []
        for item in urls:
            sum += 1
            print("当前总共爬到：" + str(sum) + "条")
            print("当前公众号链接为"+item)
            real_url = get_real_url(item)
            print("当前公众号真实链接为"+real_url)
            publisher,publish_time,title,content = getArticle(real_url)
            temple = {
                "publisher": publisher,
                "time": publish_time,
                "title": title,
                "content": content,
                "url": real_url
            }
            if (publish_time >= "2020-01-01"):
                messageAllInfo.append(temple)
            temple = {}
        putIntoMogo(messageAllInfo)
