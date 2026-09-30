# Run with: python -m unittest
import unittest
from datetime import date

from src.recognizer import recognize

# A Monday, so weekday resolution is predictable.
TODAY = date(2026, 9, 28)


class IntentTests(unittest.TestCase):
    def assertIntent(self, text, intent):
        self.assertEqual(recognize(text, TODAY).intent, intent, text)

    def test_intents(self):
        self.assertIntent("hello", "Greeting")
        self.assertIntent("good evening", "Greeting")
        self.assertIntent("what can you do?", "Help")
        self.assertIntent("book a flight to Paris", "BookFlight")
        self.assertIntent("I need 2 tickets to Tokyo", "BookFlight")
        self.assertIntent("is it raining in Seattle?", "GetWeather")
        self.assertIntent("never mind", "Cancel")

    def test_unknown_text_is_none(self):
        self.assertIntent("tell me a joke", "None")

    def test_entities_alone_have_no_intent(self):
        self.assertIntent("Paris", "None")
        self.assertIntent("tomorrow", "None")


class EntityTests(unittest.TestCase):
    def test_city_roles_and_synonyms(self):
        result = recognize("book a flight from NYC to Mexico City", TODAY)
        self.assertEqual(result.get("origin"), "New York")
        self.assertEqual(result.get("destination"), "Mexico City")

    def test_location_role(self):
        self.assertEqual(recognize("weather in london", TODAY).get("location"), "London")

    def test_dates_are_resolved(self):
        self.assertEqual(recognize("tomorrow", TODAY).get("date"), "2026-09-29")
        self.assertEqual(recognize("friday", TODAY).get("date"), "2026-10-02")
        self.assertEqual(recognize("next friday", TODAY).get("date"), "2026-10-09")

    def test_passengers(self):
        self.assertEqual(recognize("three tickets to paris", TODAY).get("passengers"), 3)
        self.assertEqual(recognize("2 people to paris", TODAY).get("passengers"), 2)


if __name__ == "__main__":
    unittest.main()
