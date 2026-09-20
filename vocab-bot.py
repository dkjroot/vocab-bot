"""dkjroot's vocab-bot

Given a list of vocab, generate audio and visual flashcards to aid memorisation of a foreign language.

"""

# To reduce the amount of things we need to load, as some of the models are very big, and because we don't want to
# even load modules that can go online if we're in offline mode, we'll load the config first and then load the rest of
# the dependencies dynamically based on the config.
import os
import sys
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
system_prompt = "You are an assistant helping an English speaker to produce flash cards to help them memorize their French vocabulary.  Answer precisely the question asked, do not add any padding or explanation.  Your output will be used to call an API so respond only with the requested JSON, no other text."

if os.path.isfile("local-config.json"):
    config_file = "local-config.json"
else:
    logger.info(
        "Using the default (offline) configuration - consider running configure.py if you want to choose your options"
    )
    config_file = "local-config-default.json"
try:
    with open(config_file) as config_file_fh:
        settings = json.load(config_file_fh)
except Exception as e:
    logger.exception(f"Error loading config: {config_file}")
    exit(1)

# Now we can load the various modules depending on what the user has configured...
import importlib

logger.info("Loading TTS library...")
tts_engine = importlib.import_module(settings["text to speech engine"])
tts_inst = tts_engine.TTS()
if len(sys.argv) > 1 and sys.argv[1] == "--test-tts":
    logger.info(
        "Testing text to speech engine - you should hear a sentence in English and French"
    )
    tts_inst.speak(
        "This is a test of the text to speech engine", "en", "en_test_out.wav"
    )
    tts_inst.speak(
        "Ceci est un test du moteur de synthèse vocale", "fr", "fr_test_out.wav"
    )
    exit()

# Now we can load the other stuff that can be a bit slower to load because we might be loading big model files
# depending on which module the user has chosen to use.

# Load the chosen chat engine
logger.info("Loading chat engine...")
chat_engine = importlib.import_module(settings["chat engine"])
chat_inst = chat_engine.ChatEngine(settings, system_prompt)

if len(sys.argv) > 1 and sys.argv[1] == "--test-llm":
    logger.info("Testing LLM - you should see a confirmation:")
    result = chat_inst.get_response("This is a test, please confirm you're working")
    logger.info(result)
    exit()


def get_definition(word):
    query = f'Give a very brief definition in English of the French word "{word}". This definition should be suitable for a beginning to intermediate student learning French. One to five words max. Answer in the form of a json formatted exactly like this: {{"word-fr": "acheter", "definition-en": "to buy"}}'
    result = chat_inst.get_response(query)
    logger.info(f"Definition of '{word}': {result}")
    # Hopefully the result is formatted: {"word-fr": "acheter", "definition-en": "to buy"}
    return result


def get_simple_sentences(word):
    query = f'Give one to three example sentences in French intended for beginners that use the word "{word}" (or a form of that word). Supply multiple examples only if it is important to show a distinction in different usages, or if there is something worthwhile to highlight.  If one is enough, return only one. Keep each sentence brief, just enough to hear the word in context. Answer in the form of a json array formatted exactly like this: ["sentence one", "sentence two"] (the list having one, two or three entries)'
    result = chat_inst.get_response(query)
    logger.info(f"Simple sentences for '{word}': {result}")
    # Response: ["sentence one", "sentence two"]
    return result


def get_intermediate_sentences(word):
    query = f'Give one to three example sentences in French intended for intermediate speakers that use the word "{word}" (or a form of that word). Supply multiple examples only if it is important to show a distinction in different usages, or if there is something worthwhile to highlight.  If one is enough, return only one. These sentences should be different from the beginner ones and show more advanced grammar.  Keep each sentence brief, just enough to hear the word in context. Answer in the form of a json array formatted exactly like this: ["sentence one", "sentence two"] (the list having one, two or three entries)'
    result = chat_inst.get_response(query)
    logger.info(f"Intermediate sentences for '{word}': {result}")
    # Response: ["sentence one", "sentence two"]
    return result


def get_forms(word):
    query = f'List all the forms the intermediate speaker might come across in conversational French of the word "{word}". Answer in the form of a json array formatted like this: [{{"French form one":"very brief English translation"}}, {{"French form two": "very brief English translation"}}] (the list being however long you need it to be).  In the brief English translation, be careful to use only English words (so write "they" instead of "ils" etc.) Be exhaustive, but focus on different sounds in spoken French, so that the learner can learn to hear this word in all the ways it will appear in spoken French.'

    result = chat_inst.get_response(query)
    logger.info(f"Forms of '{word}': {result}")
    # Response: ["form one", "form two"]
    return result


def make_card_for_word(word):
    definition = get_definition(word)
    forms = get_forms(word)


#    simple_sentences = get_simple_sentences(word)
#    intermediate_sentences = get_intermediate_sentences(word)


# Main
if __name__ == "__main__":
    try:
        word = "manger"
        make_card_for_word(word)

    except Exception:
        logger.exception("Exception")
