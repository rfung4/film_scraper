import re
from typing import Optional
from urllib.parse import quote

from bs4 import BeautifulSoup

from core.abstract import Record, SeriesDetailRow, MovieRow
from util.util import make_soup

season_regex = re.compile('.*episodes?seasons=.*')
list_item_regex = re.compile('list_item')
ep_regex = re.compile('.*[0-9]+ ([Ee])pisode(s)*.*')
imdb_find_url = 'https://www.imdb.com/find?q='
imdb_base_url = 'https://www.imdb.com'

""" Utility methods for parsing IMDB pages """


def find_textblock_tag(soup, title):
    try:
        for block in soup.findAll('div', class_='txt-block'):
            try:
                if title.lower() in block.find('h4', class_='inline').text.strip().lower():
                    return block
            except Exception as e:
                continue
    except Exception as e:
        pass


def find_inline_tag(soup, title):
    try:
        for block in soup.findAll('div', class_='see-more inline canwrap'):
            try:
                if title.lower() in block.find('h4', class_='inline').text.strip().lower():
                    return block
            except Exception as e:
                continue
    except Exception as e:
        pass


def get_div_from_header(soup, header):
    for div in soup.find('div', class_='seasons-and-year-nav').findAll('div'):
        if header in div.find('h4'):
            return div


def title_to_search(title):
    return title.replace(' ', '_').replace("'", '%27')


def extract_year_from_date(raw):
    digits = ''.join([x for x in raw if x.isdigit() or x.isspace()])
    for digit in digits.split(" "):
        if len(digit) == 4:
            return digit
    return ''


def get_language_from_soup(soup: BeautifulSoup) -> str:
    return find_textblock_tag(soup, 'Language').find('a').text.strip()


def get_cast_list_string(soup) -> str:
    cast_table = soup.find('table', class_='cast_list')
    if not cast_table:
        return ''

    cast_box = cast_table.findAll('tr', class_=True)
    cast_list = [r.find('td', class_=False).text.strip().replace(",", '') for r in cast_box]
    cast_list = [x for x in cast_list if len(x)]
    return ', '.join(cast_list)


def get_year_of_production_from_soup(soup: BeautifulSoup):
    yop_tag = find_textblock_tag(soup, 'Release Date')
    return extract_year_from_date(yop_tag.text.strip())


""" Main functionality """


def get_page_url_from_title(title: str) -> str:
    search_query = quote(title)
    title = title.lower()
    soup = make_soup(imdb_find_url + search_query)

    if soup.find('div', class_='findNoResults') is not None:
        return ''

    s = None

    for search in soup.findAll('div', class_='findSection'):
        if 'Titles' in search.find('h3').text:
            s = search
            break

    if s:
        titles = [x for x in s.find('table').findAll('tr')]

        if titles:
            match = list(filter(
                lambda x: title in x.find('td', class_='result_text').find('a').text.strip().lower(),
                titles))

            if len(match):
                title = match[0]
                matching_url = imdb_base_url + title.find('a')['href'].split("?")[0]
                print("Parsing IMDB page: " + matching_url)
                return matching_url


def get_movie_row(title, cast=None) -> Optional[MovieRow]:

    matching_url = get_page_url_from_title(title)

    if not matching_url:
        return None

    soup = make_soup(matching_url)
    mr = MovieRow(title)

    try:
        mr.yop = get_year_of_production_from_soup(soup)
    except Exception as e:
        print("Failed to parse Year of Production from movie page (IMDB)")

    if not cast or not len(cast):
        try:
            mr.cast = get_cast_list_string(soup)
            print("Set cast: " + mr.cast)
        except Exception as e:
            print("Failed to parse cast from movie page (IMDB)")
    else:
        mr.cast = cast

    try:
        mr.language = get_language_from_soup(soup)
    except Exception as e:
        print("Failed to parse broadcast language from movie page")

    return mr


