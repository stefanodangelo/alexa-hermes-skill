# -*- coding: utf-8 -*-
import logging
import requests
import json

import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

# Imports for progressive response
from ask_sdk_model.services.directive import Directive, SendDirectiveRequest, SpeakDirective, Header
from ask_sdk_model.services import ServiceClientFactory

# Import the DefaultApiClient for enabling API calls
from ask_sdk_core.api_client import DefaultApiClient

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TLDR_API_URL = "https://hermes-phi.vercel.app/tldr-news"

# --- LOCALIZED STRINGS DICTIONARY --
LOCALIZED_STRINGS = json.load(open("responses.json", "r", encoding="utf-8"))


# --- HELPER FUNCTION FOR LOCALIZATION ---
def get_localized_string(handler_input: HandlerInput, key: str, **kwargs) -> str:
    """
    Helper function to get localized string based on current locale.
    Allows for string formatting using kwargs.
    """
    locale = handler_input.request_envelope.request.locale
    api_language = locale.split('-')[0].lower()
    
    # Try to get the string for the specific locale
    locale_strings = LOCALIZED_STRINGS.get(locale, LOCALIZED_STRINGS[api_language])
    
    # Get the string, using a fallback default message if the key isn't found
    string_template = locale_strings.get(key, f"Missing translation for key: {key} in locale: {locale}")
    
    # Format the string with any provided keyword arguments
    try:
        return string_template.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing format key '{e}' in localized string for '{key}' in locale '{locale}'. String: '{string_template}'")
        return string_template # Return template if formatting fails


# --- REQUEST HANDLERS ---

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = get_localized_string(handler_input, "WELCOME_MESSAGE")
        reprompt_output = get_localized_string(handler_input, "WELCOME_REPROMPT")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_output)
                .response
        )

class LanguageCheckIntentHandler(AbstractRequestHandler):
    """Handler for Language Check Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("LanguageCheckIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        locale = handler_input.request_envelope.request.locale
        speak_output = get_localized_string(handler_input, "LANGUAGE_CHECK_MESSAGE", locale=locale)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class NewsRequestIntentHandler(AbstractRequestHandler):
    """Handler for News Request Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("NewsRequestIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("--- In NewsRequestIntentHandler handle ---")
        
        # Default speak_output, will be overwritten if successful
        speak_output = get_localized_string(handler_input, "NEWS_GENERAL_ERROR") 

        try:
            request = handler_input.request_envelope.request
            alexa_locale = handler_input.request_envelope.request.locale
            api_language = alexa_locale.split('-')[0].upper()
            
            logger.info(f"Detected intent name: {request.intent.name}")
            logger.info(f"Alexa locale: {alexa_locale}, API language: {api_language}")
            
            user_input_slot = request.intent.slots.get("userInput")

            if user_input_slot and user_input_slot.value:
                user_input = user_input_slot.value
                logger.info(f"Successfully extracted user input: '{user_input}'")

                response = requests.get(TLDR_API_URL, params={"query": user_input.strip(), "language": alexa_locale})

                if response.status_code == 200:
                    speak_output = response.text
                else:
                    logger.warning(f"TLDR API Error: Status Code {response.status_code}, Response: {response.text}")
                    speak_output = get_localized_string(handler_input, "NEWS_API_ERROR")
            else:
                if not user_input_slot:
                    speak_output = get_localized_string(handler_input, "NEWS_TOPIC_NOT_FOUND")
                    logger.warning("The 'userInput' slot was not found in the intent's slots.")
                else: # slot exists but value is empty
                    speak_output = get_localized_string(handler_input, "NEWS_TOPIC_NOT_CAUGHT")
                    logger.warning("userInput slot was found but its value was empty.")

        except Exception as e:
            speak_output = get_localized_string(handler_input, "NEWS_API_ERROR") # Use a general error message
            logger.exception(f"An unexpected error occurred in NewsRequestIntentHandler: {e}") 
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = get_localized_string(handler_input, "HELLO_WORLD_MESSAGE")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = get_localized_string(handler_input, "HELP_MESSAGE")
        reprompt_output = get_localized_string(handler_input, "HELP_REPROMPT")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = get_localized_string(handler_input, "GOODBYE_MESSAGE")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = get_localized_string(handler_input, "FALLBACK_MESSAGE")
        reprompt = get_localized_string(handler_input, "FALLBACK_REPROMPT")

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # Any cleanup logic goes here.
        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = get_localized_string(handler_input, "ERROR_MESSAGE")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(LanguageCheckIntentHandler())
sb.add_request_handler(NewsRequestIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()