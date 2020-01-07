import datetime
import re
from urllib.error import URLError
from bs4 import BeautifulSoup
import xlsxwriter

from core.abstract import Record
from sched.nie import Nieuwsblad
from util.util import make_soup

alpha = 'abcdefghijklmnopqrstuvwxyz'.upper()
today = datetime.date.today()
ep_regex = re.compile('.*[0-9]+ ([Ee])pisode(s)*.*')

headers_map = {
    'title': 'Uitzendtitel', 'date': 'Datum', 'channel': 'Zender',
    'start_time': 'Beginuur', 'stop_time': 'Einduur', 'original_title': 'Titel',
    'yop': 'Jaar', 'season': 'Jaargang', 'total_no_of_ep': 'Totaal aantal afleveringen',
    'cop': 'Productielanden', 'genre': 'Genre', 'subgenre': 'SubGenre', 'broadcast_lang': 'Taal van uitzending',
    'series': 'Serie of film', 'id': 'ID', 'cast': 'Cast'
}


def records_to_xml(records: [Record]):
    workbook = xlsxwriter.Workbook("schedule_output_2020.xlsx")
    worksheet = workbook.add_worksheet()
    headers = {k: headers_map[k] for k, v in Record().__dict__.items() if type(v) in (int, float, str)}

    for c, h in enumerate(headers):
        worksheet.write(alpha[c]+str(1), headers[h])

    for row, record in enumerate(records):
        for c, v in enumerate(headers):
            worksheet.write(alpha[c]+str(row+2), str(getattr(record, v)))

    workbook.close()


def find_textblock_tag(soup, title):
    try:
        for block in soup.findAll('div', class_='txt-block'):
            if title.lower() in block.find('h4', class_='inline').text.strip().lower():
                return block
    except Exception as e:
        pass


def find_inline_tag(soup, title):
    try:
        for block in soup.findAll('div', class_='see-more inline canwrap'):
            if title.lower() in block.find('h4', class_='inline').text.strip().lower():
                return block
    except Exception as e:
        pass


def get_div_from_header(soup, header):
    for div in soup.find('div', class_='seasons-and-year-nav').findAll('div'):
        if header in div.find('h4'):
            return div


def parse_imdb_page(record, soup: BeautifulSoup):

    if not len(record.yop):
        pass

    if not len(record.title):
        tag = soup.find('div', class_='originalTitle')
        if tag is not None:
            record.original_title = tag.text.replace('(original title)', '').strip()

    if not len(record.genre):
        tag = find_inline_tag(soup, 'Genres')
        if tag is not None:
            record.genre = tag.find('a').text.strip()

    if not len(record.cop):
        tag = find_inline_tag(soup, 'Country')
        if tag is not None:
            record.cop = tag.find('a').text.strip()

    if not len(record.broadcast_lang):
        tag = find_textblock_tag(soup, 'Language')
        if tag is not None:
            record.broadcast_lang = tag.find('a').text.strip()

    if not len(record.total_no_of_ep):
        raw_count_tag = soup.find('div', class_='button_panel navigation_panel')

        if raw_count_tag is not None:
            raw_count = raw_count_tag.find('span', text=ep_regex.match)
            if raw_count is not None:
                record.total_no_of_ep = raw_count.text.split(" ")[0].strip()

    if not len(record.season):
        year_nav = soup.find('div', class_='seasons-and-year-nav')

        if year_nav is not None:
            season_box = year_nav.findAll('a', href=re.compile('.*episodes?season=.*').match)
            seasons = [x.text for x in season_box]
            seasons.sort(reverse=True)
            record.season = seasons[0] if len(seasons) else ''

    if not len(record.cast):
        cast_table = soup.find('table', class_='cast_list')
        if cast_table is not None:
            cast_box = cast_table.findAll('tr', class_=True)
            cast_list = [r.find('td', class_=False).text.strip().replace(",", '') for r in cast_box]
            cast_list = [x for x in cast_list if len(x)]
            record.cast = ' ,'.join(cast_list)

    if not len(record.yop):
        yop_tag = find_textblock_tag(soup, 'Release Date')
        if yop_tag is not None:
            record.yop = extract_year_from_date(yop_tag.text.strip())


en_wiki_base = 'https://en.wikipedia.org/wiki/'
nl_wiki_base = 'https://nl.wikipedia.org/wiki/'

en_wiki_search = 'https://en.wikipedia.org/w/index.php?sort=relevance&search='
nl_wiki_search = 'https://nl.wikipedia.org/w/index.php?search='

imdb_find_url = 'https://www.imdb.com/find?q='
imdb_base_url = 'https://www.imdb.com'


