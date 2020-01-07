import os
from urllib.error import URLError

from bs4 import BeautifulSoup
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

import urllib
from urllib import request
from requests import Session

driver = None

def make_soup(input_url):
    try:
        html_headers = {'User-Agent': 'Mozilla/5.0'
                                      'KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                        'Accept-Encoding': 'none',
                        'Accept-Language': 'en-US,en;q=0.8',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Connection': 'keep-alive'}
        req = urllib.request.Request(input_url, headers=html_headers)
        return BeautifulSoup(urllib.request.urlopen(req).read(), "lxml")
    except UnicodeEncodeError as e:
        r = Session().get(url=input_url)
        return BeautifulSoup(r.content, "lxml")
    except URLError as e:
        print("Error with URL: " + input_url)
        return BeautifulSoup('', features='lxml')

# TO DO: Normalize film strings

def create_web_driver():
    global driver

    if driver is None:
        chrome_driver_path = os.path.dirname(os.path.abspath(__file__)) + "/chromedriver.exe"
        chrome_options = Options()

        driver = webdriver.Chrome(executable_path=chrome_driver_path, chrome_options=chrome_options)
        driver.set_window_size(1920, 1080)


def get_sel_web_driver() -> webdriver.Chrome:
    global driver
    if driver is None:
        create_web_driver()
    return driver

