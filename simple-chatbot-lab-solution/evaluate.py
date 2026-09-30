"""Measure how often the recognizer picks the right intent on sentences it has never seen."""
from src.recognizer import recognize

# Sentences written by someone who never saw INTENTS. Never copy these into INTENTS:
# the point is to measure how the bot handles phrasings it wasn't given.
TEST_SET = [
    ("yo what's up", "Greeting"),
    ("I'm hungry, send me a pizza", "OrderPizza"),
    ("gimme a small cheese pizza", "OrderPizza"),
    ("could you deliver two pizzas to my place", "OrderPizza"),
    ("one family size with pineapple", "OrderPizza"),
    ("has my pizza left the shop yet", "CheckOrder"),
    ("when will my food get here", "CheckOrder"),
    ("forget the whole thing", "Cancel"),
    ("what is the capital of France", "None"),
    ("do you sell burgers", "None"),
]

correct = 0
for text, expected in TEST_SET:
    result = recognize(text)
    ok = result.intent == expected
    correct += ok
    print(f"{'✅' if ok else '❌'} {text!r}: expected {expected}, got {result.intent} ({result.score})")

print(f"\nAccuracy: {correct}/{len(TEST_SET)} = {correct / len(TEST_SET):.0%}")
