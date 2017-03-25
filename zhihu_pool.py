#-*- coding:utf-8 -*-

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
from functools import partial

reload(sys)
sys.setdefaultencoding('utf-8')

"""
分析
<div class="zh-summary summary clearfix">
    <img data-rawheight="1280" data-width="960" ....
    class="origin_image inline-img zh-lightbox-thumb"
    data-original="https://pic3.zhimg.com/fc7b1f96b1bc37e2cdf359609db57b42_r.jpg">
</div>

<a href="/question/28550624/answer/147276777" class="toggle-expand">显示全部</a>

<a href="?page=63">63</a> 最大的页数

"""
headers = { "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate, sdch, br",
            "DNT":"1",
            "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
            "Host":"www.zhihu.com",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36"}

pic_headers = { "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding":"gzip, deflate, sdch, br",
                "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
                "DNT":"1",
                "Host":"pic2.zhimg.com",
                "Upgrade-Insecure-Requests":"1",
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36"}


def get_pic_url(url,  pagenum):
    """
    :param url: 收藏夹连接
    :param pagenum: 页数
    :return:  具体回答的链接的列表
    """
    link_list = []
    real_url = url + "?page=" +str(pagenum)
    r = requests.get(real_url, headers=headers).text
    soup = BeautifulSoup(r, 'lxml')
    for more_tag in soup.find_all("a", class_="toggle-expand"):
        link_list.append("https://www.zhihu.com" + more_tag['href'])

    return link_list

def download_pic(pic_list, dirname):
    """
    :param pic_list: 获得到的图片链接列表
    :param dirname:  保存的目录名字
    :return: None
    """
    count = 1
    if pic_list != None:
        total = len(pic_list)
    else:
        total = 0
        print "链接中没有图片"
    if os.path.exists(dirname) == False:
        os.mkdir(dirname)
    #进入具体文件目录
    os.chdir(dirname)
    for pic_url in pic_list:
        try:
            file = pic_url.split('/')[3]
            #防止重复下载图片
            if  os.path.isfile(file) == False:
                pic = requests.get(pic_url, headers=pic_headers,timeout=10)
                pic.raise_for_status()
                with open(file, "wb") as f:
                    f.write(pic.content)
                print "\r 正在下载回答中的第%s张图片， 共%s张图片"%(count, total)
            count = count + 1
        except:
            print "download %s failed"%(pic_url)
    #退回上一层目录
    os.chdir('..')
    #会遇到图片已经删除的情况，删除空的文件夹
    if count == 1:
        os.rmdir(dirname)

def get_more_pic(url, headers):
    """
    :param url: 详情页 具体问题下的回答的连接
    :param headers: 模仿浏览器
    :return:  具体问题下的原图url
    """
    more_url = []
    try:
        html = requests.get(url, headers=headers)
        html.raise_for_status()
        soup = BeautifulSoup(html.text, 'lxml')
        for pic_tag in soup.find_all("img", class_="origin_image zh-lightbox-thumb"):
            more_url.append(pic_tag['data-original'])
        return more_url
    except:
        print "can't get %s"%(url)

def get_page_num(start_url):
    """
    :param start_url: 收藏夹连接
    :return: 收藏夹的页数
    """
    try:
        html = requests.get(start_url, headers=headers)
        html.raise_for_status()
        soup = BeautifulSoup(html.text, 'lxml')
        #页面总数
        pagenum = soup.find('div', class_='zm-invite-pager').contents[11].a.string
        return pagenum
    except:
        return None

def main(start_url, page):
    link_list = get_pic_url(start_url, page)
    print "正在下载:%s%s"%(start_url + "?page=", page)
    for more_url in link_list:
        print "下载: %s中的图片"%(more_url)
        pic_list = get_more_pic(more_url, headers)
        download_pic(pic_list, more_url.split('/')[-1])

if __name__ == "__main__":
    pool = Pool(processes=4)
    start_url = "https://www.zhihu.com/collection/69105016"
    start = time.time()
    pagenum = get_page_num(start_url)
    #如果想全部下载的话 range(1,int(pagenum)+1)
    #测试时候参数可以设置成range(1,3)
    func = partial(main, start_url)
    pool.map_async(func, range(1,3))
    pool.close()
    pool.join()
    stop = time.time()
    print 'time cost : %ss'%(stop-start)
