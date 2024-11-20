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
    "US_LIST": "/usa-newspapers-by-state.cfm"
}

DELAY = 10
MAX_RETRIES = 3


class ThePaperBoyScraper(SQLiteMixin):
    def __init__(self):
        self.db = None
        self.base_url: str = URLs.get("BASE_URL")
        self.DATABASE_PATH = "output/database/thepaperboy.db"
        self.scraper: CloudScraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})
        self.initialize_database()
        logger.info("Scraper is initialized with base URL [%s]", self.base_url)



    def initialize_database(self):
        self.db = self._get_connection()
        self.create_table('countries',{
            'id': 'INTEGER PRIMARY KEY',
            'name': 'TEXT NOT NULL',
            'url': 'TEXT NOT NULL UNIQUE',
            'crawl_status': 'TEXT CHECK (crawl_status IN ("pending", "in_progress", "completed")) DEFAULT "pending"',
            'start_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'finish_crawl_time': 'TIMESTAMP DEFAULT NULL',
            'total': 'INTEGER DEFAULT NULL',
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

    def __scrape_countries(self):
        countries_data = []
        response = self.scraper.get(urljoin(self.base_url, URLs.get("COUNTRY_LIST")))
        soup = BeautifulSoup(response.text, features="lxml")
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if "START MAIN COLUMN TABLE" in comment:
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
                                country, total = self.extract_country_totals(text)
                                if country and total:
                                    logger.info("Found: href=%s, country=%s, total=%s",
                                                href, country, total)
                                    countries_data.append({
                                        "name": country,
                                        "url": href,
                                        "total": total
                                    })
                break

        total_records = self.count('countries')
        if total_records == 0:
            self.bulk_insert('countries', countries_data)
        else:
            logger.info("Countries already set in database, no further processing is required")
        return countries_data

    def __scrape_sources_from_specific_location(self, data):
        response = self.scraper.get(urljoin(self.base_url, data.get("url")))
        fetched_data = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features="lxml")
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                if "START MAIN PAPER DISPLAY TABLE" in comment:
                    main_table = comment.find_next()
                    rows = main_table.find_all("tr")[1:]
                    for index, row in enumerate(rows, start=1):
                        cells = row.find_all("td")
                        if len(cells) == 3:
                            source_link_tag = cells[0].find("a")
                            name = source_link_tag.get_text(strip=True)
                            url = source_link_tag['href']
                            city = cells[1].find("a", href=True).get_text()
                            language = cells[2].find("font", class_="smallfont").get_text()
                            updated_data = self.scrape_source_metadata_with_retry({
                                "state": data.get("state"),
                                "country": data.get("country"),
                                "url": url,
                                "city": city,
                                "language": language,
                                "name": name
                            })
                            fetched_data.append(updated_data)
                            logger.info("Fetched source %s - %s ", index, name)
                            sleep(DELAY)
            return fetched_data

    def __scrape_source_metadata(self, data):
        if data.get("url"):
            response = self.scraper.get(urljoin(self.base_url, data.get("url")))
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, features="lxml")
                # Get the link to the actual source website
                source_final_link = soup.find("h1").find("a")
                if source_final_link:
                    has_found_content = True
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

    def __scrape_non_us_sources(self, countries):
        for country in countries:
            if country.get("name") == "Tanzania":
                print(country)

    def scrape_source_metadata_with_retry(self, data):
        return self.scrape_content_with_retry(self.__scrape_source_metadata, data)

    def scrape_source_from_specific_location_with_retry(self, data):
        return self.scrape_content_with_retry(self.__scrape_sources_from_specific_location, data)

    def scrape_countries_with_retry(self):
        return self.scrape_content_with_retry(self.__scrape_countries)

    @staticmethod
    def extract_country_totals(text):
        pattern = r"(.*?)\s*\((\d+)\)"
        match = re.search(pattern, text)
        if match:
            country = match.group(1).strip()
            total = int(match.group(2))
            return country, total
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
        self.scrape_countries_with_retry()
        pass






if __name__ == "__main__":
    scraper = ThePaperBoyScraper()
    scraper.main()

