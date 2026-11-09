"""dkjroot's vocab-bot

Given a list of vocab, generate audio and visual flashcards to aid memorisation of a foreign language.

"""

import argparse
import importlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
system_prompt = "You are an assistant helping an English speaker to produce flash cards to help them memorize their French vocabulary.  Answer precisely the question asked, do not add any padding or explanation.  Your output will be used to call an API so respond only with the requested JSON, no other text."


def load_settings():
    config_file = Path("local-config.json")
    if not config_file.is_file():
        logger.info("Using the default configuration. Run configure.py to choose your engines.")
        config_file = Path(__file__).with_name("local-config-default.json")
    with config_file.open(encoding="utf-8") as config:
        return json.load(config)


def test_tts(settings):
    engine = importlib.import_module(settings["text to speech engine"]).TTS()
    engine.speak("I would like to buy some bread.", "en", "en_test_out.wav")
    engine.speak("Je voudrais acheter du pain.", "fr", "fr_test_out.wav")


def get_definition(chat_inst, word):
    query = f'Give a very brief definition in English of the French word "{word}". This definition should be suitable for a beginning to intermediate student learning French. One to five words max. Answer in the form of a json formatted exactly like this: {{"word-fr": "acheter", "definition-en": "to buy"}}'
    result = chat_inst.get_response(query)
    logger.info(f"Definition of '{word}': {result}")
    # Hopefully the result is formatted: {"word-fr": "acheter", "definition-en": "to buy"}
    return result


def get_simple_sentences(chat_inst, word):
    query = f'Give one to three example sentences in French intended for beginners that use the word "{word}" (or a form of that word). Supply multiple examples only if it is important to show a distinction in different usages, or if there is something worthwhile to highlight.  If one is enough, return only one. Keep each sentence brief, just enough to hear the word in context. Answer in the form of a json array formatted exactly like this: ["sentence one", "sentence two"] (the list having one, two or three entries)'
    result = chat_inst.get_response(query)
    logger.info(f"Simple sentences for '{word}': {result}")
    # Response: ["sentence one", "sentence two"]
    return result


def get_intermediate_sentences(chat_inst, word):
    query = f'Give one to three example sentences in French intended for intermediate speakers that use the word "{word}" (or a form of that word). Supply multiple examples only if it is important to show a distinction in different usages, or if there is something worthwhile to highlight.  If one is enough, return only one. These sentences should be different from the beginner ones and show more advanced grammar.  Keep each sentence brief, just enough to hear the word in context. Answer in the form of a json array formatted exactly like this: ["sentence one", "sentence two"] (the list having one, two or three entries)'
    result = chat_inst.get_response(query)
    logger.info(f"Intermediate sentences for '{word}': {result}")
    # Response: ["sentence one", "sentence two"]
    return result


def get_forms(chat_inst, word):
    query = f'List all the forms the intermediate speaker might come across in conversational French of the word "{word}". Answer in the form of a json array formatted like this: [{{"French form one":"very brief English translation"}}, {{"French form two": "very brief English translation"}}] (the list being however long you need it to be).  In the brief English translation, be careful to use only English words (so write "they" instead of "ils" etc.) Be exhaustive, but focus on different sounds in spoken French, so that the learner can learn to hear this word in all the ways it will appear in spoken French.'

    result = chat_inst.get_response(query)
    logger.info(f"Forms of '{word}': {result}")
    # Response: ["form one", "form two"]
    return result


def make_card_for_word(chat_inst, word):
    get_definition(chat_inst, word)
    get_forms(chat_inst, word)


def main():
    parser = argparse.ArgumentParser(description="vocab-bot")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--test-tts", action="store_true", help="Play and save English and French samples")
    mode.add_argument("--test-llm", action="store_true", help="Ask the configured LLM for a sample definition")
    parser.add_argument("--word", default="manger", help="The French word to process")
    args = parser.parse_args()

    try:
        settings = load_settings()
        if args.test_tts:
            test_tts(settings)
        else:
            engine = importlib.import_module(settings["chat engine"])
            chat_inst = engine.ChatEngine(settings, system_prompt)
            if args.test_llm:
                definition = json.loads(get_definition(chat_inst, args.word))
                if not isinstance(definition, dict) or not all(
                    isinstance(definition.get(key), str) and definition[key].strip()
                    for key in ("word-fr", "definition-en")
                ):
                    raise ValueError("The LLM did not return the expected French word and English definition.")
            else:
                make_card_for_word(chat_inst, args.word)
    except Exception as error:
        logger.error("%s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
