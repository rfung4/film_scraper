class Record:
    def __init__(self):
        self.title = self.date = self.channel = self.start_time = self.stop_time \
            = self.original_title = self.yop = self.season = self.total_no_of_ep = self.cop = self.genre = self.subgenre \
            = self.broadcast_lang = self.series = self.id = self.cast = ''


class ScheduleWebsite:

    def __init__(self):
        self.channel_ids = set() # Unique set of IDs for each website

    def get_records(self) -> [Record]:
        pass

