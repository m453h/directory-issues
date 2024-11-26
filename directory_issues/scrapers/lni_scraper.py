import json
import logging
import os
from time import sleep

from utils.database import SQLiteMixin
from utils.scraper import BaseScraper
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s: %(message)s")

URLs = {
    "BASE_URL": "https://www.northwesternlni.com:8068/",
    "SEARCH_ENGINE_URL": "https://duckduckgo.com/html",
    "SOURCES_LIST": "lni/localnewstable?year=2024"
}

DATABASE_PATH = "output/database/lni.db"
JSON_DUMP_PATH = "output/files"


class LocalNewsInitiativeScraper(SQLiteMixin, BaseScraper):
    def __init__(self):
        super().__init__()
        self.db = None
        self.base_url: str = URLs.get("BASE_URL")
        self.DATABASE_PATH = DATABASE_PATH
        self.initialize_database()
        logger.info("Scraper is initialized with base URL %s", self.base_url)

    def initialize_database(self):
        self.db = self._get_connection()
        self.create_table('sources', {
            'id': 'INTEGER PRIMARY KEY',
            'state': 'TEXT',
            'county': 'TEXT',
            'media_name': 'TEXT',
            'media_type': 'TEXT',
            'year_loaded': 'TEXT',
            'fips': 'TEXT',
            'url': 'TEXT'
        })

    def fetch_sources(self):
        response = self.scraper.get(urljoin(self.base_url, URLs.get("SOURCES_LIST")))
        sources = response.json()

        for source in sources:
            logging.info(f"Recording source {source.get('id')} - {source.get('mediaName')}")
            self.insert("sources", {
                "state": source.get("state"),
                "county": source.get("county"),
                "media_name": source.get("mediaName"),
                "media_type": source.get("mediaType"),
                "year_loaded": source.get("yearLoaded"),
                "fips": source.get("fips"),
            })

    def fetch_source_url(self, query):
        try:
            params = {"q": quote(query)}
            response = self.scraper.get(URLs.get("SEARCH_ENGINE_URL"), params=params)
            soup = BeautifulSoup(response.text, features="lxml")
            first_result_div = soup.find('div', class_='result')
            if first_result_div:
                extras_url_div = first_result_div.find('div', class_='result__extras__url')
                if extras_url_div:
                    link = extras_url_div.find('a', class_='result__url')
                    if link:
                        return link.text.strip()
        except Exception as e:
            logger.exception(e)

        return None

    def fetch_source_metadata(self):
        sources = self.select("sources", where="url IS NULL")
        if len(sources) > 0:
            for source in sources:
                search_string = f"{source.get('media_name')} {source.get('state')} {source.get('county')}"
                logging.info("Attempting to fetch url for: %s - %s", source.get("id"), search_string)
                source_url = self.fetch_source_url(search_string)
                if source_url:
                    logger.info("Completed fetching URL from %s", search_string)
                    self.update("sources", {"url": source_url, }, "id = ?",
                                (source.get("id"),))
                else:
                    raise Exception("No URL fetched, possibly blocked")
                logging.info("Crawl delay. Waiting for %s seconds...", self.crawl_delay)
                sleep(self.crawl_delay)
        else:
            logger.info("All sources have been updated, exiting...")


    def export_sources_to_file(self):
        sources = self.select("sources")
        data = []

        for source in sources:
            data.append(source)
        os.makedirs(JSON_DUMP_PATH, exist_ok=True)

        with open(f"{JSON_DUMP_PATH}/lni_sources.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info("Data has been written to file")


    def main(self):
        super().main()
        if self.data_to_scrape == "sources":
            self.fetch_sources()
        elif self.data_to_scrape == "metadata":
            self.fetch_source_metadata()
        elif self.data_to_scrape == "export":
            self.export_sources_to_file()


if __name__ == "__main__":
    scraper = LocalNewsInitiativeScraper()
    scraper.main()
