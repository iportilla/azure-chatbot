# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
A small rule-based intent and entity recognizer, for teaching.

It does, in miniature, what a language-understanding service such as Azure AI
Language (CLU) does:

1. Entity extraction: find cities (list entity), dates (regex entity, resolved
   to a real date) and passenger counts (regex entity) in the text. Cities get a
   role from the word before them: "from X" is the origin, "to X" the destination.
2. Intent classification: replace each entity with a placeholder such as @city,
   then compare the remaining words with example utterances for every intent.
   The best-matching intent wins if its score clears a threshold; otherwise the
   intent is "None".

recognize() returns the same kind of result a CLU prediction does (top intent,
confidence score, entities with category, text, offset and resolved value), so
it can be swapped for a CLU call without changing the bot's handlers.
"""

import re
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Training data: intents and their example utterances ("labeled utterances").
# Entities are written as placeholders so one example covers every city/date.
# ---------------------------------------------------------------------------
INTENTS: dict[str, list[str]] = {
    "Greeting": [
        "hello",
        "hi",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        # Added in Part 5: informal greetings.
        "what's up",
        "howdy",
        "hi there",
    ],
    "Help": [
        "help",
        "what can you do",
        "how does this work",
        "show me the commands",
    ],
    "BookFlight": [
        "book a flight",
        "book a flight to @city",
        "fly from @city to @city",
        "i want to fly to @city @date",
        "get me a ticket to @city",
        "i need @number tickets to @city",
        "reserve a plane ticket",
        "book a trip to @city",
    ],
    "GetWeather": [
        "what's the weather",
        "what's the weather in @city",
        "weather forecast for @city @date",
        "is it raining in @city",
        "will it be sunny @date",
        "how hot is it in @city",
        "temperature in @city",
    ],
    "OrderPizza": [
        "i want a pizza",
        "order a @size pizza",
        "i'd like a @size @topping pizza",
        "can i get a pizza with @topping",
        "@number @size pizzas please",
        "order food",
        # Added in Part 5: more varied ways of ordering.
        "get me a @size pizza",
        "deliver a pizza",
        "i'd like to order a pizza",
        "@size with @topping",
        "@number pizzas with @topping",
        "can you bring me food",
    ],
    "CheckOrder": [
        "where is my order",
        "order status",
        "how long until my pizza arrives",
        "is my food ready",
        # Added in Part 5.
        "when will my pizza arrive",
        "track my order",
        "is my order on the way",
        "how long will it take",
    ],
    "Cancel": [
        "cancel",
        "never mind",
        "stop",
        "forget it",
        "start over",
    ],
}

# Minimum score for an intent to be accepted; below this the intent is "None".
INTENT_THRESHOLD = 0.5

# Words too common to say anything about intent.
STOPWORDS = {"a", "an", "the", "to", "from", "in", "for", "on", "of", "at", "me", "my", "i", "please", "is", "it", "be"}
# Added in Part 5: polite filler words that said nothing about the intent.
STOPWORDS |= {"could", "would", "you", "your", "some", "just"}

# ---------------------------------------------------------------------------
# Entity definitions
# ---------------------------------------------------------------------------

# List entity: canonical value -> synonyms (like a CLU "list component").
CITIES: dict[str, list[str]] = {
    "New York": ["new york", "nyc", "ny"],
    "London": ["london"],
    "Paris": ["paris"],
    "Tokyo": ["tokyo"],
    "Seattle": ["seattle"],
    "Madrid": ["madrid"],
    "Mexico City": ["mexico city", "cdmx"],
    "San Francisco": ["san francisco", "sf"],
}

SIZES: dict[str, list[str]] = {
    "small": ["small", "personal"],
    "medium": ["medium", "regular"],
    "large": ["large", "big", "family size"],
}

TOPPINGS: dict[str, list[str]] = {
    "pepperoni": ["pepperoni"],
    "mushrooms": ["mushroom", "mushrooms"],
    "cheese": ["cheese", "extra cheese"],
    "pineapple": ["pineapple"],
}

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Regex entity: dates, resolved to an ISO date below.
DATE_PATTERN = re.compile(
    r"\b(today|tonight|tomorrow|(?:next\s+)?(?:" + "|".join(WEEKDAYS) + r")|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}

# Regex entity: passenger count, e.g. "2 tickets", "three people".
PASSENGERS_PATTERN = re.compile(
    r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+(?:people|persons|passengers|tickets|adults|seats)\b",
    re.IGNORECASE,
)

# Regex entity: how many pizzas, e.g. "2 pizzas", "three large pizzas".
QUANTITY_PATTERN = re.compile(
    r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+(?:\w+\s+){0,2}pizzas?\b",
    re.IGNORECASE,
)

# Word before a city -> the role that city plays.
CITY_ROLES = {"from": "origin", "to": "destination", "in": "location", "for": "location"}


@dataclass
class Entity:
    category: str  # origin, destination, location, city, date, passengers
    text: str  # the words as the user typed them
    value: str | int  # the resolved value, e.g. "New York" for "nyc"
    offset: int  # character position in the message
    placeholder: str = field(repr=False, default="")


@dataclass
class RecognizerResult:
    text: str
    intent: str
    score: float
    entities: list[Entity]
    # Score for every intent, so students can see why the winner won.
    intent_scores: dict[str, float]

    def get(self, *categories: str):
        """Resolved value of the first entity in any of the given categories."""
        for category in categories:
            for entity in self.entities:
                if entity.category == category:
                    return entity.value
        return None

    def to_dict(self) -> dict:
        result = asdict(self)
        for entity in result["entities"]:
            del entity["placeholder"]
        return result


def _resolve_date(text: str, today: date) -> str:
    text = text.lower()
    if text in ("today", "tonight"):
        return today.isoformat()
    if text == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    # "friday" = the next Friday after today; "next friday" = the one a week later.
    weekday = WEEKDAYS.index(text.split()[-1])
    days_ahead = (weekday - today.weekday()) % 7 or 7
    if text.startswith("next"):
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).isoformat()


def extract_entities(text: str, today: date | None = None) -> list[Entity]:
    today = today or date.today()
    lowered = text.lower()
    entities: list[Entity] = []
    taken: list[tuple[int, int]] = []

    def overlaps(start: int, end: int) -> bool:
        return any(start < t_end and end > t_start for t_start, t_end in taken)

    # Cities: try longer synonyms first so "mexico city" wins over shorter matches.
    synonyms = sorted(
        ((syn, city) for city, syns in CITIES.items() for syn in syns),
        key=lambda pair: -len(pair[0]),
    )
    for synonym, city in synonyms:
        for match in re.finditer(rf"\b{re.escape(synonym)}\b", lowered):
            start, end = match.span()
            if overlaps(start, end):
                continue
            previous_word = re.findall(r"[a-z]+", lowered[:start])[-1:]
            role = CITY_ROLES.get(previous_word[0], "city") if previous_word else "city"
            entities.append(Entity(role, text[start:end], city, start, "@city"))
            taken.append((start, end))

    # Pizza list entities: same idea as cities, but without roles.
    for category, values in (("size", SIZES), ("topping", TOPPINGS)):
        synonyms = sorted(
            ((syn, value) for value, syns in values.items() for syn in syns),
            key=lambda pair: -len(pair[0]),
        )
        for synonym, value in synonyms:
            for match in re.finditer(rf"\b{re.escape(synonym)}\b", lowered):
                start, end = match.span()
                if overlaps(start, end):
                    continue
                entities.append(Entity(category, text[start:end], value, start, f"@{category}"))
                taken.append((start, end))

    for match in DATE_PATTERN.finditer(text):
        if not overlaps(*match.span()):
            entities.append(
                Entity("date", match.group(0), _resolve_date(match.group(0), today), match.start(), "@date")
            )
            taken.append(match.span())

    for match in PASSENGERS_PATTERN.finditer(text):
        if not overlaps(*match.span()):
            count = match.group(1).lower()
            value = int(count) if count.isdigit() else NUMBER_WORDS[count]
            entities.append(Entity("passengers", match.group(0), value, match.start(), "@number"))
            taken.append(match.span())

    for match in QUANTITY_PATTERN.finditer(text):
        start, end = match.span(1)  # only the number, so "large" is still a size
        if not overlaps(start, end):
            count = match.group(1).lower()
            value = int(count) if count.isdigit() else NUMBER_WORDS[count]
            entities.append(Entity("quantity", match.group(1), value, start, "@number"))
            taken.append((start, end))

    return sorted(entities, key=lambda e: e.offset)


def _singular(word: str) -> str:
    """Added in Part 5: treat "pizzas" and "pizza" as the same word."""
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "'s")):
        return word[:-1]
    return word


def _tokens(text: str) -> set[str]:
    return {_singular(word) for word in re.findall(r"@?[a-z']+", text.lower()) if word not in STOPWORDS}


def _similarity(a: set[str], b: set[str]) -> float:
    """Dice coefficient: 1.0 when the word sets are identical, 0.0 when disjoint."""
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def classify_intent(text: str, entities: list[Entity]) -> tuple[str, float, dict[str, float]]:
    # Swap each entity for its placeholder so "fly to paris" looks like "fly to @city".
    normalized = text
    for entity in sorted(entities, key=lambda e: -e.offset):
        normalized = normalized[: entity.offset] + entity.placeholder + normalized[entity.offset + len(entity.text) :]

    tokens = _tokens(normalized)
    scores = {
        intent: round(max(_similarity(tokens, _tokens(example)) for example in examples), 2)
        for intent, examples in INTENTS.items()
    }

    # A message made only of entities ("Paris", "tomorrow") has no intent of its own.
    if not any(not token.startswith("@") for token in tokens):
        return "None", 0.0, scores

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] < INTENT_THRESHOLD:
        return "None", scores[best_intent], scores
    return best_intent, scores[best_intent], scores


def recognize(text: str, today: date | None = None) -> RecognizerResult:
    entities = extract_entities(text, today)
    intent, score, scores = classify_intent(text, entities)
    return RecognizerResult(text, intent, score, entities, scores)
