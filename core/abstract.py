class Record:
    def __init__(self):
        self.title = self.date = self.channel = self.start_time = self.stop_time \
            = self.original_title = self.yop = self.seasons = self.season = self.total_no_of_ep = self.cop = self.genre\
            = self.subgenre = self.broadcast_lang = self.type = self.id = self.cast = self.episode = ''


class ScheduleWebsite:
    def get_records(self) -> [Record]:
        pass


class SeriesDetailRow:
    def __init__(self):
        self.ep_title = self.series_title = self.language = self.cast = self.yop = ''
        self.season_year = ''  ##
        self.type = 'series'


class MovieRow:
    def __init__(self, title=None):
        self.title = title
        self.yop = self.cast = self.language = ''
        self.type = 'film'


class SeriesSummaryRow:

    def __init__(self, title, type, season, season_year=None):
        self.title = title
        self.type = type
        self.season = season
        self.count = 1
        self.season_year = season_year

    def increment_count(self):
        self.count += 1


class EnrichWebsite:

    def add_listing_info(self, record: Record) -> None:
        pass

    def add_summary_info(self, record: Record) -> None:
        pass


