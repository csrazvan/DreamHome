from dataclasses import dataclass
from typing import List


@dataclass
class ORPropertyDetails:
    """
    Simple object to hold information about a property.
    When other providers for data will be added this might be turned into a base class for common properties and then
    depending on the data each provider offers we could have different classes extending it.
    """
    # property ID.
    property_id: int
    # property title
    title: str
    # location data reported by OpenRent(closest underground/overground stations and distance)
    location: List[List[str]]
    # property price
    price: float
    # property description
    description: str
    # date when property is available
    # TODO: this should factor in the search
    available_from: str
    # EPC rating
    epc: str
    # does the property report include a garden ( be careful here we need to distinguish between private/shared/etc)
    has_garden: bool
    # post code - if available. it comes from the broadband availability link
    post_code: str
    # list of features for the property as reported by OR
    features: List[List[str]]
    # OR url. can be computed from the property ID
    url: str
    # number of bedrooms
    bedrooms: int
    # number of bathrooms
    bathrooms: int
