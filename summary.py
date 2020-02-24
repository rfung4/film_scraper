from os import listdir

import openpyxl
from xlsxwriter import Workbook

from core.abstract import SeriesSummaryRow, MovieRow
from definitions import CORE_PATH
from util.util import schedule_headers_map, movie_summary_headers, series_summary_headers, series_headers_map, alpha

from enrich import imdb as IMDB
from util.util import get_current_date_string


def get_year_from_workbook_name(wb_name):
    return int("".join(x for x in wb_name if x.isdigit()))


def generate_summary_worksheet_from_newest_schedule():

    books = [f for f in listdir(CORE_PATH) if 'schedule' in f]

    if not books:
        print("No schedule files to generate summary")
        return

    books.sort(key=get_year_from_workbook_name, reverse=True)

    print("Generating summary spreadsheet from : " + books[0])
    workbook = openpyxl.load_workbook(CORE_PATH + books[0])

    schedule_year = get_year_from_workbook_name(books[0])
    wb = Workbook(CORE_PATH + f'movies_series_summary_{schedule_year}_{get_current_date_string()}.xlsx')

    movie_rows = []
    series_summary_rows = []
    series_rows = []

    movie_sheet = wb.add_worksheet('movies')
    ss_sheet = wb.add_worksheet('series summary')
    s_sheet = wb.add_worksheet('series')

    is_headers_row = True

    for row in workbook.active.rows:
        if is_headers_row:
            is_headers_row = False
            continue

        movie_series_type = row[list(schedule_headers_map).index('type')].value
        title = row[list(schedule_headers_map.keys()).index('title')].value

        if movie_series_type == 'film':
            existing_movie_record = list(filter(lambda m: m.title == title, movie_rows))

            if not existing_movie_record:
                cast = row[list(schedule_headers_map).index('cast')].value
                mr = IMDB.get_movie_row(title=title, cast=cast)

                if mr:
                    movie_rows.append(mr)
            else:
                print("Existing movie record for title: " + title)

        elif movie_series_type == 'series':
            ep_number = row[list(schedule_headers_map.keys()).index('episode')].value
            season = row[list(schedule_headers_map.keys()).index('season')].value
            series_detail_row = IMDB.get_summary_detail_row(title=title, episode=ep_number, season=season)

            if series_detail_row:
                series_rows.append(series_detail_row)
                series_row = list(filter(lambda r: r.title == title and r.season == season, series_summary_rows))

                if series_row:   # Row with the season and title already exists
                    series_row[0].increment_count()  # Increment number of episodes for this season
                else:
                    print("Created new Summary Row for : " + title)
                    sr = SeriesSummaryRow(title=title, type='series', season=season, season_year=series_detail_row.season_year)
                    series_summary_rows.append(sr)

    series_rows.sort(key=lambda m: m.title)
    movie_rows.sort(key=lambda m: m.title)
    series_summary_rows.sort(key=lambda m: m.title)

    for c, h in enumerate(series_headers_map.keys()):   # Write headers to series sheet
        s_sheet.write(alpha[c] + str(1), series_headers_map[h])

    for row, series_row in enumerate(series_rows):
        for i, field_name in enumerate(series_headers_map.keys()):
            s_sheet.write(alpha[i] + str(row+2), getattr(series_row, field_name))

    for c, h in enumerate(vars(SeriesSummaryRow('', '', '')).keys()):   # Write headers series summary sheet
        ss_sheet.write(alpha[c] + str(1), series_summary_headers[h])

    for row, series_row in enumerate(series_summary_rows):
        for i, field_name in enumerate(vars(series_row).keys()):  # Get attribute of SummaryRow object
            ss_sheet.write(alpha[i] + str(row + 2), getattr(series_row, field_name))

    for c, h in enumerate(vars(MovieRow()).keys()):   # Write headers series summary sheet
        movie_sheet.write(alpha[c] + str(1), movie_summary_headers[h])

    for row, movie_row in enumerate(movie_rows):
        for i, field_name in enumerate(vars(movie_row).keys()):  # Get attribute of MovieRow object
            movie_sheet.write(alpha[i] + str(row + 2), getattr(movie_row, field_name))

    print("\n\nExecution complete, exiting..\n\n")
    wb.close()


if __name__ == '__main__':
    generate_summary_worksheet_from_newest_schedule()
