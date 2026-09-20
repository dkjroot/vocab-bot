# Reads the file 'words' and outputs the words in it that are useful to learn (helps prune the junk out of word lists!)
# When you have a hammer, everything looks like a nail, eh!  A small model should be able to cope with this task.
import os
import sys
import json

input_file = "words"
output_file = "words_pruned"
system_prompt = "Your job is to help curate a high-quality word list for French language learners.  We're processing a list of words, many of which are in the top 5000 most commonly used French words, however the list also contains some garbage and your job is to separate the two.  Approve only French words, do not approve punctuation characters if they appear alone, web addresses, email addresses etc. Don't disregard words that are also English - if they're used in French then they're acceptable."

if os.path.isfile('local-config.json'):
    config_file = 'local-config.json'
else:
    print(
        "Using the default (offline) configuration - consider running configure.py if you want to choose your options")
    config_file = 'local-config-default.json'
try:
    with open(config_file) as config_file_fh:
        settings = json.load(config_file_fh)
except Exception as e:
    print(f"Error loading config: {config_file}, {e}")
    exit(1)

# Load the chosen chat engine
import importlib
chat_engine = importlib.import_module(settings['chat engine'])
chat_inst = chat_engine.ChatEngine(settings, system_prompt)


def check(word):
    query = f'Is this word useful in our word list: "{word}".  Answer only "yes" or "no".'
    result = chat_inst.get_response(query)
    chat_inst.clear_conversation(system_prompt)
    if "YES" in result.upper():
        print(word)
        return word
    return None


# Main
if __name__ == "__main__":
    with open(input_file, 'r', encoding='utf-8') as in_file:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for line in in_file.readlines():
                if len(line.strip()) > 2: # Lets assume the student can figure out the meaning of all 1 and 2 letter words without our help!
                   checked = check(line.strip())
                   if checked:
                       out_file.write(f"{checked}\n")
