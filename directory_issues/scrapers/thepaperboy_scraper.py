import logging
from time import sleep
import re
import cloudscraper
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s: %(message)s")

URLs = {
    "COUNTRY_LIST": "/newspapers-by-country.cfm",
    "US_LIST": "/usa-newspapers-by-state.cfm"
}

CRAWL_DELAY = 10
MAXIMUM_RETRIES = 3


class ThePaperBoyScraper:
    def __init__(self):
        self.base_url = "https://www.thepaperboy.com/"
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
        logger.info("Initialize scraper with base URL [%s]", self.base_url)

    def fetch_countries(self):
        has_found_content = False
        number_of_retries = 0
        while not has_found_content:
            try:
                countries_data = []
                response = self.scraper.get(urljoin(self.base_url, URLs.get("COUNTRY_LIST")))
                soup = BeautifulSoup(response.text, features="lxml")
                comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    if 'START MAIN COLUMN TABLE' in comment:
                        number_of_retries = 0
                        has_found_content = True
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
                                        country, count = self.extract_country_count(text)
                                        if country and count:
                                            logger.info("Found: href='%s', country='%s', count=%s",
                                                        href, country, count)
                                            countries_data.append({
                                                "country": country,
                                                "url": href,
                                                "count": count
                                            })

                        break
            except Exception as e:
                logging.exception(e)
            if not has_found_content:
                logging.info("Waiting for [%s] seconds before retrying ...", CRAWL_DELAY * number_of_retries)
                sleep(CRAWL_DELAY * number_of_retries)
                number_of_retries += 1

    @staticmethod
    def extract_country_count(text):
        pattern = r'(.*?)\s*\((\d+)\)'
        match = re.search(pattern, text)
        if match:
            country = match.group(1).strip()
            count = int(match.group(2))
            return country, count
        return None, None

    def main(self):
        self.fetch_countries()


if __name__ == "__main__":
    scraper = ThePaperBoyScraper()
    scraper.main()

