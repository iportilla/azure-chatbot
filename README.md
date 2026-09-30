# Azure Chatbot Lab: Intents and Entities

A hands-on lab (about 90 minutes) that teaches the core ideas behind conversational AI — **intents**, **entities**, and **slot filling** — by building a chatbot on the [Microsoft 365 Agents SDK](https://learn.microsoft.com/microsoft-365/agents-sdk/) for Python.

The bot uses a small rule-based recognizer, so it runs entirely offline with no Azure account or language service. Its results have the same shape as an Azure AI Language (CLU) prediction, so it can later be swapped for a real service without changing the bot's handlers. An optional final step connects the bot to **Azure Bot Service**.

## What's in this repository

| Folder | Purpose |
| --- | --- |
| [`simple-chatbot/`](simple-chatbot/README.md) | The **starting sample**: a travel bot (book flights, check weather) and the lab instructions in [LAB.md](simple-chatbot/LAB.md) |
| [`simple-chatbot-lab-solution/`](simple-chatbot-lab-solution/README.md) | The **finished solution**: a pizza-ordering bot, with checkpoint answers, an accuracy study, unit tests and notes for instructors |

## Learning objectives

By the end of the lab, students can:

- **Classify intents:** match a user message against labeled example utterances and pick the best-scoring intent, falling back to `None` below a confidence threshold.
- **Extract entities:** list entities with synonyms (`NYC` → New York), regex entities (dates, quantities), **roles** (origin vs. destination) and **resolution** (`next friday` → an ISO date).
- **Route on intent:** write one handler per intent.
- **Fill slots across turns:** ask follow-up questions for missing details and remember answers in conversation state.
- **Measure accuracy:** evaluate the recognizer on a held-out test set and reason about the trade-offs of tuning it.

## Lab outline

| Part | Activity | Time |
| --- | --- | --- |
| 0 | Set up and explore the starting bot | 15 min |
| 1 | Design your own bot (intents, entities, required details) | 10 min |
| 2 | Add your intents | 10 min |
| 3 | Add your entities | 15 min |
| 4 | Write the intent handlers and slot filling | 20 min |
| 5 | Measure and improve accuracy | 15 min |
| 6 | Reflect | 5 min |

The full step-by-step instructions are in [simple-chatbot/LAB.md](simple-chatbot/LAB.md).

## Prerequisites

- **Python 3.10 or newer** (`python3 --version`). The macOS built-in Python 3.9 is too old.
- **Node.js**, for the Microsoft 365 Agents Playground
- A code editor and basic Python knowledge
- *(Optional)* An Azure subscription, to connect the bot to Azure Bot Service

## Quick start

```bash
cd simple-chatbot
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

In a second terminal, start the Agents Playground to chat with the bot at `http://localhost:3978/api/messages`:

```bash
npm install -g @microsoft/teams-app-test-tool
teamsapptester
```

Type `/debug` in the chat to see the recognized intent, scores and entities for each message. Run the tests with `python -m unittest`.

To run the solution instead, do the same from `simple-chatbot-lab-solution/`, and also try `python evaluate.py` for the accuracy check.

## Deploying to Azure

Both folders include an [AZURE_README.md](simple-chatbot/AZURE_README.md) that walks through registering an app in Microsoft Entra ID, creating an Azure Bot, configuring `.env` from `env.TEMPLATE`, exposing the local bot with a dev tunnel, and testing it in Web Chat. It also covers the fix for the "AAD App Creation Failed" error.

> Never commit your `.env` file — it contains your bot's client secret. It is excluded by `.gitignore`.

## For instructors

The [solution README](simple-chatbot-lab-solution/README.md) contains answers to every checkpoint, a worked accuracy study (including why a higher score isn't always a better bot), reflection answers and common student mistakes. Ask students to complete the Part 0 installs before class to save about 10 minutes.

## Credits

Based on the Python samples in [microsoft/Agents](https://github.com/microsoft/Agents), licensed under the MIT License.
