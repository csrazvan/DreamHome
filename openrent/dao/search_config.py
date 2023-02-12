from dataclasses import dataclass
from typing import List, Dict

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Bathrooms:
    max_bathrooms: int
    min_bathrooms: int
    weight: int


@dataclass_json
@dataclass
class HasGarden:
    value: bool
    weight: int


@dataclass_json
@dataclass
class WorkLocations:
    time_to_location_in_minutes: int
    locations: List[str]
    weight: int


@dataclass_json
@dataclass
class Scoring:
    bathrooms: Bathrooms
    has_garden: HasGarden
    notify_at: int
    work_locations: WorkLocations


@dataclass_json
@dataclass
class Areas:
    radius: int
    seed_locations: List[str]


@dataclass_json
@dataclass
class Bedrooms:
    max_bedrooms: int
    min_bedrooms: int
    weight: int


@dataclass_json
@dataclass
class Price:
    max_price: int
    min_price: int
    sweet_spot: int
    weight: int


@dataclass_json
@dataclass
class SearchFields:
    areas: Areas
    bedrooms: Bedrooms
    price: Price


@dataclass_json
@dataclass
class SearchConfig:
    scoring: Scoring
    search_fields: SearchFields

    def get_query_fields(self) -> Dict[str, str]:
        sf: SearchFields = self.search_fields
        return {
            'prices_min': sf.price.min_price,
            'prices_max': sf.price.max_price,
            'bedrooms_min': sf.bedrooms.min_bedrooms,
            'bedrooms_max': sf.bedrooms.max_bedrooms,
            'isLive': "true",
            # we'll use values in 'scoring' to compute score based on this interval. but let's search for everything
            'bathrooms_min': 1,
            'bathrooms_max': 3,
            'within': sf.areas.radius,
        }

    @property
    def total_weight(self) -> int:
        total_weight = 0
        total_weight += self.search_fields.price.weight
        total_weight += self.search_fields.bedrooms.weight
        total_weight += self.scoring.work_locations.weight
        total_weight += self.scoring.bathrooms.weight
        total_weight += self.scoring.has_garden.weight
        return total_weight
