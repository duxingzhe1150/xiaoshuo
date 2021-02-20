# This is a sample Python script.

import schedule
import time
import datetime
import requests
import base64
import os
import json
from pymysql_comm import UsingMysql
from my_log import Logger
from bs4 import BeautifulSoup
import traceback


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
my_session_poor = {}
main_log = Logger('all.log', level='debug')
my_token = {'access_token': '', 'expires_in': 1}

s = requests.session()


# 获取session
def get_session(nsrsbh):
    if my_session_poor.get(nsrsbh):
        return my_session_poor[nsrsbh]
    else:
        this_session = requests.Session()
        this_session.headers.update(header)
        xxx = {nsrsbh: this_session}
        my_session_poor.update(xxx)
        return this_session


# 下载验证码图片
def request_download(nsrsbh):
    IMAGE_URL = "http://www.bwfapiao.com/qypt/manage/validateCode?timestamp=1610855935826"
    my_session = get_session(nsrsbh)

    r = my_session.get(IMAGE_URL)
    main_log.logger.info(my_session.cookies)
    with open('./image/img.png', 'wb') as f:
        f.write(r.content)


def get_api_token(flag):
    if my_token['expires_in'] < 1000 or flag == 1:
        r = requests.get('https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&'
                         'client_id=PFSBty4IfIDUgbUALAG7ho51&client_secret=M1L9PXGMGOMNZXb4VqZzv6VXNRyNUaT2')
        result = json.loads(r.text)
        main_log.logger.info('刷新图片识别token')
        main_log.logger.info(result)
        xx = {'access_token': result['access_token'], 'expires_in': result['expires_in']}
        my_token.update(xx)
        return result['access_token']
    else:
        return my_token['access_token']


# 获取验证码值
def get_code(nsrsbh):
    os.makedirs('./image/', exist_ok=True)
    request_download(nsrsbh)
    request_url0 = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
    # 二进制方式打开图片文件
    f = open('./image/img.png', 'rb')
    img = base64.b64encode(f.read())
    params = {"image": img}

    request_url = request_url0 + "?access_token=" + get_api_token(0)
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    result = json.loads(response.text)
    main_log.logger.info(result)

    if 'error_code' in result:
        request_url1 = request_url0 + "?access_token=" + get_api_token(1)
        response = requests.post(request_url1, data=params, headers=headers)
        result = json.loads(response.text)
        main_log.logger.info(result)

    words_result = result['words_result']
    words = words_result[0]['words']
    main_log.logger.info(words)
    return words


# 登录
def login():
    postdated = {'username': "yuanjiangting", 'password': "yjt123"}
    url = 'http://crm.bwfapiao.com/manage/login.do'

    r = s.post(url, data=postdated)
    main_log.logger.info(r.text)


# 查询接口数据
def getdate():
    s.headers.update(header)
    url = 'https://qxs.la/top/3'
    r = s.get(url)
    # print(r.text)
    soup = BeautifulSoup(r.content, 'html.parser')

    result = soup.findAll('li', class_='cc2')
    print(len(result))
    # print(result_1)

    for inx, item in enumerate(result):
        if item.a:
            print(item.find('a').get('href'))
            print(item.find('a').string)
            print(inx)
            if inx <= 22:
                continue
            url_1 = 'https://qxs.la' + item.find('a').get('href')
            r_1 = s.get(url_1)
            # print(r_1.text)
            soup_1 = BeautifulSoup(r_1.content, 'html.parser')
            result_1 = soup_1.findAll('div', class_='chapter')
            story_name = item.find('a').string
            story_desc = soup_1.select('.desc')[0].get_text()
            story_type = soup_1.select('.w3')[0].font.string
            story_author = soup_1.select('.w2')[0].a.string
            story_id = 123
            if inx > 23:
                data_one = {'story_name': story_name, 'story_desc': story_desc, 'story_type': story_type,
                            'story_author': story_author, 'story_search': inx}
                story_id = create_story(data_one)
            for inx2, item2 in enumerate(result_1):
                if (inx == 23 and inx2 > 3090) or inx > 23:
                    print(item2.find('a').get('href'))
                    print(item2.find('a').string)
                    print(inx2)
                    save_detail(item2, story_id, inx2)