def get_soup_from_wiki_search(record: Record, search_url: str) -> BeautifulSoup:
    search_soup = make_soup(search_url)

    if 'search=' not in search_url:
        return search_soup

    # if 'disamigious' in article, go to page

    results = search_soup.findAll('li', class_='mw-search-result')

    for result in results:
        if record.title.lower() in result.find('a').text.lower():
            url = en_wiki_base if 'en.' in search_url else nl_wiki_base
            url += result.find('a')['href']
            return make_soup(url)


def title_to_search(title):
    return title.replace(' ', '_').replace("'", '%27')


def add_info(record: Record):      # Return if page was found & information added
    parsed = False

    try:
        url = en_wiki_base+title_to_search(record.title)
        soup = make_soup(url)
        if soup is not None:
            parsed = parse_wiki_page_en(record, soup)
    except URLError as e:
        print("Ex!")
        pass

    if not parsed:
        try:
            url = nl_wiki_base + title_to_search(record.title)
            parsed = parse_wiki_page_nl(record, make_soup(url))
        except URLError as e:
            print("Ex!")
            pass

    soup = make_soup(imdb_find_url+record.title.replace(' ', '+'))

    if soup.find('div', class_='findNoResults') is not None:
        return

    s = None

    for search in soup.findAll('div', class_='findSection'):
        if 'Titles' in search.find('h3').text:
            s = search
            break

    if s is not None:
        titles = [x for x in s.find('table').findAll('tr')]

        if titles is not None:
            match = list(filter(
                lambda x: record.title.lower() in x.find('td', class_='result_text').find('a').text.strip().lower(),
                titles))

            if len(match) > 0:
                title = match[0]
                matching_url = imdb_base_url + title.find('a')['href']
                print("Parsing IMDB page: "+ matching_url)
                parse_imdb_page(record, make_soup(matching_url))


def parse_ep_count(raw):
    digits = ' '.join([x for x in raw.replace(",", '') if x.isdigit() or x.isspace()])
    return max(digits.split(" ")) if len(digits) > 0 else ''


def extract_year_from_date(raw):
    digits = ''.join([x for x in raw if x.isdigit()or x.isspace()])
    for digit in digits.split(" "):
        if len(digit) == 4:
            return digit
    return ''


def parse_wiki_page_en(record: Record, soup: BeautifulSoup) -> bool:

    table = soup.find('table', class_='infobox vevent')
    table_map = {}

    if soup.find('table', class_='infobox vevent') is None:
        return False

    for row in table.findAll('tr'):

        header = row.find('th')
        element = row.find('td')

        if element and header:
            text = '\n'.join([x.text.strip() for x in element.findAll('a')])
            if not len(text):
                text = element.text
            table_map[header.text.strip()] = text

    if 'Genre' in table_map.keys():
        record.genre = table_map['Genre'].split("\n")[0]

    if 'Country of origin' in table_map.keys():
        record.cop = table_map['Country of origin']

    if 'Original language(s)' in table_map.keys():
        record.broadcast_lang = table_map['Original language(s)']

    if 'No. of episodes' in table_map.keys():
        record.total_no_of_ep = parse_ep_count(table_map['No. of episodes'])

    if 'No. of seasons' in table_map.keys():
        record.season = parse_ep_count(table_map['No. of seasons']).split(" ")[0]
        print("Set Season: " + record.season)

    if 'Original release' in table_map.keys():
        record.yop = extract_year_from_date(table_map['Original release'])

    #print(str(table_map))
    return True


def parse_wiki_page_nl(record: Record, soup: BeautifulSoup):

    if soup is None:
        return False

    table = soup.find("table", class_='toccolours vatop infobox')

    if table is None:
        return False

    table_map = {}

    for row in table.findAll('tr'):
        elements = row.findAll('td')
        if len(elements) > 1:
            text = '\n'.join([x.text.strip() for x in elements[1].findAll('a')])
            if not len(text):
                text = elements[1].text
            table_map[elements[0].text.strip()] = text

   # print(str(table_map))

    if 'Genre' in table_map.keys():
        record.genre = table_map['Genre'].split("\n")[0]

    if 'Afleveringen' in table_map.keys():
        record.total_no_of_ep = table_map['Afleveringen'].split(" ")[0].strip()

    if 'Seizoenen' in table_map.keys():
        record.season = table_map['Seizoenen'].split(" ")[0]
       # print("Set Season: " + record.season)

    if 'Taal' in table_map.keys():
        record.broadcast_lang = table_map['Taal']

    if 'Start' in table_map.keys():  # Start or end??
        record.yop = extract_year_from_date(table_map['Start'])

    return True


def run():
    records = Nieuwsblad().get_records()
    for record in records:
        print("record: " + record.title)
        add_info(record)

    records_to_xml(records)


if __name__ == '__main__':
    run()






