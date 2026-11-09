# vocab-bot

Vocab Bot is a French flashcard notebook that runs on your own computer. You can
start with the built-in decks, or make cards for things you come across in a
book or conversation. I built it so I could practise going both ways between
English and French, hear how things are said, and spend less time reviewing
words I already know.

## What you can do

- [x] Browse **2,287 French cards** by CEFR level or frequency. Pick a topic such as pronouns, travel or work and study it on its own.
- [x] Make a card by asking in your own words. Get a draft with examples, useful forms and recall questions, then ask for changes or save it to a local deck.
- [x] Study and test in either direction. Shuffle the cards or let the app pick a prompt language at random for each card.
- [x] Listen to French headwords, examples and forms, or paste your own text into **Pronounce text**.
- [x] Choose which decks to train on and disable individual cards you've mastered. You can enable them again with their review progress intact.
- [x] Schedule reviews based on how well you remembered each card, or practise without changing the schedule.
- [x] Work through a session with keyboard shortcuts, and switch between light and dark mode.

## Get started

You can browse, study and test the built-in cards with Python 3.12 and a
browser. You only need to set up an LLM if you want to make new cards.

### macOS and Linux

```sh
git clone https://github.com/dkjroot/vocab-bot.git
cd vocab-bot
python3.12 web_server.py
```

If your Python 3.12 installation provides `python3`, use that command in
place of `python3.12`.

### Windows (PowerShell)

```powershell
git clone https://github.com/dkjroot/vocab-bot.git
Set-Location vocab-bot
py -3.12 web_server.py
```

If Python 3.12 is on your PATH as `python`, you can use `python` in place
of `py -3.12` throughout the Windows instructions.

### Start studying

Open [Vocab Bot](http://localhost:8477) in your browser. Go to **Decks**, browse
a level and choose **Include in training** when you're ready. The published
decks are opt-in, so you can start with just one. Then open **Study** to reveal
translations or **Test** to type them from memory.

In Study, **R** reveals the answer and **N** moves to the next card. In Test,
press **Enter** to check your answer. Press **Enter** or **Space** again to take
the highlighted rating, or use **A**, **H** and **G** for Again, Hard and Got it.
The buttons show their shortcuts, and you can turn off letter shortcuts in
**Session options**.

## Make your own cards

You can use Gemini to draft cards on all three platforms. Get a Google AI
Studio API key, stop the server with **Ctrl+C** if it's running, and run the
commands for your system from the project directory. [Google AI Studio](https://aistudio.google.com/apikey)

### macOS and Linux (zsh or Bash)

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install google-genai
printf 'Google AI Studio API key: '
IFS= read -rs GEMINI_API_KEY
printf '\n'
export GEMINI_API_KEY
.venv/bin/python configure.py
```

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install google-genai
$key = Read-Host 'Google AI Studio API key' -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', $key).Password
Remove-Variable key
.\.venv\Scripts\python.exe configure.py
```

### Choose the engines and start the server

Choose `chat_engines.gemini_online` for the chat engine. For speech, choose
`tts_engines.macos_offline` on macOS. On Linux and Windows, you can select
`tts_engines.gTTS_online` to finish the wizard. The website uses an installed
browser voice on those platforms, so the gTTS package is only needed if you
use the separate command-line speech tools.

Start the server in the same terminal with `.venv/bin/python web_server.py`
on macOS or Linux, or `.\.venv\Scripts\python.exe web_server.py` in
PowerShell. You can change the model in `local-config.json`. If you start
the server in a new terminal, set the API key again there.

Try **Make a card** with a request like “Make me a card for *se faire* followed
by an infinitive.” Read the draft and listen to the examples before saving it.
You can ask for changes, such as adding a future-tense example. **Reading notes**
is your first local deck. Use **Decks** to create more and choose where each
draft goes.

### Use a different model server or voice

If you already have an OpenAI-compatible model server, install `openai` and
choose `chat_engines.openai_local` in `configure.py`. Set `OPENAI_BASE_URL` to
its API URL and edit the model in `local-config.json` to match. The default URL
is `http://localhost:8081/v1`. Set `OPENAI_API_KEY` if your server needs one.

On Linux and Windows, pronunciation depends on your browser exposing an
installed French speech voice. If the speaker buttons can't play anything,
check your system's speech or language settings for a French voice. On macOS
the built-in engine defaults to Thomas for French. To change it, run
`say -v '?'` to see the installed voices, then set `VOCAB_BOT_FR_VOICE`
to the name you want before starting the
server. Apple's licence covers how you can use audio generated with its voices.
[Apple's macOS licence](https://www.apple.com/legal/sla/)

## The published decks

| Deck | Cards | What you'll practise |
| --- | ---: | --- |
| A1 | 1,010 | Everyday verbs, pronouns, time, numbers, shopping and directions |
| A2 | 346 | Returns, holidays, housing, health, cooking, work and study |
| B1 | 555 | Job interviews, outings, relationships, culture, news and opinions |
| B2 | 325 | Meetings, evaluating evidence, argument, economics, climate and technology |

If you'd like to start with the words you're most likely to come across, go to
**Decks → Core frequency**. The first 2,000 ranks are all covered. Start with
the first 800 or 1,000 if you'd like a smaller set, and use the rank and topic
filters to browse a smaller group of cards. The 5,000 tier includes the cards
available so far beyond the first 2,000. You can
include a frequency tier alongside any French level. If a card appears in both,
you'll see it once per session and it keeps the same review schedule.

I used the Eaquals/CIEP French Core Inventory to choose vocabulary themes and
wrote the cards and examples for this project. The level labels are approximate.
You can see how much vocabulary the decks cover against the frequency list and
the Inventory's themes in the coverage report. [French Core Inventory](https://www.eaquals.org/wp-content/uploads/Inventaire_ONLINE_full.pdf) · [Deck coverage report](decks/COVERAGE.md)

## Where your data goes

The website listens on your own computer at `localhost:8477`. Saved cards and
review dates live in `data/flashcards.sqlite3`. To back up your deck, stop the
server and copy that file. Studying and testing saved cards use the local deck.
When you make or revise a draft, your request and any draft you're revising go
to the model server you've configured.

## Licence and support

I develop this project to be freely available to everyone, supported, if at all,
by voluntary contributions. Please keep this work freely available, credit its
origins, and point people to the official repository. If you'd like to support
my work directly, you can buy me a coffee. [Official repository](https://github.com/dkjroot/vocab-bot) · [Buy Me a Coffee](https://buymeacoffee.com/dkjroot)

That is a personal request. The GNU General Public License v3.0 permits
commercial use and redistribution, including forks, subject to its terms.
[GPLv3](LICENSE) · [Licensing details](LICENSING.md) · [Third-party credits](THIRD_PARTY_NOTICES.md)
