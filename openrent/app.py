import logging
import time

from app_config import AppConfig
from db import DbConnOrm
from openrent_bs import OpenRentBeautifulSoup
from property import Property
from scoring import Scoring
from search_config import SearchConfig
from slack_client import Slack

INFINITE_SCROLL_SLEEP = 3


class App:
    def __init__(self, app_config: AppConfig):
        self.app_config = app_config
        self.db_connector = DbConnOrm(app_config.db_name)
        self.slack = Slack(app_config.slack_token, app_config.slack_channel)
        self.logger = logging.getLogger()
        self.openrent_bs = OpenRentBeautifulSoup()

    def search_properties(self, search_config: SearchConfig, headless=True):
        self.slack.send_message("!!!! Starting a new run !!!!!")

        properties = {}
        # prepare the scoring class
        scoring = Scoring(search_config, self.app_config.tfl_app_id, self.app_config.tfl_app_key)
        # get seed locations for search
        locations = search_config.search_fields.areas.seed_locations

        # retrieve the list of already viewed properties. for now the hardcoded limit is fine.
        already_viewed_properties = self.db_connector.get_latest_properties(10000)
        self.logger.debug(already_viewed_properties)

        # for each search location ( think center of circle of radius X) we do a search
        for location in locations:
            property_ids = self.openrent_bs.search_properties(search_config=search_config, location=location,
                                                              headless=headless)
            # remove all viewed properties
            new_properties = property_ids - already_viewed_properties

            self.logger.info(
                f"[Location: {location}] Received {len(property_ids)} property links. New ones: {len(new_properties)}")
            # send message to slack channel so humans know we're working
            if len(new_properties) == 0:
                self.slack.send_message(f">>>> No new properties found for {location}")
            else:
                self.slack.send_message(f">>>> Yay!!! {len(new_properties)} new properties were found for {location}")

            # could be done in parallel but let's be nice people and not overload their site.
            notifications_sent = 0
            for prop_id in new_properties:
                new_property = Property(prop_id)
                new_property.score, new_property.score_reasons = scoring.compute_likeness_score(new_property)
                notification_sent = self.slack.notify(new_property, search_config.scoring.notify_at)
                if notification_sent:
                    notifications_sent += 1
                time.sleep(1)
                properties[prop_id] = new_property
                self.logger.info(new_property.url)
                self.logger.debug(f"\tScore: {new_property.score}, \n\treasons:{new_property.score_reasons}")

            if len(new_properties) != 0:
                self.slack.send_message(
                    f">>>>> Out of {len(new_properties)} only {notifications_sent} properties had a score above the notification threshold. <<<<<")

        # insert all new properties
        self.db_connector.insert_properties(properties)
        self.slack.send_message(f'!!!! Finished.  !!!!!')
        return properties
