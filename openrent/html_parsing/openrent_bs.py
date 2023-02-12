import logging
import time
import urllib.parse
from typing import Optional, Set
from urllib.parse import urlencode

import dateparser
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from property_details import ORPropertyDetails
from search_config import SearchConfig


class OpenRentBeautifulSoup:
    """
    This class includes all the html parsing code to retrieve:
    * a list of properties available based on a search
    * information about each property.

    If I add other websites there should be a base class defining the interface and each class should overwrite it with
    customized HTML parsing for each site.

    Bits of the html parsing code inspired by https://github.com/afiodorov/openrent
    """

    def __init__(self):
        self.logger = logging.getLogger()

    def search_properties(self, search_config: SearchConfig, location: str, headless=True) -> Set[int]:
        """
        Returns a set of all property ids matching a query.
        """

        params = search_config.get_query_fields()
        # Configure Selenium
        options = Options()
        options.headless = headless
        driver = webdriver.Chrome(options=options)

        # since we can have our search start around various locations each location requires its own query
        params['term'] = location
        query_string = urlencode(
            params)

        url = f"http://www.openrent.co.uk/properties-to-rent/?{query_string}"
        self.logger.debug(url)
        driver.get(url)

        # since the site has infinite scrolling we need to scroll to the bottom to capture all results
        current_offset = -1
        while driver.execute_script("return window.pageYOffset;") != current_offset:
            current_offset = driver.execute_script("return window.pageYOffset;")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

        html_doc = driver.page_source
        # get all property ids
        soup = BeautifulSoup(html_doc, 'html.parser')
        property_ids = [x['href'][1:] for x in soup.find_all("a", {'class': "pli clearfix"})]
        return set([int(property_id) for property_id in property_ids])

    def parse_property_data(self, property_id: int, url: str) -> ORPropertyDetails:
        """
           Retrieve data about a property from OR.
        """
        html_doc = requests.get(url,timeout=30).text
        soup = BeautifulSoup(html_doc, 'lxml')
        self._preprocess(soup)
        price = soup.find_all("h3", {"class": "price-title"})[0]
        price = float(price.text[1:].replace(',', ''))

        desc = soup.find_all("div", {"class": "description"})[0]
        desc = desc.get_text().strip()
        desc.replace("\t", "")

        location = self._parse_location_table(soup)
        features: list[list[str]] = self._parse_feature_table(soup)
        overview = self._parse_overview_table(soup)

        return ORPropertyDetails(
            property_id=property_id,
            title=self._get_title(soup),
            location=location,
            price=price,
            description=desc,
            available_from=self._available_from(features),
            epc=self._epc_rating(features),
            has_garden=self._has_garden(features),
            post_code=self._extract_post_code_from_bb_link(soup),
            features=features,
            url=url,
            bedrooms=self._bedrooms(overview),
            bathrooms=self._bathrooms(overview),
        )

    @staticmethod
    def _parse_location_table(soup):
        """
        Find local transport hubs(stations/undergroudn etc)
        """

        data = []
        table = soup.find('div', attrs={'id': 'LocalTransport'})
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele])

        return data

    @staticmethod
    def _get_title(soup):
        return soup.find("h1", attrs={'class': "property-title"}).text.strip()

    @staticmethod
    def _parse_overview_table(soup):
        def process_element(element):
            return element.text.strip()

        data = []
        tables = soup.find('div', attrs={'class': 'card manage-card mb-0'}).find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [process_element(ele) for ele in cols]
                data.append([ele for ele in cols if ele])
        return data

    @staticmethod
    def _parse_feature_table(soup):
        def process_element(element):
            return element.text.strip()

        data = []
        tables = soup.find('div', attrs={'id': 'Features'}).find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [process_element(ele) for ele in cols]
                data.append([ele for ele in cols if ele])
        return data

    @staticmethod
    def _available_from(features) -> str:
        date_text = [x[1] for x in features if x[0] == "Available From"][0]
        parsed = dateparser.parse(date_text)
        if not parsed:
            return date_text
        return str(parsed.date())

    @staticmethod
    def _bedrooms(overview) -> int:
        for row in overview:
            for idx, field in enumerate(row):
                if field.find("Bedrooms") >= 0:
                    bedrooms = row[idx + 1]
                    if bedrooms:
                        return int(bedrooms)
        return 0

    @staticmethod
    def _bathrooms(overview) -> int:
        for row in overview:
            for idx, field in enumerate(row):
                if field.find("Bathrooms") >= 0:
                    bathrooms = row[idx + 1]
                    if bathrooms:
                        return int(bathrooms)
        return 0

    @staticmethod
    def _epc_rating(features):
        rating = [x[1] for x in features if x[0] == "EPC Rating"]
        if rating:
            return rating[0]

    @staticmethod
    def _has_garden(features) -> bool:
        garden_found = [x[1] for x in features if x[0] == "Garden"]
        if garden_found:
            has_garden = None
            if garden_found[0] == "yes":
                has_garden = True
            elif garden_found[0] == "no":
                has_garden = False

            return has_garden
        return False

    @staticmethod
    def _extract_post_code_from_bb_link(soup) -> Optional[str]:
        """
        Best way to determine an exact post code seems to be to pick it up from the comparebroadband link
        """
        broadband_link = soup.select("a[href*=comparebroadband]")[0].attrs['href']
        return urllib.parse.unquote(broadband_link.split("=")[1])

    @staticmethod
    def _preprocess(soup):
        ticks = soup.find_all("i", attrs={'class': 'fa fa-check'})
        for tick in ticks:
            if tick.text == "":
                tick.string = "yes"

        ticks = soup.find_all("i", attrs={'class': 'fa fa-times'})
        for tick in ticks:
            if tick.text == "":
                tick.string = "no"

        return []
