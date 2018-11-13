# _*_ coding: utf-8 _*_

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import time
from pyquery import PyQuery as pq
import csv


def create_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    options.add_argument('lang=zh_CN.UTF-8')
    options.add_argument('user-agent="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"')
    options.add_argument('disable-infobars')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins-discovery")

    driver = webdriver.Chrome(executable_path='chromedriver.exe', chrome_options=options)
    driver.start_client()
    # driver.delete_all_cookies()
    return driver

def unfold_info(driver):
    # extend car type tab
    try:
        unfold_sel = driver.find_elements_by_css_selector('div.list-cont div.js-list-cont-btn a.btn')
        for sel in unfold_sel:
            sel.click()
            time.sleep(1)
    except NoSuchElementException:
        driver.quit()
        pass

def brand_name(driver):
    brand_name = driver.find_element_by_css_selector('div.uibox-title h2.fn-left').text
    return brand_name


def get_info(html):
    doc = pq(html, parser='html')
    # get car series info
    data_series = []
    car_series_items = doc('.tab-content-item .list-cont').items()
    for s_item in car_series_items:
        car_series_id = s_item.attr('data-value')
        car_series_title = s_item.find('.main-title a').text()
        car_series_link = 'https://car.autohome.com.cn/' + s_item.find('.main-title a').attr('href')
        cell_series = {
            'series_id': car_series_id,
            'series_title': car_series_title,
            'series_link': car_series_link,
        }
        # 'type_info': '',
        data_series.append(cell_series)
        # [{}, {}, {}], add series info as dict in list

    # get car type info
    data_series_type = []
    car_type_series_id_items = doc.find('.tab-content-item .intervalcont').items()
    for t_s_i in car_type_series_id_items:
        car_type_series_id_str = t_s_i.attr('id')
        car_type_series_id = car_type_series_id_str.lstrip('divSpecList')
        car_type_list_items = t_s_i.find('.interval01 ul.interval01-list li').items()
        for l_i in car_type_list_items:
            car_type_id = l_i.attr('data-value')
            car_type_name = l_i.find('.interval01-list-cars-infor p a').text()
            car_type_link = 'https:' + l_i.find('.interval01-list-cars-infor p a').attr('href')
            car_type_price_guidance = l_i.find('.interval01-list-guidance div').text()
            car_type_price_lowest = l_i.find('.interval01-list-lowest div .js-dprice.red-link.price-link').text()
            # car_type_price_lowest = car_type_price_lowest_sel.split('')[0]
            car_type_attention = l_i.find('.interval01-list-attention .attention .attention-value').attr('style')
            car_type_attention_percent = car_type_attention.split(':')[-1]
            cell_type = {
                'type_series_id': car_type_series_id,
                'type_info': {
                    'type_name': car_type_name,
                    'type_link': car_type_link,
                    'type_price_g': car_type_price_guidance,
                    'type_id': car_type_id,
                    'type_lowest_price': car_type_price_lowest,
                    'type_attention_percent': car_type_attention_percent
                }
            }
            data_series_type.append(cell_type)
            # [{}, {}, {}], add type info as dict in list

    # merge car series and type dict to new dict if series ID num is same
    # and add to new list
    data_sum = []
    for s in data_series:
        for t in data_series_type:
            if s['series_id'] == t['type_series_id']:
                new = dict(s, **t)
                data_sum.append(new)
    return data_sum

def save_csv(data_sum, brand_name):
    # extract dict value to add a new list as row for writing file
    data_row = []
    for d in data_sum:
        s_id = d['series_id']
        s_name = d['series_title']
        s_link = d['series_link']
        t_info = d['type_info']
        t_id = t_info['type_id']
        t_name = t_info['type_name']
        t_link = t_info['type_link']
        t_price_g = t_info['type_price_g']
        t_lowest_price = t_info['type_lowest_price']
        t_attention_percent = t_info['type_attention_percent']
        data_row.append([s_id, s_name, s_link, t_name, t_price_g, t_lowest_price, t_attention_percent, t_link, t_id])
    path = './' + 'csv'
    file_name = brand_name + '.csv'
    with open(path + './' + file_name, 'a', newline='', encoding='gbk', errors='ignore') as f:
        writer = csv.writer(f)
        writer.writerow(["车系ID", "车系名称", "车系链接", "车型名称", "车型指导价", "车型最低价", "车型关注度", "车型链接", "车型ID"])
        writer.writerows(data_row)

def crawler(driver):
    unfold_info(driver)
    html = driver.page_source
    car_data = get_info(html)
    cur_brand_name = brand_name(driver)
    save_csv(car_data, cur_brand_name)

driver = create_driver()
wait = WebDriverWait(driver, 3)

brand_num = [x for x in range(15, 17)]
for num in brand_num:
    brand_url = f'https://car.autohome.com.cn/price/brand-{num}.html'
    driver.get(brand_url)
    # try brand-num page if exists
    try:
        wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, '#errorList')))
        for i in range(1, 6):
            crawler(driver)
            # try next page if exists
            try:
                next_sel = driver.find_element_by_css_selector('a.page-item-next')
                if next_sel.get_attribute('href') != 'javascript:void(0)':
                    next_sel.click()
                    time.sleep(3)
                else:
                    break
            except NoSuchElementException:
                break
    except :
        driver.quit()
        pass

driver.quit()