def get_summary_detail_row(title, episode, season) -> Optional[SeriesDetailRow]:
    record_url = get_page_url_from_title(title)
    if not record_url:
        return None

    ep_guide_url = record_url + f'episodes?season={season}'
    print("Season URL: " + ep_guide_url)

    try:
        season_soup = make_soup(ep_guide_url)
        if season_soup.find('a', text='TV Episodes submission guide') is not None:
            return None
    except Exception as e:
        return None

    try:
        if int(season) > len(season_soup.find('select', id='bySeason').findAll('option')):
            print(f"Season {season} of {title} not visible (IMDB)")
            return None
    except Exception as e:
        return None

    season_year = ''
s
    try:
        first_ep = season_soup.find('div', class_=list_item_regex)
        season_year = int(first_ep.find('div', class_='airdate').text.strip().split(" ")[-1])
    except Exception as e:
        pass

    ep_soup = None

    try:
        print("Searching " + ep_guide_url + " For season: " + season + " episode: " + episode)
        episode_list = season_soup.find('div', class_='list detail eplist').findAll('div', class_=list_item_regex)
        episode_box = episode_list[int(episode) - 1]
        ep_soup = make_soup(imdb_base_url + episode_box.find('a')['href'])
    except IndexError as e:
        print(f"Episode {episode} not visible for title {title} : {e}")
    except (TypeError, AttributeError) as e:
        print(f"Error adding info from IMDB for record with title: {title} for ep {episode} season {season} ")
        print("Exception: " + str(e))

    return get_series_summary_from_imdb_page_soup(ep_soup=ep_soup, episode=episode, season=season,
                                                  title=title, season_year=season_year)


def get_series_summary_from_imdb_page_soup(ep_soup, title, episode, season, season_year) -> SeriesDetailRow:

    s_row = SeriesDetailRow()
    s_row.title = title
    s_row.episode = episode
    s_row.season = season
    s_row.season_year = season_year

    try:
        title = ep_soup.find('div', class_='title_wrapper').find('h1').text.strip()
        print(f"Set Episode Title: {title} (summary)")
    except AttributeError as e:
        pass

    try:
        s_row.cast = get_cast_list_string(ep_soup)
        print(f'Set Episode Cast: {s_row.cast} (summary)')
    except AttributeError as e:
        pass

    try:
        s_row.yop = get_year_of_production_from_soup(ep_soup)
        print(f'Set Episode Air Date: {s_row.yop}')
    except AttributeError as e:
        pass

    try:
        s_row.language = get_language_from_soup(ep_soup)
        print(f'Set Broadcast Language : {s_row.language}')
    except AttributeError as e:
        pass

    return s_row


def add_schedule_info_to_record(record: Record, soup):

    if not len(record.yop):
        pass

    if not len(record.type):
        meta_type = soup.find('meta', property='og:type')['content'].split(".")[1]
        if meta_type == 'tv_show':
            record.type = 'series'
        elif meta_type == 'movie':
            record.type = 'film'

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
            #print("Set cop: " + record.cop)

    if not len(record.broadcast_lang):
        record.broadcast_lang = get_language_from_soup(soup)

    if not len(record.total_no_of_ep):
        raw_count_tag = soup.find('div', class_='button_panel navigation_panel')

        if raw_count_tag is not None:
            raw_count = raw_count_tag.find('span', text=ep_regex.match)
            if raw_count is not None:
                record.total_no_of_ep = raw_count.text.split(" ")[0].strip()

    if not len(record.season):
        year_nav = soup.find('div', class_='seasons-and-year-nav')

        if year_nav is not None:
            season_box = year_nav.findAll('a', href=season_regex.match)
            seasons = [x.text for x in season_box]
            seasons.sort(reverse=True)
            record.season = seasons[0] if len(seasons) else ''

    if not len(record.cast):
        record.cast = get_cast_list_string(soup)

    if not len(record.yop):
        record.yop = get_year_of_production_from_soup(soup)

    if not len(record.type):
        pass



