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

A French vocabulary notebook for making flashcards and practising what you've learned.

Goals:

- [x] Port the plugin architecture from Iris so we can support multiple chat client APIs and TTS engines
- [ ] Acquire a dictionary of French words ordered by frequency of usage.
- [x] Ask the LLM for an English explanation of the word.
- [x] Ask the LLM for beginner and intermediate sentences using the word.
- [x] Ask the LLM about different written forms in which the word is likely to be seen.
- [x] Generate structured cards with examples, forms and recall questions.
- [ ] Use TTS to create a spoken summary of the above info (in French and English)
- [ ] Generate a flashcard image
- [x] Save cards and review dates in a local deck.
- [ ] Generate videos for upload to youtube
- [ ] Share the tools freely; invite voluntary support for development.




## Setup on a Mac with Gemini

If you've got a Google AI Studio API key, you can use Gemini for the vocabulary
prompts and let your Mac read the English and French aloud. Run these commands
from the project directory.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install google-genai
read -rs 'GEMINI_API_KEY?Google AI Studio API key: '
export GEMINI_API_KEY
python configure.py
```

The key prompt above is for zsh, the default shell on a Mac. You can get a key
from [Google AI Studio](https://aistudio.google.com/apikey). Choose
`chat_engines.gemini_online` and `tts_engines.macos_offline` in the setup menu.
You can change the Gemini model in `local-config.json`. The bot keeps the key in
your shell environment and sends your vocabulary prompts to Google's API.

The speech engine uses Daniel for UK English and Thomas for French as spoken in
France. Both run on your Mac. Use `say -v '?'` to see the names your Mac knows
about. To try another voice, download it through Accessibility in System
Settings and set `VOCAB_BOT_EN_VOICE` or `VOCAB_BOT_FR_VOICE` to its exact
name. Apple's system voices are for personal practice. See
[Apple's macOS licence](https://www.apple.com/legal/sla/) for the terms on using
the audio.

## Use the flashcard website

With the virtual environment active and your key exported, start the server.

```sh
python web_server.py
```

Open [the flashcard notebook](http://localhost:8477). I use **Make a card** to
capture whatever I've come across, from a single word to a request like “Make
me a card for *se faire* followed by an infinitive”. Read the draft and listen
to the examples, then ask for changes or save it to your deck. Gemini writes
the draft from your request, so it's worth checking the French before you
save it.

Open **Decks** to browse 746 French vocabulary cards across A1, A2, B1 and B2.
Each has a French example, an English translation and a recall prompt. I used
Annex E of the freely available Eaquals/CIEP French Core Inventory to choose
themes and useful things to practise at each level. The words, examples and
level assignments are my selection. [French Core Inventory](https://www.eaquals.org/wp-content/uploads/Inventaire_ONLINE_full.pdf)

| Deck | Cards | What you'll practise |
| --- | ---: | --- |
| A1 | 237 | Everyday verbs, pronouns, time, numbers, shopping and directions |
| A2 | 166 | Returns, holidays, housing, health, cooking, work and study |
| B1 | 170 | Job interviews, outings, relationships, culture, news and opinions |
| B2 | 173 | Meetings, evaluating evidence, argument, economics, climate and technology |

Each published deck is grouped by topic. Pick a topic to narrow the list, or
choose **Study topic** to study its enabled cards from your training suite.

The decks cover selected vocabulary and expressions. The Inventory also covers
grammar, communication and other skills you'll need alongside the cards.
The [deck coverage report](decks/COVERAGE.md) tracks frequent words and Annex E
vocabulary themes separately.

Include the decks you want to train on. **Reading notes** is the default local
deck, and you can create others and choose where to save each draft. If a card
is already second nature, disable it from its card page or after answering in
Test. You can enable it again later and pick up with its existing review progress.

- **Study** shows a cue first. Try to say the translation, then reveal the
  card to read and hear the examples and forms.
- **Test** asks you to write the translation. It compares your answer with the
  suggested answers and leaves the final judgement to you. Rate your recall
  to schedule the next review, or choose **Practise all cards** for a round
  that leaves your schedule alone.
- In either mode, tick **Shuffle cards** to mix up the order. Choose which
  language to see first under **Prompt in**. With both selected, the app picks
  a direction for each new card.
- The underlined letters are shortcuts. In Study, use **R** to reveal, **N**
  for next, **P** for previous and **H** to hide. In Test, press Enter to
  check your answer. Press Enter or Space again for the highlighted rating,
  or use **A**, **H** or **G** to choose one. You can turn
  off **Letter shortcuts** in the session options.
- Use a speaker button beside the French or paste any French text into
  **Pronounce text**. You can switch between light and dark mode in the sidebar.

The server listens on this computer only. Saved cards and review dates live in
`data/flashcards.sqlite3`. You can back up that file after stopping the server.
Draft requests and any draft you ask to revise go to your configured LLM.
Studying and testing saved cards use the local deck.

## Other setups

For an OpenAI-compatible server, install `openai` and choose
`chat_engines.openai_local`. Set `OPENAI_BASE_URL` to your server's API URL
and edit `model` in `local-config.json` to match the model your server offers.
The default URL is `http://localhost:8081/v1`. Set `OPENAI_API_KEY` if the
server asks for a key.

For online speech with gTTS, install `gTTS` and `pydub` as well as FFmpeg.
The Coqui option uses PyTorch, Coqui TTS and `pydub` with separately
downloaded models. See [the model credits and terms](THIRD_PARTY_NOTICES.md)
before using that option.

## Test the command-line setup

```sh
python vocab-bot.py --test-llm
python vocab-bot.py --test-tts
```

The LLM test asks for a sample definition. The speech test plays a sentence in
each language and saves `en_test_out.wav` and `fr_test_out.wav` so you can
listen again.

# You'll need a word list

I got one from here, https://wortschatz.uni-leipzig.de/en/download/French, trimmed the numbers out of it, then ran the wordlist-pruner.py on it to weed out the junk.


# Run it

```
python vocab-bot.py --word acheter
```

This prints an English definition and a list of French forms in the terminal.
