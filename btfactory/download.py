# coding=utf-8
import re
from time import sleep
import urllib
import os
import settings

__author__ = 'silver.lao'
import urllib2

def download(url):
    index1 = url.rfind("/") + 1
    index2 = url.rfind(".")
    film_id = url[index1:index2]
    film_name = ""
    url_index = str(url).find("file.php")
    film_url = url[0:url_index] + "down.php"
    url_index1 = str(url).find("//") + 2
    url_index2 = str(url).find("/", url_index1)
    url_host = url[url_index1:url_index2]
    content = ""
    try:
        page = urllib2.urlopen(url)
        content = page.read()
        page.close()
    except urllib2.URLError:
        raise

    input_pattern = re.compile('<input type="hidden" value=".*" id=".*" name="name" />', re.IGNORECASE)

    for match in input_pattern.finditer(content):
        raw_text = str(match.group())
        mindex1 = raw_text.find('value="') + 7
        mindex2 = raw_text.find('"', mindex1)
        film_name = raw_text[mindex1:mindex2]

    bt_values = {'type': 'torrent', 'id': film_id, 'name': film_name}

    headers = {
        'Accept': 'application/x-ms-application, image/jpeg, application/xaml+xml, image/gif, image/pjpeg, application/x-ms-xbap, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/msword, */*'
        ,
        'Referer': url,
        'Accept-Language': 'zh-CN',
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; QQDownload 715; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)'
        ,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Encoding': 'gzip, deflate',
        'Host': url_host,
        'Content-Length': '50',
        'Pragma': 'no-cache',
        }
    #values = {'type':'torrent','id':'M64EGLI','name':'一本道 042412_323 鈴木さとみ 「素晴らしきハメ撮りの親近感」HD ALL'}
    data = urllib.urlencode(bt_values)

    print str(bt_values) + ">film_url>" + film_url
    #print headers
    sleep(1)
    req = urllib2.Request(film_url, data, headers)
    localName = bt_values['id'] + '.torrent'
    file_ref = urllib2.urlopen(req)
    fileName = os.path.join(settings.MEDIA_ROOT, 'bt', localName)
    f = open(fileName, 'wb')
    f.write(file_ref.read())
    f.close()


#sample url
#http://www1.wkdown.info/fs3/file.php/M65JY0K.html
#http://www1.pidown.info/bf2/file.php/M64B9IA.html
#http://www1.97down.info/qb/file.php/M64IXIS.html
download("http://www1.wkdown.info/fs3/file.php/M65JY0K.html")
sleep(1)
download("http://www1.pidown.info/bf2/file.php/M64B9IA.html")
sleep(1)
download("http://www1.97down.info/qb/file.php/M64IXIS.html")



