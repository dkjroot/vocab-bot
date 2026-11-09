"""Card validation and the local SQLite deck."""

from contextlib import closing, contextmanager
import json
from pathlib import Path
import sqlite3
import time
from uuid import UUID

KINDS = ("Word", "Phrase", "Grammar", "Conjugation")
RATINGS = ("again", "hard", "got-it")
INTERVALS = (1, 3, 7, 14, 30)
DAY = 86400
LOCAL_DECK = "reading"


class StaleReview(ValueError):
    """The card has changed since the review was opened."""


def clean_text(value, label, limit, optional=False):
    if isinstance(value, str):
        value = value.strip()
        if (value or optional) and len(value) <= limit and "\x00" not in value:
            return value
    raise ValueError(f"{label} must be text of up to {limit} characters.")


def rows(value, label, limit, minimum=0):
    if not isinstance(value, list) or not minimum <= len(value) <= limit:
        raise ValueError(f"{label} must contain between {minimum} and {limit} entries.")
    if any(not isinstance(item, dict) for item in value):
        raise ValueError(f"Each entry in {label.lower()} must be an object.")
    return value


def validate_card(value):
    if not isinstance(value, dict):
        raise ValueError("The card must be an object.")
    kind = value.get("kind")
    if kind not in KINDS:
        raise ValueError("Choose a valid card type.")
    examples = []
    for row in rows(value.get("examples"), "Examples", 6, minimum=1):
        examples.append({
            "label": clean_text(row.get("label", ""), "Example label", 70, optional=True),
            "fr": clean_text(row.get("fr"), "French example", 300),
            "en": clean_text(row.get("en"), "English translation", 300),
        })
    forms = []
    for row in rows(value.get("forms", []), "Forms", 12):
        forms.append({
            "label": clean_text(row.get("label"), "Form label", 70),
            "fr": clean_text(row.get("fr"), "French form", 300),
            "en": clean_text(row.get("en", ""), "English gloss", 300, optional=True),
        })
    exercises = []
    for row in rows(value.get("exercises"), "Exercises", 5, minimum=1):
        alternatives = row.get("alternatives", [])
        if not isinstance(alternatives, list) or len(alternatives) > 4:
            raise ValueError("An exercise can have up to four alternative answers.")
        exercises.append({
            "prompt": clean_text(row.get("prompt"), "Recall prompt", 350),
            "answer": clean_text(row.get("answer"), "French answer", 300),
            "alternatives": [clean_text(a, "Alternative answer", 300) for a in alternatives],
        })
    return {
        "kind": kind,
        "title": clean_text(value.get("title"), "French headword or phrase", 100),
        "cue": clean_text(value.get("cue"), "English cue", 240),
        "notes": clean_text(value.get("notes", ""), "Usage notes", 1200, optional=True),
        "correction": clean_text(value.get("correction", ""), "Correction", 450, optional=True),
        "examples": examples,
        "forms": forms,
        "exercises": exercises,
    }


