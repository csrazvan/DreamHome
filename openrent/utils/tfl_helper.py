import datetime
import json
import logging
import math

from retry import retry
from tfl.api_token import ApiToken
from tfl.client import RestClient




class TflHelper:
    """
    Utility class for calling TFL journey APIs.
    Given 2 points TFL will give various journey plans. We pick the shortest.
    Some more logic could go here in order to understand for example that the shortest journey is 75% walking and 25% tube.
    Or some other similar stuff.
    """
    def __init__(self, app_id: str, app_key: str) -> None:
        token = ApiToken(app_id, app_key)
        self.client = RestClient(token)
        self.logger = logging.getLogger()

    # retry ... just in case
    @retry(KeyError, delay=1, backoff=2, tries=3)
    def get_best_time(self, start_location: str, end_location: str) -> int:
        # compute next monday since traffic on weekends is less important
        next_monday = self._get_next_working_day_as_string()

        # only select overground/tube since we don't care about other transportation methods
        resp = self.client.send_request(f"Journey/JourneyResults/{start_location}/to/{end_location}",
                                        params={'mode': 'overground,tube', 'date': next_monday, 'time': '0800'})
        journeys_response = json.loads(resp.text)
        min_duration = math.inf

        # if we can't compute the journey let's respond with a long time. humans can then judge.
        if "journeys" not in journeys_response:
            self.logger.error(f"Could not find route from {start_location} to {end_location}")
            return 120
        for journey in journeys_response["journeys"]:
            min_duration = min(min_duration, int(journey['duration']))
        return min_duration

    # I mean sure ... next working day could be a strike but let's assume this will not happen that often
    @staticmethod
    def _get_next_working_day_as_string() -> str:
        today = datetime.date.today()
        diff = (0 - today.weekday()) % 7
        next_working_day = today + datetime.timedelta(days=diff)
        return next_working_day.strftime("%Y%m%d")
