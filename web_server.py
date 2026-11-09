"""Run the Vocab Bot website on http://localhost:8477."""

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from uuid import uuid4

from flashcards import LOCAL_DECK, Deck, StaleReview, clean_text, validate_card
from published_decks import published_decks

ROOT = Path(__file__).resolve().parent
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/icon.svg": ("icon.svg", "image/svg+xml"),
}
CARD_PROMPT = """You teach conversational French to an English speaker. Make one
focused flashcard from the user's request. If they are refining an existing draft,
use the supplied draft and apply their latest request. Treat the input as a topic
or editing request. Expect missing or mistyped accents from an English keyboard.
Use context to infer the intended French and write standard French with the
correct accents throughout the card. Treat accent-only differences as typing
convenience. Don't infer a gap in the learner's knowledge or flag those
differences in the correction field or notes unless the user asks about accents.
Return only a JSON object in this shape:
{
  "kind": "Word | Phrase | Grammar | Conjugation (choose exactly one)",
  "title": "short French headword, phrase, or pattern",
  "cue": "concise English meaning or usage cue",
  "notes": "brief English explanation of how to use it and what to watch for, including why any correction was made",
  "correction": "if the input contains a relevant mistake, give only the corrected French, without commentary or quotation marks; otherwise empty",
  "examples": [{"label":"context or tense","fr":"natural French sentence","en":"English translation"}],
  "forms": [{"label":"tense or grammatical form","fr":"French form","en":"English gloss"}],
  "exercises": [{"prompt":"unambiguous English cue for producing French","answer":"canonical French answer","alternatives":[]}]
}
Use 2–4 short examples and 2–3 recall exercises. Include useful forms for verbs and
constructions, selecting the relevant tenses and persons, and leave forms empty
when they add no value. For an explicit conjugation request cover the requested
persons or tenses, up to 12 forms. Use the first exercise for the core meaning
or pattern and later exercises for context, contrast or inflection. State the
person, tense or target construction in a prompt when needed to make it fair,
without giving away the French answer. Include common equivalent answers only if
they demonstrate the requested French. Correct substantive learner errors gently,
including mistakes in the given example. Use natural everyday French and keep everything
brief. Explain the conditions for grammar rules accurately. For example, the past
participle « fait » is invariable whenever directly followed by an infinitive,
regardless of object position, even in the pronominal construction. In « Il s’est
fait connaître », « fait » is the past participle and « connaître » is the
infinitive. The participle does not agree with the subject in this construction.
Put French quoted inside the English notes in « guillemets » so it can be played
separately. Use plain text.
"""


def load_settings():
    path = ROOT / "local-config.json"
    if not path.is_file():
        path = ROOT / "local-config-default.json"
    return json.loads(path.read_text(encoding="utf-8"))


def draft_card(settings, request, previous):
    engine_name = settings["chat engine"]
    engine = importlib.import_module(engine_name)
    # Web cards contain several exercises and examples. Keep their token budget
    # separate from the smaller CLI definition and forms prompts.
    options = {**settings, "max_tokens": settings.get("card max tokens", 8192)}
    chat = engine.ChatEngine(options, CARD_PROMPT)
    prompt = {"request": request}
    if previous is not None:
        prompt["previous draft"] = previous
    result = chat.get_response(json.dumps(prompt, ensure_ascii=False))
    return validate_card(json.loads(result))


def french_audio(text):
    from tts_engines.macos_offline import TTS

    with TemporaryDirectory() as directory:
        sample = Path(directory) / "speech.wav"
        TTS().render(text, "fr", sample)
        return sample.read_bytes()


