import json
import logging
from time import sleep
import re
import cloudscraper
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Comment
from cloudscraper import CloudScraper
from utils.database import SQLiteMixin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s: %(message)s")

URLs = {
    "BASE_URL": "https://www.thepaperboy.com/",
    "COUNTRY_LIST": "/newspapers-by-country.cfm",
    "US_STATES_LIST": "/usa-newspapers-by-state.cfm"
}

DELAY = 10
MAX_RETRIES = 3
DATABASE_PATH = "output/database/thepaperboy.db"


class ThePaperBoyScraper(SQLiteMixin):
    def __init__(self):
        self.db = None
        self.base_url: str = URLs.get("BASE_URL")
        self.DATABASE_PATH = DATABASE_PATH
        self.scraper: CloudScraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})
        self.initialize_database()
        logger.info("Scraper is initialized with base URL %s", self.base_url)

    def initialize_database(self):
        self.db = self._get_connection()
        self.create_table('countries', {
            'id': 'INTEGER PRIMARY KEY',
            'name': 'TEXT NOT NULL',
            'url': 'TEXT NOT NULL UNIQUE',
            'crawl_status': 'TEXT CHECK (crawl_status IN ("pending", "in_progress", "completed")) DEFAULT "pending"',
            'start_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'finish_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'total': 'INTEGER DEFAULT NULL',
            'last_crawl_time': 'TIMESTAMP DEFAULT NULL'
        })

        self.create_table('states', {
            'id': 'INTEGER PRIMARY KEY',
            'name': 'TEXT NOT NULL',
            'abbreviation': 'TEXT NOT NULL',
            'url': 'TEXT NOT NULL UNIQUE',
            'crawl_status': 'TEXT CHECK (crawl_status IN ("pending", "in_progress", "completed")) DEFAULT "pending"',
            'start_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'finish_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'total': 'INTEGER DEFAULT NULL',
            'last_crawl_time': 'TIMESTAMP DEFAULT NULL'
        })

        self.create_table('sources', {
            'id': 'INTEGER PRIMARY KEY',
            'url': 'TEXT NOT NULL UNIQUE',
            'data': 'TEXT NOT NULL UNIQUE',
            'crawl_status': 'TEXT CHECK (crawl_status IN ("pending", "in_progress", "completed")) DEFAULT "pending"',
            'start_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'finish_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'last_crawl_time': 'TIMESTAMP DEFAULT NULL'
        })

    def scrape_content_with_retry(self, method, *args, **kwargs):
        """
        A method to for scraping content with exponential backoff.

        Args:
            method (callable): The method to execute.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            Any: The return value of the method, or None if retries fail.
        """
        number_of_retries = 0
        while number_of_retries < MAX_RETRIES:
            try:
                result = method(*args, **kwargs)
                if result:
                    return result
            except Exception as e:
                logging.info(f"Error during execution: {e}")
            number_of_retries += 1
            delay = DELAY * number_of_retries
            logging.info("Retry [%s/%s]. Waiting %s seconds...", number_of_retries, MAX_RETRIES, delay)
            sleep(delay)
        logging.error("Max retries reached. Method execution failed.")
        return None

    def __scrape_locations(self, level):
        if level == "states":
            url = URLs.get("US_STATES_LIST")
            entry_point = "START MAIN LEFT COLUMN TABLE"
        else:
            url = URLs.get("COUNTRY_LIST")
            entry_point = "START MAIN COLUMN TABLE"

        total_records = self.count(level)

        if total_records == 0:
            data = []
            response = self.scraper.get(urljoin(self.base_url, url))
            soup = BeautifulSoup(response.text, features="lxml")
            comments = soup.find_all(string=lambda node: isinstance(node, Comment))
            for comment in comments:
                if entry_point in comment:
                    main_table = comment.find_next()
                    tables = main_table.find_all("table")
                    for table in tables:
                        rows = table.find_all("tr")
                        for row in rows:
                            anchors = row.find_all("a")
                            for anchor in anchors:
                                href = anchor.get("href")
                                text = anchor.get_text(strip=True)
                                if text != "(FP)":
                                    if level == "countries":
                                        location, total = self.extract_location_totals(text, level)
                                        if location and total:
                                            logger.info("Found: href=%s, location=%s, total=%s",
                                                        href, location, total)
                                            data.append({
                                                "name": location,
                                                "url": href,
                                                "total": total
                                            })
                                    elif level == "states":
                                        location, abbreviation, total = self.extract_location_totals(text, level)
                                        data.append({
                                            "name": location,
                                            "abbreviation": abbreviation,
                                            "url": href,
                                            "total": total
                                        })
                    break
            logger.info("Recording [%s] %s", len(data), level)
            self.bulk_insert(level, data, "IGNORE")
        else:
            logger.info("%s already set in database, no further processing is required", level)

        return True

    def __scrape_sources_from_specific_location(self, data):
        response = self.scraper.get(urljoin(self.base_url, data.get("url")))
        fetched_data = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features="lxml")
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                if "START MAIN PAPER DISPLAY TABLE" in comment:
                    main_table = comment.find_next()
                    if data.get("country") == "United States":
                        no_columns = 3
                    else:
                        no_columns = 4
                    rows = main_table.find_all("tr")[1:]
                    for index, row in enumerate(rows, start=1):
                        cells = row.find_all("td")
                        if len(cells) == no_columns:
                            source_link_tag = cells[0].find("a")
                            name = source_link_tag.get_text(strip=True)
                            url = source_link_tag['href']

                            # Local sources (USA) have 3 columns, other sources have 4 columns
                            if no_columns == 4:
                                city = cells[1].find("a", href=True).get_text()
                                state = cells[2].find("a", href=True).get_text()
                                language = cells[3].find("font", class_="smallfont").get_text()
                                country = data.get("name")
                            else:
                                state = data.get("state")
                                city = cells[1].find("a", href=True).get_text()
                                language = cells[2].find("font", class_="smallfont").get_text()
                                country = data.get("country")

                            fetched_data.append({"url": url, "data": json.dumps({
                                "state": state,
                                "country": country,
                                "url": url,
                                "city": city,
                                "language": language,
                                "name": name
                            })})

            logger.info("Recording [%s] sources", len(fetched_data))
            self.bulk_insert("sources", fetched_data, "IGNORE")
            return fetched_data

    def __scrape_source_metadata(self, data):
        if data.get("url"):
            response = self.scraper.get(urljoin(self.base_url, data.get("url")))
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, features="lxml")
                # Get the link to the actual source website
                source_final_link = soup.find("h1").find("a")
                if source_final_link:
                    data["url"] = source_final_link.get('href')

                # Get the description of the source (this is mostly present for USA sources)
                pre_formatted_text = soup.find("pre")
                if pre_formatted_text:
                    data["description"] = pre_formatted_text.text.strip()

                # Get social details
                comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    if "SHOW SOCIAL ICONS AVAILABLE" in comment:
                        data["social_media"] = []
                        social_tags_container = comment.find_next()
                        if social_tags_container:
                            social_tags = social_tags_container.find_all('a', target="_blank")
                            for social_tag in social_tags:
                                data["social_media"].append(self.extract_social_media_tag_info(social_tag))
                        break
        return data

    def scrape_non_us_sources(self):
        countries = self.select("countries",
                                where="finish_crawl_time IS NULL AND name <> ?",
                                params=("United States",)
                                )
        if len(countries) > 0:
            for location in countries:
                self.update("countries", {"start_crawl_time": "CURRENT_TIMESTAMP",
                                          "crawl_status": "in_progress"}, "id = ?",
                            (location.get("id"),))
                logging.info("Starting to scrape sources from: %s", location.get("name"))
                location["level"] = "country"
                if self.scrape_sources_from_specific_location(location):
                    logger.info("Completed scraping sources from %s",location.get("name"))
                self.update("countries", {"finish_crawl_time": "CURRENT_TIMESTAMP",
                                          "crawl_status": "completed"}, "id = ?",
                            (location.get("id"),))
                logging.info("Crawl delay. Waiting for %s seconds...", DELAY)
                sleep(DELAY)
        else:
            logger.info("Sources for all countries have been to be scraped, exiting...")



        # Grab metadata from the scraped table of sources
        """countries = self.select("sources",
                                where="finish_crawl_time IS NULL AND name <> ?",
                                params=("United States",)
                                )
        """

    def scrape_us_sources(self):
        states = self.select("states", where="finish_crawl_time IS NULL")
        if len(states) > 0:
            for location in states:
                self.update("states", {"start_crawl_time": "CURRENT_TIMESTAMP",
                                          "crawl_status": "in_progress"}, "id = ?",
                            (location.get("id"),))
                logging.info("Starting to scrape sources from: %s", location.get("name"))
                location["level"] = "state"
                location["country"] = "United States"
                if self.scrape_sources_from_specific_location(location):
                    logger.info("Completed scraping sources from %s",location.get("name"))
                self.update("states", {"finish_crawl_time": "CURRENT_TIMESTAMP",
                                          "crawl_status": "completed"}, "id = ?",
                            (location.get("id"),))
                logging.info("Crawl delay. Waiting for %s seconds...", DELAY)
                sleep(DELAY)
        else:
            logger.info("Sources for all states have been to be scraped, exiting...")



        # Grab metadata from the scraped table of sources
        """countries = self.select("sources",
                                where="finish_crawl_time IS NULL AND name <> ?",
                                params=("United States",)
                                )
        """

    def scrape_source_metadata_with_retry(self, data):
        return self.scrape_content_with_retry(self.__scrape_source_metadata, data)

    def scrape_sources_from_specific_location(self, data):
        return self.scrape_content_with_retry(self.__scrape_sources_from_specific_location, data)

    def scrape_countries(self):
        return self.scrape_content_with_retry(self.__scrape_locations, "countries")

    def scrape_states(self):
        return self.scrape_content_with_retry(self.__scrape_locations, "states")

    @staticmethod
    def extract_location_totals(text: str, type: str):
        if type == "countries":
            pattern = r"(.*?)\s*\((\d+)\)"
            match = re.search(pattern, text)
            if match:
                country = match.group(1).strip()
                total = int(match.group(2))
                return country, total
        elif type == "states":
            pattern = r"(.*?)\[(.*?)\]\((\d+)\)"
            match = re.search(pattern, text)
            if match:
                state_name = match.group(1).strip()
                state_abbrev = match.group(2)
                total = int(match.group(3))
                return state_name, state_abbrev, total
        return None, None

    @staticmethod
    def extract_social_media_tag_info(social_media_anchor_tag):
        social_media_info = {}
        url = social_media_anchor_tag.get("href")
        if "wikipedia" in url:
            social_media_info["Wikipedia"] = url
        elif "facebook" in url:
            social_media_info["Facebook"] = url
        elif "twitter" in url:
            social_media_info["Twitter"] = url
        return social_media_info

    def main(self):
        self.scrape_states()
        self.scrape_countries()
        self.scrape_non_us_sources()
        self.scrape_us_sources()



if __name__ == "__main__":
    scraper = ThePaperBoyScraper()
    scraper.main()
