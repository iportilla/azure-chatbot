# Simple Chatbot

A simple chatbot for teaching **intents and entities**, built on the [Microsoft 365 Agents SDK](https://learn.microsoft.com/microsoft-365/agents-sdk/quickstart?pivots=python) and based on the [quickstart](https://github.com/microsoft/Agents/tree/main/samples/python/quickstart) sample. It uses a small rule-based recognizer, so it runs offline, with no Azure account or language service.

It shows how to:

- **classify intents:** match a message against labeled example utterances and pick the best-scoring intent, or `None` below a threshold
- **extract entities:** list entities (cities with synonyms, e.g. `NYC` → New York), regex entities (dates, passenger counts), **roles** (`from X` = origin, `to X` = destination) and **resolution** (`next friday` → an ISO date)
- **route on intent:** one handler per intent
- **fill slots over several turns:** if a booking is missing its destination or date, the bot asks, and remembers the answer in conversation state

## Teaching materials

| | |
| --- | --- |
| [LAB.md](LAB.md) | A 90-minute hands-on lab. Students turn this sample into their own bot, e.g. for ordering pizza. |
| [Lab solution](../simple-chatbot-lab-solution/README.md) | The finished pizza bot, with checkpoint answers, an accuracy study, reflection answers and common student mistakes |
| [AZURE_README.md](AZURE_README.md) | Connecting the bot to Azure Bot Service, including the fix for "AAD App Creation Failed" |

## Prerequisites

- **Python 3.10 or newer.** Check with `python3 --version`. On macOS the built-in `python3` is 3.9: it installs an old SDK version without any error, and this sample won't run on it. Install a newer Python from [python.org](https://www.python.org/downloads/) or Homebrew.
- **Node.js**, for the Microsoft 365 Agents Playground

## Run locally

With no credentials configured, the bot accepts anonymous requests, so you can test it without Azure.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

On Windows, activate with `.venv\Scripts\activate` instead. You should see `======== Running on http://localhost:3978 ========`.

In a second terminal, start the Agents Playground. It opens a chat in your browser, connected to `http://localhost:3978/api/messages`:

```bash
npm install -g @microsoft/teams-app-test-tool
teamsapptester
```

Run the tests:

```bash
python -m unittest
```

## What to try

| Intent | Try saying | Entities used |
| --- | --- | --- |
| `Greeting` | "hello", "good morning" | – |
| `BookFlight` | "book a flight from NYC to Paris tomorrow", "I need 2 tickets to Tokyo" | origin, destination, date, passengers |
| `GetWeather` | "what's the weather in London", "is it raining in Seattle today?" | location, date |
| `Cancel` | "never mind", "start over" | – |
| `Help` | "help", "what can you do?" | – |
| `None` | anything else | – |

Type **/debug** to turn on a JSON view of what the recognizer found in each message: the top intent, every intent's score, and each entity with its category, text, resolved value and position.

If a booking is missing details, the bot asks for them:

```text
You: book a flight from NYC
Bot: Where would you like to fly to?
You: Paris
Bot: What date do you want to travel?
You: next friday
Bot: ✈️ Booked (pretend): 1 ticket from New York to Paris on 2026-10-09.
```

Flight bookings are pretend, and the weather reply is a placeholder. `on_get_weather` in `src/agent.py` marks where a weather API call would go.

## How the recognizer works

`src/recognizer.py` does, in miniature, what Azure AI Language (CLU) does:

1. **Entity extraction:** finds cities, dates and passenger counts, and gives each city a role from the word before it.
2. **Normalization:** replaces each entity with a placeholder, so "fly to paris" becomes "fly to @city".
3. **Intent scoring:** compares the remaining words with every example utterance in `INTENTS` using word overlap (the Dice coefficient). The best intent wins if it scores at least `INTENT_THRESHOLD` (0.5). A message made only of entities, like "Paris", has no intent of its own.

`recognize()` returns the same kind of result as a CLU prediction, so you can replace it with a call to CLU without changing the bot's handlers.

**Quick exercises** (for the full lab, see [LAB.md](LAB.md)):

- Add an example utterance to `INTENTS` and watch the `/debug` scores change.
- Add a city with synonyms to `CITIES`.
- Find phrasings the recognizer gets wrong, e.g. "I don't want to fly". They show why real services use trained models instead of word overlap.

## Run with Azure Bot Service

See [AZURE_README.md](AZURE_README.md) for the full walkthrough. In short:

1. Register an app in Microsoft Entra ID, then create an Azure Bot that uses it, and note the App ID, Tenant ID and client secret.
1. Rename `env.TEMPLATE` to `.env`, uncomment the three `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__*` lines and fill them in. When `CLIENTID` is set, anonymous access is turned off and every request must carry a valid token.
1. Start a tunnel with `devtunnel host -p 3978 --allow-anonymous`, and set the bot's **Messaging endpoint** to `{tunnel-url}/api/messages`.
1. Run `python -m src.main`, then use **Test in Web Chat** in the Azure portal.

## Code layout

| File | Contents |
| --- | --- |
| `src/agent.py` | The `AgentApplication`, intent routing and intent handlers |
| `src/recognizer.py` | The rule-based intent and entity recognizer, with its training data |
| `src/start_server.py` | aiohttp server hosting `/api/messages` |
| `src/main.py` | Logging setup and entry point |
| `tests/test_recognizer.py` | Unit tests for the recognizer |

`MemoryStorage` keeps conversation state in memory, so it's lost when the bot restarts. For production, use a persistent store such as Azure Blob or Cosmos DB storage.