def save_detail(item2, story_id, inx2):
    try:
        url_2 = 'https://qxs.la' + item2.find('a').get('href')
        r_2 = s.get(url_2)
        # print(r_2.text)
        soup_2 = BeautifulSoup(r_2.content, 'html.parser')
        result_2 = soup_2.select('#content')
        detail = ''
        for string in result_2[0].stripped_strings:
            if 'qxs.la' in string:
                continue
            detail += string
            detail += '\n'
        chapter_name = item2.find('a').string
        create_chapter(story_id, chapter_name, inx2, detail)
        # time.sleep(1)
    except:
        print(traceback.format_exc())
        time.sleep(5)
        save_detail(item2, story_id, inx2)


def job_pull():
    main_log.logger.info('Job1:每隔10分钟执行一次的任务')
    main_log.logger.info('Job1-startTime:%s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    check_it()
    main_log.logger.info('Job1-endTime:%s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    main_log.logger.info('------------------------------------------------------------------------')


# 初始化定时任务
def init_job():
    schedule.every(10 * 60).seconds.do(job_pull)
    while True:
        schedule.run_pending()


# 任务主程序
def check_it():
    getdate()


# 检查是否需要登录
def check_login(nsrsbh):
    url = 'http://www.bwfapiao.com/qypt/invoice/queryInvoices.do?FLAG=&GSM=&HM=&PDFSCZT=&FLAG_TIME=1'
    my_session = get_session(nsrsbh)
    r = my_session.get(url)
    main_log.logger.info(r.text)
    result = json.loads(r.text)

    if result['code'] == 0:
        return False
    else:
        return True


# 插入记录
def create_story(data_one):
    with UsingMysql(log_time=True) as um:
        print(data_one)
        sql = "INSERT INTO `t_bussiness_story`(`story_name`, `story_desc`, `story_type`, `story_author`, `story_search`)" \
              " VALUES ('%s', '%s', '%s', '%s', %d)" % \
              (data_one['story_name'], data_one['story_desc'].replace("'", "‘"), data_one['story_type'], data_one['story_author'],
               data_one['story_search'])

        um.cursor.execute(sql)
        story_id = um.cursor.lastrowid
        return story_id


# 插入记录
def create_chapter(story_id, chapter_name, chapter_index, story_text):
    with UsingMysql(log_time=True) as um:
        sql = "INSERT INTO `t_bussiness_chapter`(`story_id`, `chapter_name`, `chapter_index`)" \
              " VALUES (%d, '%s', '%s')" % (story_id, chapter_name.replace("'", "‘"), chapter_index)

        # print(sql)
        um.cursor.execute(sql)

        chapter_id = um.cursor.lastrowid
        sql = "INSERT INTO `t_bussiness_info`(`chapter_id`, `story_text`)" \
              " VALUES (%d, '%s')" % (chapter_id, story_text.replace("'", "‘"))
        # print(sql)
        um.cursor.execute(sql)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    getdate()
    # data_one = {'story_name': '凌霄阁', 'story_desc': '凌霄阁宗规其一', 'story_type': '玄幻', 'story_author': '凌霄阁弟子'}
    # story_id = create_story(data_one)
    # create_chapter(story_id, '第一章', 1, '凌霄阁宗规其一：凌霄阁弟子，每一日拥有挑战机会一次，每五日拥有被挑战机会一次！战斗双方实力不得'
    #                                    '相差三个层次，不得避战，不得怯战，违之逐出门墙。胜方依据对手弟子等级奖励相应贡献点数，负方依据本身弟子等级扣除相应贡献点数。')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
