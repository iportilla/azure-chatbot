# Lab: Build Your Own Intent and Entity Chatbot

In this lab you turn the Simple Chatbot sample into your own bot. You'll choose a topic, design its **intents** and **entities**, teach the bot to recognize them, and make it ask follow-up questions until it has everything it needs. Then you'll measure how accurate it is.

The worked example throughout is a **pizza-ordering bot**. You can build the same thing, but you'll learn more by choosing your own topic.

**Time:** about 90 minutes
**You'll need:** Python 3.10 or newer, Node.js, a code editor, and basic Python (functions, dictionaries, lists)

| Part | Time |
| --- | --- |
| 0. Set up and explore | 15 min |
| 1. Design your bot | 10 min |
| 2. Add your intents | 10 min |
| 3. Add your entities | 15 min |
| 4. Write the handlers | 20 min |
| 5. Measure accuracy | 15 min |
| 6. Reflect | 5 min |

> **Instructors:** to save 10 minutes of class time, ask students to do the installs in Part 0 (steps 1–3 and the `npm install`) beforehand.

---

## Part 0: Set up and explore (15 min)

1. Copy the `simple-chatbot` folder and give the copy your own name, e.g. `pizza-bot`. Work only in your copy.
1. Check that `python3 --version` shows 3.10 or newer. On macOS the built-in `python3` is 3.9, which installs an old SDK without any error, and the bot won't start. If yours is older, install Python from [python.org](https://www.python.org/downloads/) first.
1. In a terminal, from inside your folder:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   On Windows, activate with `.venv\Scripts\activate` instead.

1. Start the bot:

   ```bash
   python -m src.main
   ```

   You should see `======== Running on http://localhost:3978 ========`.

1. In a **second** terminal, install and start the Agents Playground. It opens a chat window in your browser:

   ```bash
   npm install -g @microsoft/teams-app-test-tool
   teamsapptester
   ```

1. Chat with the bot. Type `/debug` first so you can see what it recognizes, then try:
   - `book a flight from NYC to Paris tomorrow`
   - `book a flight`, then answer its questions
   - `tell me a joke`

> **Restarting:** after every code change, stop the bot with `Ctrl+C` and run `python -m src.main` again. The Playground reconnects by itself.

### Key ideas

Keep this table handy for the rest of the lab.

| Term | Meaning | Pizza example |
| --- | --- | --- |
| **Utterance** | Something the user says | "I'd like a large pepperoni pizza" |
| **Intent** | What the user wants to do | `OrderPizza` |
| **Entity** | A piece of information inside the utterance | size = `large`, topping = `pepperoni` |
| **List entity** | An entity with a fixed set of values, each with synonyms | size: `large` ← "large", "big", "family size" |
| **Regex entity** | An entity found by a text pattern | quantity: "**2** pizzas" |
| **Role** | The part an entity plays in the sentence | city: "from X" = origin, "to X" = destination |
| **Resolution** | Turning the user's words into a standard value | "NYC" → `New York`, "tomorrow" → a date |
| **Slot filling** | Asking follow-up questions until every required detail has a value | "What size would you like?" |

### ✅ Checkpoint 0

1. For `book a flight from NYC to Paris tomorrow`, what are the **intent**, the **score** and the **entities**?
1. When the bot asked for a destination and you typed just `Paris`, the debug output showed the intent `None`. Why? And why did the bot still understand your answer?

---

## Part 1: Design your bot (10 min)

Pick a topic, for example:

- 🍕 Pizza ordering (the worked example)
- 🎬 Cinema tickets: movie, showtime, number of seats
- 🏨 Hotel booking: city, check-in date, number of nights
- 🏋️ Gym classes: class type, day, time

Plan **2 intents** and **2–3 entities** in a table like this one:

| Intent | Example utterances (at least 4) | Entities | Required details |
| --- | --- | --- | --- |
| `OrderPizza` | "I want a pizza", "order a large pizza", "can I get a pizza with mushrooms", "2 big pizzas please" | size, topping, quantity | size, topping |
| `CheckOrder` | "where is my order", "order status", "how long until my pizza arrives", "is my food ready" | – | – |

| Entity | Kind | Values and synonyms |
| --- | --- | --- |
| size | list | small (small, personal), medium (medium, regular), large (large, big, family size) |
| topping | list | pepperoni, mushrooms (mushroom, mushrooms), cheese (cheese, extra cheese), pineapple |
| quantity | regex | a number before "pizza(s)": "2 pizzas", "three large pizzas" |

**Tips:**
- `Greeting`, `Help`, `Cancel` and `None` already exist. Don't add them again.
- Make your intents clearly different. If you can't decide which intent a sentence belongs to, the bot won't be able to either.
- Vary your examples: short and long, and different ways of saying the same thing.

---

## Part 2: Add your intents (10 min)

