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

if os.path.isfile('local-config.json'):
    config_file = 'local-config.json'
else:
    logger.info(
        "Using the default (offline) configuration - consider running configure.py if you want to choose your options")
    config_file = 'local-config-default.json'
try:
    with open(config_file) as config_file_fh:
        settings = json.load(config_file_fh)
except Exception as e:
    logger.exception(f"Error loading config: {config_file}")
    exit(1)

# Now we can load the various modules depending on what the user has configured...
import importlib
logger.info("Loading TTS library...")
tts_engine = importlib.import_module(settings['text to speech engine'])
tts_inst = tts_engine.TTS()
if len(sys.argv) > 1 and sys.argv[1] == "--test-tts":
    logger.info("Testing text to speech engine - you should hear a sentence in English and French")
    tts_inst.speak("This is a test of the text to speech engine", "en", "en_test_out.wav")
    tts_inst.speak("Ceci est un test du moteur de synthèse vocale", "fr", "fr_test_out.wav")
    exit()

# Now we can load the other stuff that can be a bit slower to load because we might be loading big model files
# depending on which module the user has chosen to use.

# Load the chosen chat engine
logger.info("Loading chat engine...")
chat_engine = importlib.import_module(settings['chat engine'])
chat_inst = chat_engine.ChatEngine(settings)

if len(sys.argv) > 1 and sys.argv[1] == "--test-llm":
    logger.info("Testing LLM - you should see a confirmation:")
    result = chat_inst.get_response("This is a test, please confirm you're working")
    logger.info(result)
    exit()


# Main
if __name__ == "__main__":
    try:
        user_input = "Where is Lesotho?"

        # Send the user input to the model and get the response
        result = chat_inst.get_response(user_input)

        # Print and say the response
        logger.info(result)
    except Exception:
        logger.exception("Exception")
        

