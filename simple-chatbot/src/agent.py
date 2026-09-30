# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import sys
import traceback
from datetime import date
from dotenv import load_dotenv

from os import environ
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

from .recognizer import RecognizerResult, recognize

load_dotenv()
if not environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"):
    # No Azure Bot credentials: run in local anonymous mode (Agents Playground).
    environ.setdefault("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED", "true")
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)
AUTH_CONFIGURATION = CONNECTION_MANAGER.get_default_connection_configuration()

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)

HELP_TEXT = (
    "I understand a few **intents** and pick out **entities** (cities, dates, passenger counts). Try:\n\n"
    "- **Greeting:** \"hello\", \"good morning\"\n"
    "- **BookFlight:** \"book a flight from NYC to Paris tomorrow\", \"I need 2 tickets to Tokyo next friday\"\n"
    "- **GetWeather:** \"what's the weather in London\", \"is it raining in Seattle today?\"\n"
    "- **Cancel:** \"never mind\"\n"
    "- **Help:** \"what can you do?\"\n\n"
    "Type **/debug** to see what the recognizer found in each message."
)

# Details a flight booking needs, and the question to ask when one is missing.
BOOKING_SLOTS = {
    "destination": "Where would you like to fly to?",
    "date": "What date do you want to travel?",
}

BOOKING = "ConversationState.booking"
DEBUG = "ConversationState.debug"


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    for member in context.activity.members_added or []:
        if member.id != context.activity.recipient.id:
            await context.send_activity(f"Welcome to the Simple Chatbot! 🚀\n\n{HELP_TEXT}")
    return True


@AGENT_APP.message("/help")
async def on_help_command(context: TurnContext, _state: TurnState):
    await context.send_activity(HELP_TEXT)


@AGENT_APP.message("/debug")
async def on_debug(context: TurnContext, state: TurnState):
    debug = not state.get_value(DEBUG, lambda: False)
    state.set_value(DEBUG, debug)
    await context.send_activity(f"Debug output is {'on' if debug else 'off'}.")


# --- Intent handlers --------------------------------------------------------


async def on_greeting(context: TurnContext, _state: TurnState, _result: RecognizerResult):
    name = context.activity.from_property.name if context.activity.from_property else None
    await context.send_activity(f"Hello{', ' + name if name else ''}! 👋 Ask me to book a flight or check the weather.")


async def on_help(context: TurnContext, _state: TurnState, _result: RecognizerResult):
    await context.send_activity(HELP_TEXT)


async def on_book_flight(context: TurnContext, state: TurnState, result: RecognizerResult):
    # Slot filling: merge what this message provides into the booking in progress.
    booking = state.get_value(BOOKING, dict)
    for slot, categories in (
        ("origin", ("origin",)),
        ("destination", ("destination", "location")),
        ("date", ("date",)),
        ("passengers", ("passengers",)),
    ):
        value = result.get(*categories)
        if value is not None:
            booking[slot] = value

    # A city with no "from"/"to" in front of it fills whichever city is missing.
    city = result.get("city")
    if city is not None:
        booking.setdefault("destination" if "destination" not in booking else "origin", city)

    missing = [slot for slot in BOOKING_SLOTS if slot not in booking]
    if missing:
        # Remember which question we asked. This also keeps the saved booking from
        # being empty, which the SDK would treat the same as "no booking".
        booking["asking_for"] = missing[0]
        state.set_value(BOOKING, booking)
        await context.send_activity(BOOKING_SLOTS[missing[0]])
        return

    state.delete_value(BOOKING)
    passengers = booking.get("passengers", 1)
    origin = f" from {booking['origin']}" if "origin" in booking else ""
    await context.send_activity(
        f"✈️ Booked (pretend): {passengers} ticket{'s' if passengers != 1 else ''}"
        f"{origin} to {booking['destination']} on {booking['date']}."
    )


async def on_get_weather(context: TurnContext, _state: TurnState, result: RecognizerResult):
    city = result.get("location", "city", "destination")
    if city is None:
        await context.send_activity("Which city? For example: \"what's the weather in Paris\".")
        return
    when = result.get("date") or date.today().isoformat()
    # A real bot would call a weather API here.
    await context.send_activity(f"🌤️ I'd look up the weather in {city} for {when} here. (Connect a weather API in on_get_weather.)")


async def on_cancel(context: TurnContext, state: TurnState, _result: RecognizerResult):
    state.delete_value(BOOKING)
    await context.send_activity("OK, cancelled. What else can I do for you?")


async def on_none(context: TurnContext, _state: TurnState, _result: RecognizerResult):
    await context.send_activity("Sorry, I didn't understand that. Type **help** to see what I can do.")


INTENT_HANDLERS = {
    "Greeting": on_greeting,
    "Help": on_help,
    "BookFlight": on_book_flight,
    "GetWeather": on_get_weather,
    "Cancel": on_cancel,
    "None": on_none,
}


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    result = recognize(context.activity.text or "")

    if state.get_value(DEBUG, lambda: False):
        await context.send_activity(f"```json\n{json.dumps(result.to_dict(), indent=2)}\n```")

    intent = result.intent
    # While a booking is waiting for details, a reply like "Paris" or "tomorrow"
    # has no intent of its own: treat it as an answer to the booking question.
    if intent == "None" and result.entities and state.get_value(BOOKING, lambda: None):
        intent = "BookFlight"

    await INTENT_HANDLERS[intent](context, state, result)


@AGENT_APP.error
async def on_error(context: TurnContext, error: Exception):
    # NOTE: In production, consider logging this to Azure Application Insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    await context.send_activity("The bot encountered an error or bug.")