Open [src/recognizer.py](src/recognizer.py) and find the `INTENTS` dictionary. Add your intents **above** `"Cancel"`. Write entities as placeholders: `@` followed by the entity name, and `@number` for numbers.

```python
    "OrderPizza": [
        "i want a pizza",
        "order a @size pizza",
        "i'd like a @size @topping pizza",
        "can i get a pizza with @topping",
        "@number @size pizzas please",
        "order food",
    ],
    "CheckOrder": [
        "where is my order",
        "order status",
        "how long until my pizza arrives",
        "is my food ready",
    ],
```

**Why placeholders?** Before scoring, the recognizer replaces every entity it finds with its placeholder, so "I'd like a large pepperoni pizza" becomes "I'd like a @size @topping pizza". One example then covers every size and topping.

You can test the recognizer without restarting the bot:

```bash
python -c "from src.recognizer import recognize; print(recognize('where is my order').intent)"
```

### ✅ Checkpoint 2

The command above prints `CheckOrder`.

---

## Part 3: Add your entities (15 min)

### 3a. List entities

In [src/recognizer.py](src/recognizer.py), add your value lists just above `WEEKDAYS = [...]`. Each key is the resolved value, and the list holds the words users might type for it:

```python
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
```

Then, in the `extract_entities` function, add this block just **before** the line `for match in DATE_PATTERN.finditer(text):`. Change the tuple on the first line to use your own entity names and lists:

```python
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
```

> **Think about it:** why are the synonyms sorted longest first? Try the phrase "extra cheese".

### 3b. A regex entity

Add a pattern next to `PASSENGERS_PATTERN`. It matches a number followed by up to two words and then "pizza" or "pizzas":

```python
# Regex entity: how many pizzas, e.g. "2 pizzas", "three large pizzas".
QUANTITY_PATTERN = re.compile(
    r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+(?:\w+\s+){0,2}pizzas?\b",
    re.IGNORECASE,
)
```

Use it at the end of `extract_entities`, just before `return sorted(...)`:

```python
    for match in QUANTITY_PATTERN.finditer(text):
        start, end = match.span(1)  # only the number, so "large" is still a size
        if not overlaps(start, end):
            count = match.group(1).lower()
            value = int(count) if count.isdigit() else NUMBER_WORDS[count]
            entities.append(Entity("quantity", match.group(1), value, start, "@number"))
            taken.append((start, end))
```

### ✅ Checkpoint 3

```bash
python -c "from src.recognizer import recognize; import json; print(json.dumps(recognize('three large pepperoni pizzas').to_dict(), indent=2))"
```

This shows the intent `OrderPizza` and three entities: quantity `3`, size `large` and topping `pepperoni`.

---

## Part 4: Write the handlers (20 min)

Open [src/agent.py](src/agent.py) and look at `on_book_flight`. It's the pattern you'll copy:

1. Load the order in progress from conversation state.
1. Copy any entities from this message into it.
1. If a required detail is still missing, save the order and ask for it.
1. Otherwise, complete the action and clear the order.

Add your handlers above `async def on_cancel(`:

```python
PIZZA_SLOTS = {
    "size": "What size would you like: small, medium or large?",
    "toppings": "Which toppings? We have pepperoni, mushrooms, cheese and pineapple.",
}
PIZZA_ORDER = "ConversationState.pizza_order"


async def on_order_pizza(context: TurnContext, state: TurnState, result: RecognizerResult):
    order = state.get_value(PIZZA_ORDER, dict)

    size = result.get("size")
    if size is not None:
        order["size"] = size
    quantity = result.get("quantity")
    if quantity is not None:
        order["quantity"] = quantity
    # A message can contain several toppings, so collect all of them.
    toppings = [e.value for e in result.entities if e.category == "topping"]
    if toppings:
        order["toppings"] = toppings

    missing = [slot for slot in PIZZA_SLOTS if slot not in order]
    if missing:
        # Remember which question we asked. This also keeps the saved order from
        # being empty, which the SDK would treat the same as "no order".
        order["asking_for"] = missing[0]
        state.set_value(PIZZA_ORDER, order)
        await context.send_activity(PIZZA_SLOTS[missing[0]])
        return

    state.delete_value(PIZZA_ORDER)
    quantity = order.get("quantity", 1)
    await context.send_activity(
        f"🍕 Order placed (pretend): {quantity} {order['size']} pizza{'s' if quantity != 1 else ''} "
        f"with {', '.join(order['toppings'])}."
    )


async def on_check_order(context: TurnContext, _state: TurnState, _result: RecognizerResult):
    await context.send_activity("🛵 Your pizza is in the oven. About 20 minutes to go!")
```

Then connect everything:

1. **Register the handlers.** Add your intents to `INTENT_HANDLERS`:

   ```python
       "OrderPizza": on_order_pizza,
       "CheckOrder": on_check_order,
   ```

