import unittest

from src.recognizer import recognize


class PizzaTests(unittest.TestCase):
    def test_order_intent(self):
        self.assertEqual(recognize("can I get a large pizza").intent, "OrderPizza")

    def test_check_order_intent(self):
        self.assertEqual(recognize("where is my order").intent, "CheckOrder")

    def test_size_synonym(self):
        self.assertEqual(recognize("a big pizza please").get("size"), "large")

    def test_several_toppings(self):
        result = recognize("pizza with mushrooms and extra cheese")
        toppings = [e.value for e in result.entities if e.category == "topping"]
        self.assertEqual(toppings, ["mushrooms", "cheese"])

    def test_quantity(self):
        self.assertEqual(recognize("three large pizzas").get("quantity"), 3)


if __name__ == "__main__":
    unittest.main()
