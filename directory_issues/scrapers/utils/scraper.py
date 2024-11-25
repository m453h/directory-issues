import logging
from time import sleep
import cloudscraper
from cloudscraper import CloudScraper

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s | %(levelname)s: %(message)s")

DELAY = 1
MAX_RETRIES = 3


class BaseScraper:
    def __init__(self):
        self.scraper: CloudScraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})

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


    def main(self):
        pass

