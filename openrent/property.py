import functools
import logging

from openrent_bs import OpenRentBeautifulSoup
from property_details import ORPropertyDetails


class Property:
    """
    This might not be needed after all. We can simplify it. But at the same time if we start querying other data sources
    we might need this as a wrapper around some data.
    """

    def __init__(self, property_id: int) -> None:
        self.property_id = property_id
        self.logger = logging.getLogger()
        self.score = None
        self.score_reasons = None

    @functools.cached_property
    def property_details(self) -> ORPropertyDetails:
        self.logger.debug(f"Processing property {self.property_id}")
        pd = OpenRentBeautifulSoup().parse_property_data(self.property_id, self.url)
        self.logger.debug(f"Property {pd}")
        return pd

    @property
    def url(self) -> str:
        return f"https://www.openrent.co.uk/{self.property_id}"

    def __str__(self) -> str:
        return str(self.property_details)
