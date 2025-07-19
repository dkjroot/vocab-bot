# vocab-bot
An LLM to make a vocabulary builder

Goals:

- [ ] Acquire a dictionary of French words ordered by frequency of usage.
- [ ] Ask the LLM for an English explanation of the word.
- [ ] Ask the LLM for beginner and intermediate sentences using the word.
- [ ] Ask the LLM about different written forms in which the word is likely to be seen.
- [ ] Format the result into a consistent JSON 
- [ ] Use TTS to create a spoken summary of the above info (in French and English)
- [ ] Generate a flashcard image
- [ ] Store the word, its JSON and audio sample in a structure that promotes easy use
- [ ] Generate videos for upload to youtube
- [ ] Profit!




# Setup

```
python3.12 -m venv ./venv
source venv/bin/activate
```

Then optionally...

```
pip install -r requirements.txt
```

But beware this will install everything for all the modules and that will include a lot of huge files you won't need if you're not using local models.  If I was you I'd be inclined to configure it the way I want it, then pip install what it turns out to need in that configuration.

Finally:

```
source dev.env
python configure.py
```


## Module-specific  

If you're using the meloplus TTS engine you need to run unidic download:

```
pip install melotts-plus
python -m unidic download
```

# Test your setup:

```
python vocab-bot --test-tts
python vocab-bot --test-llm
```

# Run it

```
python vocab-bot.py
```
