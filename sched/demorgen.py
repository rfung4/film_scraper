import os
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from core.abstract import ScheduleWebsite, Record
from util.util import print_record_sched


class demo(ScheduleWebsite):

    base_url = 'https://www.demorgen.be/'
    main_url = 'https://www.demorgen.be/tv-gids/morgen'
    channels = ('Caz', 'Club RTL', 'La Deux', 'La Une', 'ZES', 'Vitaya', 'Ketnet', 'Vijf', 'Q2', 'Vier', 'VTM', 'Canvas')

    def __init__(self):
        super().__init__()
        self.driver = demo.create_web_driver()

    @staticmethod
    def create_web_driver():
        chrome_driver_path = os.path.dirname(os.path.abspath(__file__)) + "/chromedriver.exe"
        chrome_options = Options()
        ##chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(executable_path=chrome_driver_path, chrome_options=chrome_options)
        driver.set_window_size(1920, 1080)
        return driver

    def get_records(self) -> [Record]:
        c_records = self.get_core_records()

        for record in c_records:
            self.driver.get(record.sched_page_url)

            try:
                record.date = self.driver.find_element_by_css_selector('time').get_attribute('datetime').split("T")[0]
            except NoSuchElementException as e:
                print("No locatable record date")
            
            try:
                ep_season_txt = self.driver.find_element_by_css_selector(
                    "span[class='tvgm-broadcast-detail__episode-numbers']").text.strip().split(" ")
                record.season = ep_season_txt[1]    # TODO: Check if 'season' text is a year (regex)
                record.episode = ep_season_txt[-1].split("/")[0]
                print(f'Set record season: {record.season} & Episode: {record.episode} for {record.sched_page_url}')
            except NoSuchElementException as e:
                print("Failed to locate record season/episode")

            try:
                record.cast = self.driver.find_element_by_css_selector(
                    "p[class='tvgm-broadcast-detail__castandcrew']").text.strip()
            except Exception as e:
                print("Failed to locate record cast")

            print_record_sched(record)

        self.driver.close()
        return c_records

    def get_core_records(self) -> [Record]:
        records = []
        self.driver.get(self.main_url)
        current_index = 3  # Previous values are Yesterday & The day before

        try:
            accept_button = self.driver.find_element_by_css_selector("button[class='button fjs-set-consent']")
            accept_button.click()
        except NoSuchElementException as e:
            pass    # No splash screen present

        for index in range(0, 6):
            full_channels = [x for x in self.channels]
            prev_button = None

            try:
                prev_button = self.driver.find_element_by_css_selector("button[class='tvgm-pager__nav tvgm-pager__nav--prev ']")
            except NoSuchElementException:
                print("No previous button locatable")

            sleep(5)

            if prev_button:
                try:
                    cat_list_div = self.driver.find_element_by_css_selector(
                        "div[class='tvgm-controls__group tvgm-controls__group--channel']")

                    cat_list = cat_list_div.find_element_by_css_selector('ul')

                    self.driver.execute_script("arguments[0].click();", cat_list)  # Select channel dropdown list
                    self.driver.execute_script("arguments[0].click();", cat_list.find_elements_by_css_selector('li')[
                        6])  # Select first required channel
                except RecursionError as e:
                    print("Failed to select channels")

            nxt_button = None

            try:
                nxt_button = self.driver.find_element_by_css_selector(
                    "button[class='tvgm-pager__nav tvgm-pager__nav--next ']")
            except NoSuchElementException as e:
                print("Error finding next button, sleeping 10 seconds")
                sleep(10)

                try:
                    nxt_button = self.driver.find_element_by_css_selector(
                        "button[class='tvgm-pager__nav tvgm-pager__nav--next ']")
                except Exception as e:
                    pass

            while nxt_button and len(full_channels):
                chan_bar = self.driver.find_element_by_css_selector("li[class='tvgm-ribbon__slide tvgm-ribbon__slide--active']")
                visible_chan = [x.find_element_by_css_selector('img').get_attribute('alt') for x in chan_bar.find_elements_by_css_selector('a')]
                lanes = self.driver.find_elements_by_css_selector("div[class='tvgm-lanes__child']")

                for chan in visible_chan:
                    if chan in full_channels:
                        lane = lanes[visible_chan.index(chan)]
                        articles = lane.find_elements_by_css_selector('article')

                        for article in articles:

                            record = Record()
                            record.start_time = article.find_element_by_css_selector("a[class='tvgm-broadcast-teaser__link']").text.strip().replace("TIP", '')
                            record.title = article.find_element_by_css_selector("h1[class='tvgm-broadcast-teaser__title']").text.strip()
                            record.sched_page_url = article.find_element_by_css_selector("a[class='tvgm-broadcast-teaser__link']").get_attribute('href')
                            record.channel = chan

                            if articles.index(article) != len(articles)-1:  # Last article
                                record.stop_time = articles[articles.index(article)+1].find_element_by_css_selector("a[class='tvgm-broadcast-teaser__link']").text.strip().replace("TIP", '')
                            records.append(record)

                        full_channels.remove(chan)

                try:
                    nxt_button = self.driver.find_element_by_css_selector(
                        "button[class='tvgm-pager__nav tvgm-pager__nav--next ']")
                    nxt_button.click()
                    sleep(3)
                except NoSuchElementException as e:
                    print("At final relevant page, going to next day.")
                    break

            day_list = self.driver.find_element_by_css_selector("ul[class='tvgm-dropdown__options']")
            self.driver.execute_script("arguments[0].click();", day_list)
            current_index += 1
            days = day_list.find_elements_by_css_selector('li')
            self.driver.execute_script("arguments[0].click();", days[current_index])
            sleep(2)

        return records


if __name__ == '__main__':
    d = demo()
    d.get_records()







