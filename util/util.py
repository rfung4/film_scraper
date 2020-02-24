import datetime
from urllib.error import URLError
from bs4 import BeautifulSoup
import urllib
from urllib import request
from requests import Session
from core.abstract import Record

alpha = 'abcdefghijklmnopqrstuvwxyz'.upper()


schedule_headers_map = {
    'title': 'Original Title', 'date': 'Date', 'channel': 'Channel',
    'start_time': 'Start Time', 'stop_time': 'Stop Time', 'original_title': 'Original Title',
    'yop': 'Year of production', 'season': 'Season', 'seasons': 'Seasons', 'total_no_of_ep': 'Total number of episodes',
    'cop': 'Countries of production ', 'genre': 'Genre', 'subgenre': 'Sub Genre', 'broadcast_lang': 'Broadcast language',
    'type': 'Series/Movie', 'id': 'ID', 'cast': 'Cast', 'episode': 'Episode'
}

""" Maps instance variables to formatted Headers """

series_headers_map = {
    'title': 'Title', 'cast': 'actors', 'language': 'Broadcast language', 'episode': 'Episode',
    'season': 'Season', 'type': 'Series/Movie', 'yop': 'Year of Production', 'season_year': 'Season Year'
}


movie_summary_headers = {
    'title': 'Title', 'yop': 'Production Date', 'language': 'Language', 'cast': 'Actors', 'type': 'Movie/Series'
}

series_summary_headers = {
    'title': 'Series Name', 'season': 'Season', 'season_year': 'Season year', 'count': 'No. of Episodes',
    'type': 'Movie/Series'
}

driver = None


def print_record_sched(record: Record):
    _print_record_fields(record, schedule_headers_map, 'schedule')


def print_record_summary(record: Record):
    _print_record_fields(record, series_headers_map, 'summary')


def _print_record_fields(record: Record, field_map: {}, type_name: str):
    for k, v in vars(record).items():
        if k in field_map.keys() and len(v):
            print(f"Set {field_map[k]} : {v} ({type_name})")
    print("\n")


def get_current_date_string() -> str:
    n = datetime.datetime.now()
    return n.strftime("%m_%d_%y__%H%M")


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
        return BeautifulSoup('', features='lxml')



