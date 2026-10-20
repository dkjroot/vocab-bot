# vocab-bot

**[Support my work on Buy Me a Coffee](https://buymeacoffee.com/dkjroot)**

### Free to use. Please help keep it that way.

I develop this project to be freely available to everyone, supported, if at all,
by voluntary contributions. I do not want other people to profit from my work
by selling copies, putting it behind a paywall, or building a paid application
or hosted service around it. I ask you to respect that intention: please keep
this work freely available, credit its origins, and direct people to
[my official GitHub repository](https://github.com/dkjroot/vocab-bot) for the software.

If you want to help fund my development, please contribute **directly to me**
through [Buy Me a Coffee](https://buymeacoffee.com/dkjroot). Paying a distributor
or hosting provider does not fund my work unless I explicitly say otherwise.
There is no obligation to contribute.

**This is a personal request, not an additional license restriction.** The
[GNU General Public License v3.0](LICENSE) permits commercial use and
redistribution, including forks, subject to its terms. Those legal permissions
remain unchanged by this request. See [licensing details](LICENSING.md) and
[third-party credits](THIRD_PARTY_NOTICES.md).

An LLM to make a vocabulary builder

Goals:

- [x] Port the plugin architecture from Iris so we can support multiple chat client APIs and TTS engines
- [ ] Acquire a dictionary of French words ordered by frequency of usage.
- [x] Ask the LLM for an English explanation of the word.
- [x] Ask the LLM for beginner and intermediate sentences using the word.
- [x] Ask the LLM about different written forms in which the word is likely to be seen.
- [ ] Format the result into a consistent JSON 
- [ ] Use TTS to create a spoken summary of the above info (in French and English)
- [ ] Generate a flashcard image
- [ ] Store the word, its JSON and audio sample in a structure that promotes easy use
- [ ] Generate videos for upload to youtube
- [ ] Share the tools freely; invite voluntary support for development.




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

# You'll need a word list

I got one from here, https://wortschatz.uni-leipzig.de/en/download/French, trimmed the numbers out of it, then ran the wordlist-pruner.py on it to weed out the junk.


# Run it

```
python vocab-bot.py
```