1. **Continue an unfinished order.** In `on_message`, under the similar lines for `BOOKING`, add these lines. They make a one-word answer like "large" count as part of the order:

   ```python
       if intent == "None" and result.entities and state.get_value(PIZZA_ORDER, lambda: None):
           intent = "OrderPizza"
   ```

1. **Let users cancel.** In `on_cancel`, also clear your order:

   ```python
       state.delete_value(PIZZA_ORDER)
   ```

1. **Update `HELP_TEXT`** so users know what your bot can do.

### ✅ Checkpoint 4

Restart the bot. This conversation works in the Playground:

```text
You: I want 2 pizzas
Bot: What size would you like: small, medium or large?
You: large
Bot: Which toppings? We have pepperoni, mushrooms, cheese and pineapple.
You: pepperoni and mushrooms
Bot: 🍕 Order placed (pretend): 2 large pizzas with pepperoni, mushrooms.
```

---

## Part 5: Measure accuracy (15 min)

So far you've only tried sentences you wrote with your own examples in mind. Real users will say things you didn't expect. To measure that, you need a **test set**: sentences the bot has never seen.

1. Ask a classmate to write 6 sentences for your bot without looking at your `INTENTS`. At least one should match **none** of your intents.
1. Create `evaluate.py` in your project folder, with their sentences in `TEST_SET`:

   ```python
   """Measure how often the recognizer picks the right intent on sentences it has never seen."""
   from src.recognizer import recognize

   # Your classmate's sentences. Don't copy the examples from INTENTS.
   TEST_SET = [
       ("yo what's up", "Greeting"),
       ("I'm hungry, send me a pizza", "OrderPizza"),
       ("gimme a small cheese pizza", "OrderPizza"),
       ("has my pizza left the shop yet", "CheckOrder"),
       ("forget the whole thing", "Cancel"),
       ("what is the capital of France", "None"),
   ]

   correct = 0
   for text, expected in TEST_SET:
       result = recognize(text)
       ok = result.intent == expected
       correct += ok
       print(f"{'✅' if ok else '❌'} {text!r}: expected {expected}, got {result.intent} ({result.score})")

   print(f"\nAccuracy: {correct}/{len(TEST_SET)} = {correct / len(TEST_SET):.0%}")
   ```

1. Run it:

   ```bash
   python evaluate.py
   ```

   With the example sentences above, the pizza bot scores **50%**.

1. Try to improve the score **without** copying the test sentences into `INTENTS`. Add more varied example utterances, or add synonyms to your entity lists. Run `evaluate.py` after each change.

### ✅ Checkpoint 5

Write down your accuracy before and after your changes.

> **Why not just paste the test sentences into `INTENTS`?** Then you'd be measuring whether the bot remembers what it was told, not whether it understands new sentences. Keeping test sentences separate from training examples is one of the most important habits in machine learning.

---

## Part 6: Reflect (5 min)

1. Pick one sentence your bot got wrong. Why did it fail?
1. Try "I don't want a pizza". What does the bot do, and why can't counting shared words handle this?

---

## What to hand in

- [ ] Your design table (Part 1)
- [ ] Your bot folder, with 2 new intents, at least 2 new entities, and one intent that asks follow-up questions
- [ ] `evaluate.py` and your before-and-after accuracy (Part 5)
- [ ] Your answers to Checkpoint 0 and Part 6
- [ ] A screenshot of a complete conversation in the Agents Playground

---

## Going further (optional)

- **Write unit tests:** add `tests/test_my_bot.py` using [tests/test_recognizer.py](tests/test_recognizer.py) as a model, and run `python -m unittest`.
- **Tune the threshold:** lower `INTENT_THRESHOLD` from 0.5 to 0.4 and run `evaluate.py` again. Then try "my order was wrong" at both thresholds. A lower threshold lets the bot answer more sentences, but what does it cost?
- **More reflection:** what would go wrong with 500 toppings, or with spelling mistakes? What happens if the user asks "actually, where's my order?" while the bot is waiting for a size, and what *should* happen?
- **Confirmation step:** before placing the order, ask "2 large pizzas with pepperoni. Shall I place the order?" and handle yes and no.
- **Remove the travel intents:** delete `BookFlight` and `GetWeather`, their handlers and their tests, so the bot is only about your topic.
- **Deploy to Azure:** follow [AZURE_README.md](AZURE_README.md) and test your bot in Web Chat.
- **Use a real language service:** build the same intents and entities in [Azure AI Language (CLU)](https://learn.microsoft.com/azure/ai-services/language-service/conversational-language-understanding/overview) and replace `recognize()` with a call to it. Run `evaluate.py` against both and compare.

## Solution

A complete version of the pizza bot, with checkpoint answers and an explanation of every step, is in [simple-chatbot-lab-solution](../simple-chatbot-lab-solution/README.md). Try the lab yourself first!
