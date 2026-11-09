from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from flashcards import Deck, StaleReview
from published_decks import FREQUENCY_TIERS, published_decks, published_id
from test_flashcards import CARD


class TrainingSuiteTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "deck.sqlite3"
        self.store = Deck(self.path)

    def test_catalog_is_opt_in_and_reinstall_preserves_progress(self):
        catalog = list(published_decks())
        self.assertEqual(len({identifier for deck in catalog for identifier, _ in deck["cards"]}), 5206)
        previous_sizes = (120, 100, 100, 100)
        previous = ({**deck, "members": [], "cards": [
            (identifier, {k: v for k, v in card.items() if k not in ("topic", "frequency_rank", "source_level")})
            for identifier, card in deck["cards"][:size]
        ]} for deck, size in zip(catalog[:4], previous_sizes, strict=True))
        self.store.install_published(previous)
        self.assertEqual(len(self.store.list()), 420)
        published = [deck for deck in self.store.decks() if deck["published"]]
        self.assertEqual([deck["id"] for deck in published], ["a1", "a2", "b1", "b2"])
        self.assertFalse(any(deck["enabled"] for deck in published))
        card = next(card for card in self.store.list() if card["deck_id"] == "a1")
        with self.assertRaises(StaleReview):
            self.store.review(card["id"], "got-it", 0)
        self.store.set_enabled("a1", True)
        reviewed = self.store.review(card["id"], "got-it", 0)
        self.store.set_enabled(card["id"], False, card=True)
        self.store.install_published(catalog)
        self.assertEqual(len(self.store.list()), 5206)
        updated = next(item for item in self.store.list() if item["id"] == card["id"])
        self.assertEqual((updated["reviews"], updated["enabled"]), (1, 0))
        self.assertEqual(updated["due_at"], reviewed["due_at"])
        self.assertTrue(updated["topic"])
        self.assertTrue(next(deck for deck in self.store.decks() if deck["id"] == "a1")["enabled"])
        self.assertFalse(self.store.delete(card["id"]))

    def test_frequency_tiers_share_cards_and_review_state(self):
        self.store.install_published(published_decks())
        cards = self.store.list()
        for ceiling in FREQUENCY_TIERS:
            ranks = [card["frequency_rank"] for card in cards if f"core-{ceiling}" in card["deck_ids"]]
            self.assertEqual(sorted(ranks), list(range(1, ceiling + 1)))
        for card in cards:
            label = card.get("source_level")
            if label in ("A1", "A2", "B1", "B2"):
                self.assertIn(label.lower(), card["deck_ids"])
        identifier = published_id("a1", "be")
        self.store.set_enabled("core-800", True)
        updated = self.store.review(identifier, "got-it", 0)
        self.assertEqual(updated["reviews"], 1)
        self.assertIn("a1", updated["deck_ids"])
        self.assertIn("core-800", updated["deck_ids"])
        self.store.set_enabled("a1", True)
        self.store.set_enabled("core-800", False)
        updated = self.store.review(identifier, "got-it", 1, now=updated["due_at"])
        self.assertEqual(updated["reviews"], 2)
        self.store.set_enabled(identifier, False, card=True)
        self.store.set_enabled("core-800", True)
        with self.assertRaises(StaleReview):
            self.store.review(identifier, "got-it", 2, now=updated["due_at"])

    def test_local_deck_selection_and_disabled_cards(self):
        local = self.store.create_deck(str(uuid4()), "Le Monde")
        card = self.store.save(str(uuid4()), CARD, local["id"])
        self.assertEqual(card["deck_id"], local["id"])
        self.store.set_enabled(card["id"], False, card=True)
        with self.assertRaises(StaleReview):
            self.store.review(card["id"], "got-it", 0)
        self.store.set_enabled(card["id"], True, card=True)
        self.store.review(card["id"], "got-it", 0)

    def test_existing_cards_are_migrated_into_reading_notes(self):
        path = self.path.with_name("old.sqlite3")
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""CREATE TABLE cards (
                id TEXT PRIMARY KEY, content TEXT NOT NULL, created_at INTEGER NOT NULL,
                due_at INTEGER NOT NULL, stage INTEGER NOT NULL, reviews INTEGER NOT NULL
            )""")
            db.execute("INSERT INTO cards VALUES ('old', '{}', 0, 10, 2, 3)")
        card, = Deck(path).list()
        self.assertEqual((card["deck_id"], card["enabled"], card["reviews"]), ("reading", 1, 3))
