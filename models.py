from __future__ import annotations

import os
import re
import time
from functools import cached_property
from typing import List, Optional

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement

import exceptions
import safe_download


class BaseArchivedWebPage:
    API_URL = "https://archive.org/wayback/available"

    class Snapshot:
        def __init__(self, data: dict):
            self.status: int = data.pop('status')
            self.available: bool = data.pop('available')
            self.url: str = data.pop('url')
            self.timestamp: int = data.pop('timestamp')

        def download(self, directory: str, file_name: str, overwrite: bool = False):
            file_name = safe_download.get_valid_filename(file_name)

            path = os.path.join(directory, file_name)
            if os.path.exists(path) and overwrite is False:
                raise exceptions.AlreadyDownloaded(f"{path} seems to be already downloaded.")

            safe_download.safe_download_url(self.url, path)

    def __init__(self, url: str):
        self.url: str = url
        self._archived_snapshots = None

    def _cache(self):
        self._archived_snapshots = requests.get(self.API_URL, params={'url': self.url}).json()["archived_snapshots"]

    def cache_if_not_cached(self):
        if self._archived_snapshots is None:
            self._cache()

        if not self.is_archived:
            # sometimes internet archive gives different results between http and https, so try again
            self.url = 'https' + self.url[4:]
            self._cache()

        if not self.is_archived:
            raise exceptions.NotArchived(f"URL is not cached: {self.url}")

    @property
    def is_archived(self) -> bool:
        return bool(self._archived_snapshots)

    @cached_property
    def snapshot(self) -> Optional[Snapshot]:
        self.cache_if_not_cached()
        return BaseArchivedWebPage.Snapshot(self._archived_snapshots['closest'])

    def download_latest_snapshot(self, directory: str, file_name: str, overwrite=False):
        self.snapshot.download(directory, file_name, overwrite)


class ArchivedPlaysTVBrowser(BaseArchivedWebPage):
    def __init__(self, user_name: str):
        self.username = user_name
        self.browser = None

        super(ArchivedPlaysTVBrowser, self).__init__(url=f"http://plays.tv/u/{self.username}")

    def close(self):
        try:
            self.browser.close()
        except NoSuchWindowException:
            pass
        
    def launch_the_browser(self):
        options = Options()
        # options.add_argument('headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.browser = webdriver.Chrome(options=options)
        self.browser.get(self.snapshot.url)

    @property
    def total_video_count(self) -> int:
        return int(
            self.browser.find_element_by_class_name('header-btn').find_element_by_class_name(
                'section-value').text)

    @property
    def author_video_count(self) -> int:
        """Midorina's Videos (148) -> 148"""
        label: str = self.browser.find_element_by_class_name('nav-tab-label').text
        se = re.search("\(([^)]*)\)", label)
        return int(se.group(0)[1:-1])

    @property
    def featured_video_count(self) -> int:
        return self.total_video_count - self.author_video_count

    def scroll_down_until_all_videos_are_visible(self):
        elem = self.browser.find_element_by_tag_name("body")
        i = 0
        while True:
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)
            i += 1
            # scan at every 10 page down press
            if i % 10 == 0:
                if len(self.get_all_visible_videos()) == self.author_video_count:
                    return

    def get_all_visible_videos(self) -> List[ArchivedVideo]:
        ret = []

        containers = self.browser.find_elements_by_class_name("video-list-container")
        for container in containers:
            date_str = container.find_element_by_class_name('video-list-month').text

            video_elements: List[WebElement] = container.find_elements_by_class_name("video-item")
            ret.extend(list(map(lambda x: ArchivedVideo(x, date_str, self.username), video_elements)))

        return ret


class ArchivedVideo(BaseArchivedWebPage):
    QUALITIES = [
        1080,
        720,
        480
    ]

    def __init__(self, web_obj: WebElement, date_str: str, author_str: str, quality: int = 720):
        self.web_element = web_obj
        self.author = author_str
        self.date_str = date_str
        self.quality = quality

        super(ArchivedVideo, self).__init__(self.mp4_url)

    @cached_property
    def title(self) -> str:
        return self.web_element.find_element_by_class_name('title').text

    @cached_property
    def poster_link(self) -> str:
        return self.web_element.find_element_by_class_name('video-tag').get_attribute('poster')

    @cached_property
    def id(self) -> str:
        return self.poster_link.split('/')[-3]

    @property
    def mp4_url(self):
        return '/'.join(self.poster_link.split('/')[:-1]) + f'/{self.quality}.mp4'

    def __repr__(self):
        return f'{self.title}_{self.date_str}_{self.author}_{self.id}_{self.quality}.mp4'

    def download(self, directory: str, overwrite=False):
        self.download_latest_snapshot(directory=directory, file_name=self.__repr__(), overwrite=overwrite)

    def attempt_to_download_highest_quality(self, directory: str, overwrite=False):
        for quality in self.QUALITIES:
            if quality == self.quality:
                vid = self
            else:
                vid = ArchivedVideo(web_obj=self.web_element, date_str=self.date_str, author_str=self.author,
                                    quality=quality)

            try:
                vid.download(directory, overwrite)
            except exceptions.NotArchived:
                continue
            else:
                return

        raise exceptions.NotArchived(f"Video is not archived: {self.title}")
