import unittest
from unittest.mock import MagicMock

from scoring import Scoring


class TestScoring(unittest.TestCase):
    def setUp(self) -> None:
        self.search_criteria = MagicMock()

    def test_price_scoring_higher_than_sweetspot(self):
        self.search_criteria.price_sweetspot = 100
        self.search_criteria.price_weight = 10
        scoring = Scoring(self.search_criteria, "", "")
        self.assertEqual(scoring._get_price_score(125)[0], 7.5)

    def test_price_scoring_much_higher_than_sweetspot(self):
        self.search_criteria.price_sweetspot = 100
        self.search_criteria.price_weight = 10
        scoring = Scoring(self.search_criteria, "", "")
        self.assertEqual(scoring._get_price_score(500)[0], 0)

    def test_price_scoring_lower_than_sweetspot(self):
        self.search_criteria.price_sweetspot = 100
        self.search_criteria.price_weight = 10
        scoring = Scoring(self.search_criteria, "", "")
        self.assertEqual(scoring._get_price_score(50)[0], 10)