def card_id(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid card ID.") from None


class Deck:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY, content TEXT NOT NULL,
                created_at INTEGER NOT NULL, due_at INTEGER NOT NULL,
                stage INTEGER NOT NULL DEFAULT 0, reviews INTEGER NOT NULL DEFAULT 0,
                exercise_index INTEGER NOT NULL DEFAULT 0
            )""")
            columns = {row["name"] for row in db.execute("PRAGMA table_info(cards)")}
            if "exercise_index" not in columns:
                db.execute("ALTER TABLE cards ADD COLUMN exercise_index INTEGER NOT NULL DEFAULT 0")
            if "deck_id" not in columns:
                db.execute("ALTER TABLE cards ADD COLUMN deck_id TEXT NOT NULL DEFAULT 'reading'")
            if "enabled" not in columns:
                db.execute("ALTER TABLE cards ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1")
            db.execute("""CREATE TABLE IF NOT EXISTS decks (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
                published INTEGER NOT NULL DEFAULT 0, enabled INTEGER NOT NULL DEFAULT 1
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS card_collections (
                card_id TEXT NOT NULL REFERENCES cards(id), deck_id TEXT NOT NULL REFERENCES decks(id),
                PRIMARY KEY (card_id, deck_id)
            )""")
            db.execute("INSERT OR IGNORE INTO decks (id, name) VALUES (?, ?)", (LOCAL_DECK, "Reading notes"))

    @contextmanager
    def connection(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    @staticmethod
    def unpack(row, memberships=()):
        data = dict(row)
        data.update(json.loads(data.pop("content")))
        data["deck_ids"] = [row["deck_id"], *memberships]
        return data

    def list(self):
        with self.connection() as db:
            db.execute("BEGIN")
            memberships = {}
            for row in db.execute("SELECT card_id, deck_id FROM card_collections ORDER BY deck_id"):
                memberships.setdefault(row["card_id"], []).append(row["deck_id"])
            return [
                self.unpack(row, memberships.get(row["id"], ()))
                for row in db.execute("SELECT * FROM cards ORDER BY created_at DESC, rowid DESC")
            ]

    def decks(self):
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                """SELECT * FROM decks ORDER BY published, id LIKE 'core-%',
                    CASE WHEN id LIKE 'core-%' THEN CAST(substr(id, 6) AS INTEGER) END,
                    CASE WHEN published THEN id ELSE lower(name) END"""
            )]

    def create_deck(self, identifier, name):
        identifier = card_id(identifier)
        name = clean_text(name, "Deck name", 60)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM decks WHERE published = 0 AND name = ? COLLATE NOCASE", (name,)).fetchone():
                raise ValueError("You already have a local deck with that name.")
            db.execute("INSERT INTO decks (id, name) VALUES (?, ?)", (identifier, name))
            return dict(db.execute("SELECT * FROM decks WHERE id = ?", (identifier,)).fetchone())

    def install_published(self, decks):
        decks = list(decks)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            now = int(time.time())
            for deck in decks:
                db.execute("""INSERT INTO decks (id, name, description, published, enabled)
                    VALUES (?, ?, ?, 1, 0)
                    ON CONFLICT(id) DO UPDATE SET name = excluded.name, description = excluded.description""",
                    (deck["id"], deck["name"], deck["description"]))
            for deck in decks:
                for identifier, card in deck["cards"]:
                    content = validate_card(card)
                    if "topic" in card:
                        content["topic"] = clean_text(card["topic"], "Topic", 100)
                    for key in ("frequency_rank", "source_level"):
                        if key in card:
                            content[key] = card[key]
                    db.execute("""INSERT INTO cards (id, content, created_at, due_at, deck_id)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET content = excluded.content
                        WHERE cards.content <> excluded.content""",
                        (identifier, json.dumps(content, ensure_ascii=False, sort_keys=True),
                         now, now, deck["id"]))
            for deck in decks:
                db.execute("DELETE FROM card_collections WHERE deck_id = ?", (deck["id"],))
                for identifier in deck.get("members", ()):
                    db.execute("""INSERT INTO card_collections (card_id, deck_id)
                        SELECT id, ? FROM cards WHERE id = ? AND deck_id <> ?""",
                        (deck["id"], identifier, deck["id"]))

    def set_enabled(self, identifier, enabled, *, card=False):
        if type(enabled) is not bool:
            raise ValueError("Choose whether this item is included in training.")
        identifier = card_id(identifier) if card else clean_text(identifier, "Deck ID", 60)
        table = "cards" if card else "decks"
        with self.connection() as db:
            return db.execute(f"UPDATE {table} SET enabled = ? WHERE id = ?", (enabled, identifier)).rowcount == 1

    def save(self, identifier, value, deck_id=LOCAL_DECK):
        identifier = card_id(identifier)
        deck_id = clean_text(deck_id, "Deck ID", 60)
        content = json.dumps(validate_card(value), ensure_ascii=False, sort_keys=True)
        now = int(time.time())
        with self.connection() as db:
            deck = db.execute("SELECT published FROM decks WHERE id = ?", (deck_id,)).fetchone()
            if deck is None or deck["published"]:
                raise ValueError("Choose a local deck to save this card.")
            db.execute(
                "INSERT OR IGNORE INTO cards (id, content, created_at, due_at, deck_id) VALUES (?, ?, ?, ?, ?)",
                (identifier, content, now, now, deck_id),
            )
            row = db.execute("SELECT * FROM cards WHERE id = ?", (identifier,)).fetchone()
            if row["content"] != content or row["deck_id"] != deck_id:
                raise ValueError("That draft was already saved. Generate a new draft to save another card.")
            return self.unpack(row)

    def delete(self, identifier):
        with self.connection() as db:
            deleted = db.execute("DELETE FROM cards WHERE id = ? AND deck_id IN "
                                 "(SELECT id FROM decks WHERE published = 0)", (card_id(identifier),))
            return deleted.rowcount == 1

    def review(self, identifier, rating, reviews, now=None):
        identifier = card_id(identifier)
        if rating not in RATINGS or type(reviews) is not int or reviews < 0:
            raise ValueError("Invalid review rating or version.")
        now = int(time.time()) if now is None else now
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""SELECT cards.*, (decks.enabled OR EXISTS (
                    SELECT 1 FROM card_collections JOIN decks AS collection ON collection.id = card_collections.deck_id
                    WHERE card_collections.card_id = cards.id AND collection.enabled
                )) AS deck_enabled FROM cards
                JOIN decks ON cards.deck_id = decks.id WHERE cards.id = ?""", (identifier,)).fetchone()
            if row is None:
                return None
            if not row["enabled"] or not row["deck_enabled"]:
                raise StaleReview("This card is outside your training suite.")
            if row["reviews"] != reviews or row["due_at"] > now:
                raise StaleReview("This card is already scheduled. Refresh your review queue.")
            stage = row["stage"]
            exercise_index = row["exercise_index"]
            if rating == "again":
                stage, delay = 0, 600
            elif rating == "hard":
                stage, delay = max(0, stage - 1), DAY
            else:
                delay = INTERVALS[stage] * DAY
                stage = min(stage + 1, len(INTERVALS) - 1)
                total_exercises = len(json.loads(row["content"])["exercises"])
                exercise_index = (exercise_index + 1) % total_exercises
            db.execute(
                """UPDATE cards SET stage = ?, due_at = ?, exercise_index = ?, reviews = reviews + 1
                   WHERE id = ?""",
                (stage, now + delay, exercise_index, identifier),
            )
            memberships = [item["deck_id"] for item in db.execute(
                "SELECT deck_id FROM card_collections WHERE card_id = ? ORDER BY deck_id", (identifier,)
            )]
            return self.unpack(db.execute("SELECT * FROM cards WHERE id = ?", (identifier,)).fetchone(),
                               memberships)
