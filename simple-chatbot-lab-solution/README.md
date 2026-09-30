# Lab Solution: Pizza & Travel Bot

This is a complete, working solution to [the chatbot lab](../simple-chatbot/LAB.md), for going through with the class **after** they've done it. It's the pizza-ordering example from the lab, with every part finished. It also includes two optional "Going further" items: unit tests, and a longer accuracy study.

It keeps the original travel intents (`BookFlight`, `GetWeather`) alongside the new pizza intents, as the lab does. Removing them is an optional extra.

## Run it

You need Python 3.10 or newer and Node.js, as for the [original sample](../simple-chatbot/README.md#prerequisites).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

In a second terminal:

```bash
npm install -g @microsoft/teams-app-test-tool
teamsapptester
```

Run the tests and the accuracy check:

```bash
python -m unittest
```

```bash
python evaluate.py
```

## What changed, part by part

All changes are in four files. Search for the names below to find them.

| Part | File | What was added |
| --- | --- | --- |
| 2. Intents | `src/recognizer.py` | `"OrderPizza"` and `"CheckOrder"` in `INTENTS` |
| 3a. List entities | `src/recognizer.py` | `SIZES`, `TOPPINGS`, and the loop starting `# Pizza list entities` in `extract_entities` |
| 3b. Regex entity | `src/recognizer.py` | `QUANTITY_PATTERN`, and the loop that uses it at the end of `extract_entities` |
| 4. Handlers | `src/agent.py` | `PIZZA_SLOTS`, `PIZZA_ORDER`, `on_order_pizza`, `on_check_order`; two lines in `INTENT_HANDLERS`; the `PIZZA_ORDER` check in `on_message`; one line in `on_cancel`; pizza lines in `HELP_TEXT` |
| 5. Accuracy | `evaluate.py`, `src/recognizer.py` | A 10-sentence test set; extra example utterances marked `# Added in Part 5`; extra `STOPWORDS`; `_singular()` |
| Going further | `tests/test_my_bot.py` | 5 unit tests for intents, synonyms, several toppings and quantity |

To see every change at once, compare this folder with the starting sample:

```bash
diff -r ../simple-chatbot/src src
```

## Checkpoint answers

### Checkpoint 0: exploring the starting bot

1. `book a flight from NYC to Paris tomorrow` gives:
   - **intent:** `BookFlight`, **score:** 0.86
   - **entities:** origin = New York, destination = Paris, date = tomorrow's date (e.g. `2026-09-29`)

   "NYC" becomes "New York" because it's a **synonym** in the `CITIES` list entity; the recognizer **resolves** it to the standard value.
1. `Paris` on its own is only an entity. Once it's replaced by `@city`, there are no words left to show what the user wants, so the recognizer deliberately returns `None`. The bot still understands because a booking is waiting for details: `on_message` treats a `None` message that contains entities as the answer to the bot's question.

### Part 1: design table

Any clear design is fine. Look for:
- intents that don't overlap ("order" vs "check an order", not "order pizza" vs "buy pizza")
- at least 4 varied examples per intent
- entities with synonyms, and at least one required detail

### Checkpoint 2

The command prints `CheckOrder` (score 1.0; it's one of the examples).

### Checkpoint 3

`three large pepperoni pizzas` → `OrderPizza`, score 0.86, entities:

| category | text | value |
| --- | --- | --- |
| quantity | three | 3 |
| size | large | large |
| topping | pepperoni | pepperoni |

**"Why are synonyms sorted longest first?"** For `pizza with extra cheese`, the recognizer must match "extra cheese" as one entity before it tries "cheese" on its own. Otherwise only "cheese" becomes `@topping`, and the leftover word "extra" is scored as part of the sentence and lowers the intent score. The same rule makes "Mexico City" win over a shorter city name inside it. With longest-first, the result is one entity: text "extra cheese", value `cheese`.

### Checkpoint 4

```text
You: I want 2 pizzas
Bot: What size would you like: small, medium or large?
You: large
Bot: Which toppings? We have pepperoni, mushrooms, cheese and pineapple.
You: pepperoni and mushrooms
Bot: 🍕 Order placed (pretend): 2 large pizzas with pepperoni, mushrooms.
```

### Checkpoint 5: accuracy

The lab asks for 6 test sentences; the 6 examples given in the lab score **50%** before any changes. This solution goes further, with a 10-sentence test set (including 2 that match no intent) and several rounds of changes. It also covers the "Tune the threshold" item from Going further.

| Step | Change | Accuracy | Kept? |
| --- | --- | --- | --- |
| 0 | Starting point (Parts 2–4 only) | 3/10 = 30% | – |
| 1 | Added 13 varied example utterances to `OrderPizza`, `CheckOrder` and `Greeting` | 5/10 = 50% | ✅ |
| 2a | Lowered `INTENT_THRESHOLD` from 0.5 to 0.4 | 7/10 = 70% | ❌ |
| 2b | Tried 0.45 instead | 5/10 = 50% | ❌ |
| 3 | Threshold back at 0.5; treated plurals as singular ("pizzas" = "pizza"); added polite filler words (could, would, you, your, some, just) to `STOPWORDS` | 7/10 = 70% | ✅ |

**Why step 2a was rejected, even though it scored 70%:** lowering the threshold makes the bot guess more often. It also started misreading sentences outside the test set. "My order was wrong" became `OrderPizza`, so the bot would try to take a new order from an upset customer. Step 3 reaches the same score without that problem, and also stops "do you sell burgers" from being read as `Help`.

This is a good discussion point: **one accuracy number isn't the whole story.** Also check what the bot gets wrong and how bad those mistakes are.

**Note on step 1:** "what's up" was added as a Greeting example, and the test sentence is "yo what's up". That's fine: "what's up" is a standard greeting any designer would include, and the test sentence wasn't copied. Watch for students who paste whole test sentences into `INTENTS`. Their accuracy will jump to 100% and tell you nothing.

**Still wrong after step 3, and why:**

| Sentence | Got | Why word overlap fails |
| --- | --- | --- |
| "I'm hungry, send me a pizza" | `None` (0.33) | "Hungry" and "send" appear in no example. The bot doesn't know that being hungry implies ordering. |
| "has my pizza left the shop yet" | `None` (0.29) | A completely different way of asking about status. There are no shared words except "pizza". |
| "when will my food get here" | `None` (0.44) | Close to "when will my pizza arrive", but "food get here" and "pizza arrive" share no words even though they mean the same thing. |

All three need the bot to understand **meaning**, not just words. That's the motivation for trained models.

## Reflection answers

### Part 6

1. **A sentence the bot got wrong.** See the table above. The pattern: the bot fails whenever the user uses words that appear in none of the examples, even when the meaning is obvious to a person.

1. **"I don't want a pizza"** is read as `OrderPizza` (score 0.8), and the bot asks for a size. Word overlap only looks at *which* words appear, not how they relate, so "don't" doesn't reverse anything. It's just one more word, slightly lowering the score. Handling negation needs a model that understands sentence structure.

### Going further: more reflection

- **500 toppings or spelling mistakes.**
  - *500 toppings:* someone has to type every synonym by hand, and similar names start clashing (e.g. "pepper" inside "pepperoni" would need careful word boundaries).
  - *Spelling mistakes:* "pepperonni" or "larg" match nothing, because matching is exact. Real services use fuzzy matching or learned models that cope with typos.

- **"Actually, where's my order?" in the middle of an order.** In this bot, the message is recognized as `CheckOrder`, so the status reply is sent, and the unfinished order stays saved. If the user then says "medium", the order continues. However, the bot doesn't *remind* them it was waiting for a size, so the user may not know the order is still open. Better behavior: answer the question, then repeat the pending question ("Your pizza is in the oven. Now, what size would you like?"). The saved `asking_for` field makes this easy to add.

- **How a trained model (CLU) does better.** It learns from labeled examples instead of counting shared words, so it recognizes that "hungry, send me a pizza" and "has my pizza left the shop" are close in meaning to its examples. It copes with typos and handles negation better. It also gives calibrated confidence scores, which makes choosing a threshold more reliable. The cost: it needs an Azure resource, training time and more labeled data, and it's harder to see *why* it made a decision.

## Common student mistakes

| Symptom | Cause |
| --- | --- |
| Intent is recognized in `/debug`, but the bot says "Sorry, I didn't understand" | The handler wasn't added to `INTENT_HANDLERS` |
| A one-word answer like "large" isn't understood | The `PIZZA_ORDER` check in `on_message` is missing, or the bot was restarted mid-conversation (`MemoryStorage` loses state on restart) |
| "order a pizza" then "medium" isn't understood, but "order a large pizza" then "pepperoni" works | The saved order was empty. The SDK treats an empty value the same as "nothing saved". The lab's `order["asking_for"] = ...` line fixes this; check it wasn't left out. |
| Examples are never matched even with the right words | Entity words written literally in `INTENTS` (e.g. "a large pizza") instead of placeholders ("a @size pizza") |
| An entity isn't found | The synonym isn't in the list, or the entity loop was added after the `return` statement in `extract_entities` |
| `cancel` doesn't clear the order | `state.delete_value(PIZZA_ORDER)` wasn't added to `on_cancel` |
| Code changes have no effect | The bot wasn't restarted |
| Accuracy is 100% | Test sentences were copied into `INTENTS` |

## Other extras (not included)

Hints for the confirmation step from "Going further", and two more ideas that follow from the reflection questions:

- **Confirmation step:** add `Confirm` ("yes", "sure", "go ahead") and `Deny` ("no", "nope") intents. When every slot is filled, set `order["asking_for"] = "confirmation"` and ask, instead of placing the order. In `on_message`, if the order is waiting for confirmation, send `Confirm` and `Deny` to the pizza handler.
- **Remind after an interruption:** in `on_check_order`, if an order is in progress, add `PIZZA_SLOTS[order["asking_for"]]` to the reply.
- **"Make it medium":** add a `ChangeOrder` intent whose handler updates the matching slot in the saved order.
