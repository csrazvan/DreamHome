from typing import Tuple, List

from property import Property
from property_details import ORPropertyDetails
from search_config import SearchConfig
from tfl_helper import TflHelper


class Scoring:
    def __init__(self, search_config: SearchConfig, tfl_app_id: str, tfl_app_key: str):
        self.search_config = search_config
        self.tfl = TflHelper(tfl_app_id, tfl_app_key)

    # for every criterion that has a weight we compute the actual weight of the property based on some custom logic
    # for example having a garden is a binary value. you either get the score or not
    # but price can be a bit more complicated. since we establish a sweet spot for the price. anything bellow it gets
    # full points anything above it loses points (until 0)
    def compute_likeness_score(self, new_property: Property) -> Tuple[float, List[str]]:
        total_weight = self.search_config.total_weight
        pd: ORPropertyDetails = new_property.property_details
        price_score, price_reason = self._get_price_score(property_price=pd.price)
        bedroom_score, bedroom_reason = self._get_bedrooms_score(property_bedrooms=pd.bedrooms)
        bathroom_score, bathroom_reason = self._get_bathrooms_score(property_bathrooms=pd.bathrooms)
        garden_score, garden_reason = self._get_garden_score(has_garden=pd.has_garden,
                                                             description=pd.description.lower())
        location_score, location_reason = self._get_location_score(precise_location=pd.post_code,
                                                                   nearby_stations=pd.location)
        total_score = 100 * (
                price_score + bedroom_score + bathroom_score + garden_score + location_score) // total_weight
        reasons = [price_reason, bedroom_reason, bathroom_reason, garden_reason, location_reason]
        return total_score, reasons

    def _get_price_score(self, property_price: float) -> Tuple[float, str]:
        price_query = self.search_config.search_fields.price
        if property_price <= price_query.sweet_spot:
            return price_query.weight, f"* Property price {property_price} is le than sweetspot {price_query.sweet_spot}"

        deviation = 100. * (
                property_price - price_query.sweet_spot) / price_query.sweet_spot
        return max(0.,
                   price_query.weight - deviation * price_query.weight / 100), f"* Property price {property_price} is higher than sweetspot {price_query.sweet_spot}"

    def _get_bedrooms_score(self, property_bedrooms: int) -> Tuple[float, str]:
        bedroom_query = self.search_config.search_fields.bedrooms
        return (
            0.,
            f"* Not enough bedrooms ({property_bedrooms})") if property_bedrooms < bedroom_query.min_bedrooms else (
            bedroom_query.weight, f"* Enough bedrooms ({property_bedrooms})")

    def _get_bathrooms_score(self, property_bathrooms) -> Tuple[float, str]:
        bathroom_query = self.search_config.scoring.bathrooms
        return (
            0.,
            f"* Not enough bathrooms ({property_bathrooms})") if property_bathrooms < bathroom_query.min_bathrooms else (
            bathroom_query.weight, f"* Enough bathrooms ({property_bathrooms})")

    # gardens are always a plus
    def _get_garden_score(self, has_garden, description) -> Tuple[float, str]:
        private_garden = not (description.find("shared garden") >= 0 or description.find("communal garden") >= 0)
        if has_garden and private_garden:
            return self.search_config.scoring.has_garden.weight, "* Has garden"
        elif not has_garden:
            return 0, "* Does not have garden"
        elif not private_garden:
            return 0, "* Has garden but it's shared or communal"
        else:
            return 0, "* Garden state unknown"

    # Target locations are the ones where family members work. So we try to compute how fast each of us can get to
    # our offices. Now, this can be further refined but for now it's a decent metric.

    def _get_location_score(self, precise_location: str, nearby_stations: List[List[str]]) -> Tuple[float, str]:
        work_locations_query = self.search_config.scoring.work_locations
        total_location_weight = work_locations_query.weight
        per_location = total_location_weight // len(work_locations_query.locations)
        output = []
        total_score = 0

        # if we have a precise location it means we could compute the post code for the property
        if precise_location:
            # for every member of the family
            for location in work_locations_query.locations:
                score = 0
                # use the TFL api to get time to work
                time_to_work = self.tfl.get_best_time(precise_location, location)
                # compare with desired commute time
                if time_to_work <= work_locations_query.time_to_location_in_minutes:
                    score = per_location
                    output.append(
                        f"* Trip time {time_to_work} to {location} is lower or equal to desired one {work_locations_query.time_to_location_in_minutes}")
                else:
                    deviation = 100. * (
                            time_to_work - work_locations_query.time_to_location_in_minutes) / work_locations_query.time_to_location_in_minutes
                    score = per_location - deviation * per_location / 100
                    output.append(
                        f"* Trip time {time_to_work} to {location} is greater than desired one {work_locations_query.time_to_location_in_minutes}")
                total_score += score
            return total_score, "\n".join(output)
        else:
            # Since we could not detect the post code we should check trip time from any nearby stations and minimize it
            # TODO: implement the above.
            return work_locations_query.weight, "* Precise postcode could not be detected"
