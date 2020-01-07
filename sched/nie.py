import collections
import datetime

from core.abstract import ScheduleWebsite, Record
from util.util import make_soup


class Nieuwsblad(ScheduleWebsite):
    month_abbrv = ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    main_site = 'https://www.nieuwsblad.be/tv-gids'

    channel_urls = ['https://www.nieuwsblad.be/tv-gids/vandaag/'+str(x) for x in [0, 1, 2, 3, 6, 8]]
    channels = ('CLUB RTL', 'LA DEUX', 'LA UNE', 'ZES', 'KETNET', 'VIJF', 'VITAYA', 'CANVAS', 'Q2', 'CAZ', 'EEN', 'VTM', 'VIER')

    producer_tuple = collections.namedtuple('p_tuple', 'url producer')

    @staticmethod
    def parse_urls_from_soup(soup) -> []:
        added_urls = set()
        urls = []

        for col in soup.find('div', class_='grid channel-block').findAll('div', class_='grid__col size-1-3--bp4'):
            producer_name = col.find('div', class_='tv-guide__channel').find('a').text
            if producer_name not in Nieuwsblad.channels:
                continue

            producer = col.find('div', class_='tv-guide__channel').text.strip()
            for program in col.findAll('div', class_='program'):
                url = program.find('a')['href']
                if url not in added_urls:
                    added_urls.add(url)
                    urls.append(Nieuwsblad.producer_tuple(url, producer))
        return urls

    def get_records(self):
        records = []
        for url in self.get_programme_urls():
            print("URL : " + url.url)
            records += self.get_records_from_programme_url(url)
        return records

    @staticmethod
    def get_records_from_programme_url(url) -> [Record]: # May be multiple per page
        today = datetime.date.today()
        record = Record()
        records = []
        soup = make_soup(url.url)
        p_block = soup.find('div', class_='program-full--page')
        p_name = p_block.find('h1').text.strip()

        for program in p_block.findAll('div', class_='program-full'):
            #full_title = program.find('h3', class_='program-full__title').text.strip()

            time = program.find('span', class_='program-full__time').text
            split_time = time.split(",")

            raw_date = split_time[0].split(" ")[1:]
            month_str = raw_date[1].replace(",", '')
            day = raw_date[0]
            month = Nieuwsblad.month_abbrv.index(month_str)

            split_duration = [x.replace('u', ':') for x in split_time[1].split("-") if not x.isspace()]

            start = split_duration[0]
            end = split_duration[1]

            try:
                date = datetime.datetime(today.year, int(month), int(day))
                record.date = date.strftime("%d/%m/%Y")
            except ValueError as Exception:
                pass

            cast = soup.find('p', class_='tvguide-actors')

            if cast is not None and not len(record.cast):
                record.cast = cast.text.replace('met', '').strip()

            record.title = p_name
            record.channel = url.producer
            record.start_time = start
            record.stop_time = end

        records.append(record)

        return records

    def get_programme_urls(self): #
        urls = []
        for c_url in self.channel_urls:
            today_soup = make_soup(c_url)
            urls += self.parse_urls_from_soup(today_soup)
            for tag in today_soup.find('div', class_='tvguide-topnav').findAll('a')[2:]:
                urls += self.parse_urls_from_soup(make_soup(tag['href']))

        return urls