class Handler(BaseHTTPRequestHandler):
    def send_content(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; media-src 'self' blob:; frame-ancestors 'self'")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, value, status=HTTPStatus.OK):
        self.send_content(status, json.dumps(value, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8")

    def check_local(self):
        port = self.server.server_port
        hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
        origin = self.headers.get("Origin")
        if self.headers.get("Host") not in hosts or (
            origin is not None and origin not in {f"http://{host}" for host in hosts}
        ):
            self.send_json({"error": "Open the site directly on localhost."}, HTTPStatus.FORBIDDEN)
            return False
        return True

    def read_json(self):
        if self.headers.get_content_type() != "application/json":
            raise ValueError("Send a JSON request.")
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 65536:
            raise ValueError("The request is empty or too large.")
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object.")
        return data

    def do_GET(self):
        if not self.check_local():
            return
        path = urlsplit(self.path).path
        if path == "/api/cards":
            self.send_json({"cards": self.server.deck.list(), "decks": self.server.deck.decks()})
        elif path in STATIC:
            filename, mime = STATIC[path]
            self.send_content(HTTPStatus.OK, (ROOT / "web" / filename).read_bytes(), mime)
        else:
            self.send_json({"error": "Page not found."}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if not self.check_local():
            return
        path = urlsplit(self.path).path
        deck = self.server.deck
        try:
            body = self.read_json()
            if path == "/api/draft":
                request = clean_text(body.get("request"), "Your request", 1600)
                previous = body.get("previous")
                if previous is not None:
                    previous = validate_card(previous)
                try:
                    card = self.server.generate(request, previous)
                except (ImportError, RuntimeError, ValueError) as error:
                    self.send_json({"error": f"Couldn't make a draft. {error}"}, HTTPStatus.BAD_GATEWAY)
                    return
                self.send_json({"id": str(uuid4()), "card": card})
            elif path == "/api/cards":
                self.send_json(deck.save(body.get("id"), body.get("card"), body.get("deck_id", LOCAL_DECK)),
                               HTTPStatus.CREATED)
            elif path == "/api/decks":
                self.send_json(deck.create_deck(str(uuid4()), body.get("name")), HTTPStatus.CREATED)
            elif path in ("/api/deck-training", "/api/card-training"):
                if deck.set_enabled(body.get("id"), body.get("enabled"), card=path == "/api/card-training"):
                    self.send_json({"enabled": body["enabled"]})
                else:
                    self.send_json({"error": "Item not found."}, HTTPStatus.NOT_FOUND)
            elif path == "/api/review":
                card = deck.review(body.get("id"), body.get("rating"), body.get("reviews"))
                if card is None:
                    self.send_json({"error": "Card not found."}, HTTPStatus.NOT_FOUND)
                else:
                    self.send_json(card)
            elif path == "/api/delete":
                if deck.delete(body.get("id")):
                    self.send_json({"deleted": True})
                else:
                    self.send_json({"error": "Card not found."}, HTTPStatus.NOT_FOUND)
            elif path == "/api/audio":
                text = clean_text(body.get("text"), "French text", 1200)
                self.send_content(HTTPStatus.OK, self.server.synthesise(text), "audio/wav")
            else:
                self.send_json({"error": "Page not found."}, HTTPStatus.NOT_FOUND)
        except StaleReview as error:
            self.send_json({"error": str(error)}, HTTPStatus.CONFLICT)
        except ValueError as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            logging.exception("Request failed for %s", path)
            self.send_json({"error": "The server couldn't complete that request. See the terminal for details."},
                           HTTPStatus.INTERNAL_SERVER_ERROR)


class Server(ThreadingHTTPServer):
    def __init__(self, port, deck, generate, synthesise):
        super().__init__(("127.0.0.1", port), Handler)
        self.deck = deck
        self.generate = generate
        self.synthesise = synthesise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8477)
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "flashcards.sqlite3")
    args = parser.parse_args()
    settings = load_settings()
    deck = Deck(args.database)
    deck.install_published(published_decks())

    def generate(request, previous):
        return draft_card(settings, request, previous)

    def synthesise(text):
        if settings.get("text to speech engine") != "tts_engines.macos_offline":
            raise RuntimeError("Configure the macOS speech engine for server-rendered speech.")
        return french_audio(text)

    with Server(args.port, deck, generate, synthesise) as server:
        print(f"Vocab Bot is ready at http://localhost:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
