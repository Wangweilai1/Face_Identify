# -*- coding: utf-8 -*-
""" 百度贴吧帖子抓取
"""
import urllib.request
import json
import os
#from lxml import etree
#from pymongo import MongoClient
import sys
#reload(sys)
#sys.setdefaultencoding("utf-8")
#client = MongoClient('localhost', 27017)
tb = u'四川大学'  # 设置要抓取的贴吧
 
 
def get_tz_id(tb_name, page_num):
    tz_id = []
    for page in range(1, page_num+1):
        url = "http://tieba.baidu.com/f?kw=%s&pn=%s" % (tb_name, (page*50-50))
        html = urllib.request.urlopen(url).read()
        tree = etree.HTML(html)
        ul_li = tree.xpath('//*[@id="thread_list"]/li')[1:]
        for li in ul_li:
            data_field = li.xpath('./@data-field')  # 滤掉百度推广部分
            if data_field:
                id_ = eval(data_field[0])['id']
                tz_id.append(id_)
    return tz_id
 
 
def save_img(path, img_id, url):
    try:
        picture = urllib.request.urlopen(url).read()
    except urllib.request.URLError:
        print (urllib.request.URLError)
        picture = False
    if picture:
        if not os.path.exists(path):  # 创建文件路径
            os.makedirs(path)
        f = open('%s/%s.jpg' % (path, img_id), "wb")
        f.write(picture)
        f.flush()
        f.close()
 
 
def store_mongodb(dic):
    database = client.bdtb
    return database[tb].insert(dic)
 
 
def get_info(tz_id):
    tz_url = 'http://tieba.baidu.com/p/%s' % tz_id
    html = urllib.request.urlopen(tz_url).read()
    tree = etree.HTML(html)
    fist_floor = tree.xpath('//div[@class="l_post j_l_post l_post_bright noborder "]')
    title = tree.xpath('//div[@class="core_title core_title_theme_bright"]/h1/@title')
    content = fist_floor[0].xpath('./div[3]/div[1]/cc/div')[0]
    info = {}
 
    if content.xpath('./img'):   # 判断是否有图片,有图片为true
        text = fist_floor[0].xpath('./div[3]/div[1]/cc/div')[0].xpath('string(.)').strip()
        if len(text) == 0:
            return False  # 滤掉没有文字的帖子
        images = fist_floor[0].xpath('./div[3]/div[1]/cc/div/img')  # 获取图片
        number = 1
        image_li = []
        for each in images:
            src = each.xpath('./@src')[0]
            if src.find('static')+1:  # 滤掉贴吧表情图片
                pass
            else:
                img_id = '%s_%s' % (tz_id, number)
                save_img(tb, img_id, src)  # 保存图片到本地
                image_li.append('%s/%s_%s' % (tb, tz_id, number))
                number += 1
        info['content'] = text
        info['image'] = image_li
    else:
        info['content'] = content.text.strip()
        info['image'] = 'null'
    info['source'] = tb
    info['title'] = ''.join(title)
    data_field = fist_floor[0].xpath('./@data-field')[0]
    data_info = json.loads(data_field)
    info['dateline'] = data_info['content']['date']  # create time
    info['sex'] = data_info['author']['user_sex']  # sex
    info['author'] = data_info['author']['user_name']
    reply_floor = tree.xpath('//div[@class="l_post j_l_post l_post_bright  "]')
    reply_li = []
    for each_floor in reply_floor:
        if not each_floor.xpath('./div[3]/div[1]/cc/div'):  # 滤掉百度推广
            return False
        reply_content = each_floor.xpath('./div[3]/div[1]/cc/div')[0].xpath('string(.)').strip()
        reply_info = {}
        if len(reply_content) > 0:  # 滤掉无文字的回复
            re_field = each_floor.xpath('./@data-field')[0]
            re_info = json.loads(re_field)
            reply_info['dateline'] = re_info['content']['date']
            reply_info['author'] = re_info['author']['user_name']
            reply_info['content'] = reply_content
        reply_li.append(reply_info)
    info['reply'] = reply_li
    store_mongodb(info)
 
 
def main():
    id_list = get_tz_id(tb, 1)
    for each in id_list:
        get_info(each)
        # break
    client.close()
if __name__ == "__main__":
    main()
