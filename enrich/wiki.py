from urllib.error import URLError

from bs4 import BeautifulSoup

from core.abstract import Record
from util.util import make_soup

en_wiki_base = 'https://en.wikipedia.org/wiki/'
nl_wiki_base = 'https://nl.wikipedia.org/wiki/'

en_wiki_search = 'https://en.wikipedia.org/w/index.php?sort=relevance&search='
nl_wiki_search = 'https://nl.wikipedia.org/w/index.php?search='


def add_en_info(record) -> bool:
    try:
        url = en_wiki_base + title_to_search(str(record.title))
        soup = make_soup(url)

        if soup is not None:
            parsed = parse_wiki_page_en(record, soup)
            if parsed:
                print(f"Added schedule info from (EN Wiki) : {url}  ")
            return parsed
    except URLError as e:
        print("No matching EN wiki page")


def add_nl_info(record) -> bool:
    try:
        url = nl_wiki_base + title_to_search(record.title)
        parsed = parse_wiki_page_nl(record, make_soup(url))
        if parsed:
            print(f"Added schedule info from (NL Wiki) : {url}  ")
        return parsed
    except URLError as e:
        print("No matching NL wiki page")


def title_to_search(title):
    return title.replace(' ', '_').replace("'", '%27')


def get_soup_from_wiki_search(record: Record, search_url: str) -> BeautifulSoup:
    search_soup = make_soup(search_url)

    if 'search=' not in search_url:
        return search_soup

    results = search_soup.findAll('li', class_='mw-search-result')
    for result in results:
        if record.title.lower() in result.find('a').text.lower():
            url = en_wiki_base if 'en.' in search_url else nl_wiki_base
            url += result.find('a')['href']
            return make_soup(url)


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

    if 'No. of episodes' in table_map.keys() or 'No. of seasons' in table_map.keys():
        record.type = 'series'

    if 'Genre' in table_map.keys():
        record.genre = table_map['Genre'].split("\n")[0]

    if 'Country of origin' in table_map.keys():
        record.cop = table_map['Country of origin']

    if 'Original language(s)' in table_map.keys():
        record.broadcast_lang = table_map['Original language(s)']

    if 'No. of episodes' in table_map.keys() and not len(record.episode):
        record.total_no_of_ep = parse_ep_count(table_map['No. of episodes'])

    if 'No. of seasons' in table_map.keys() and not len(record.seasons):
        record.seasons = parse_ep_count(table_map['No. of seasons']).split(" ")[0]

    if 'Original release' in table_map.keys():
        record.yop = extract_year_from_date(table_map['Original release'])

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

    if 'Afleveringen' in table_map.keys() or 'Seizoenen' in table_map.keys():
        record.type = 'series'

    if 'Genre' in table_map.keys():
        record.genre = table_map['Genre'].split("\n")[0]

    if 'Afleveringen' in table_map.keys() and not len(record.total_no_of_ep):
        record.total_no_of_ep = table_map['Afleveringen'].split(" ")[0].strip()

    if 'Seizoenen' in table_map.keys() and not len(record.seasons):
        record.seasons = table_map['Seizoenen'].split(" ")[0]

    if 'Taal' in table_map.keys():
        record.broadcast_lang = table_map['Taal']

    if 'Start' in table_map.keys():  # Start or end??
        record.yop = extract_year_from_date(table_map['Start'])

    return True


def extract_year_from_date(raw):
    digits = ''.join([x for x in raw if x.isdigit() or x.isspace()])
    for digit in digits.split(" "):
        if len(digit) == 4:
            return digit
    return ''


def parse_ep_count(raw):
    digits = ' '.join([x for x in raw.replace(",", '') if x.isdigit() or x.isspace()])
    return max(digits.split(" ")) if len(digits) > 0 else ''
