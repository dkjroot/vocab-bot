import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from flashcards import DAY, Deck, StaleReview, validate_card


CARD = {
    "kind": "Phrase",
    "title": "Ça marche",
    "cue": "That works.",
    "examples": [{"fr": "Ça marche pour moi.", "en": "That works for me."}],
    "exercises": [{"prompt": "Say ‘That works’.", "answer": "Ça marche"}],
}


class FlashcardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "deck.sqlite3"
        self.deck = Deck(self.path)
        self.identifier = str(uuid4())

    def test_save_retry_does_not_duplicate_or_reset_a_review(self):
        card = self.deck.save(self.identifier, CARD)
        self.deck.review(self.identifier, "got-it", 0, now=card["due_at"])
        self.deck = Deck(self.path)
        same = self.deck.save(self.identifier, CARD)
        self.assertEqual(same["reviews"], 1)
        self.assertEqual(len(self.deck.list()), 1)

    def test_schedule_increases_on_recall_and_resets_after_a_lapse(self):
        card = self.deck.save(self.identifier, CARD)
        first = self.deck.review(self.identifier, "got-it", 0, now=card["due_at"])
        self.assertEqual(first["due_at"], card["due_at"] + DAY)
        second = self.deck.review(self.identifier, "got-it", 1, now=first["due_at"])
        self.assertEqual(second["due_at"], first["due_at"] + 3 * DAY)
        lapse = self.deck.review(self.identifier, "again", 2, now=second["due_at"])
        self.assertEqual(lapse["due_at"], second["due_at"] + 600)
        self.assertEqual(lapse["stage"], 0)

    def test_stale_and_early_reviews_do_not_change_progress(self):
        card = self.deck.save(self.identifier, CARD)
        review = self.deck.review(self.identifier, "hard", 0, now=card["due_at"])
        with self.assertRaises(StaleReview):
            self.deck.review(self.identifier, "got-it", 1, now=card["due_at"])
        with self.assertRaises(StaleReview):
            self.deck.review(self.identifier, "got-it", 0, now=review["due_at"])
        self.assertEqual(self.deck.list()[0], review)

    def test_confident_recall_rotates_exercises_but_a_lapse_repeats_the_prompt(self):
        content = {**CARD, "exercises": [*CARD["exercises"],
                   {"prompt": "Say ‘That works for me’.", "answer": "Ça marche pour moi."}]}
        card = self.deck.save(self.identifier, content)
        first = self.deck.review(self.identifier, "got-it", 0, now=card["due_at"])
        self.assertEqual(first["exercise_index"], 1)
        lapse = self.deck.review(self.identifier, "again", 1, now=first["due_at"])
        self.assertEqual(lapse["exercise_index"], 1)

    def test_invalid_draft_cannot_be_saved(self):
        with self.assertRaises(ValueError):
            self.deck.save(self.identifier, {**CARD, "exercises": []})
        self.assertEqual(self.deck.list(), [])
        with self.assertRaises(ValueError):
            validate_card({**CARD, "forms": ["present"]})

    def test_deleting_a_card_also_removes_its_review_record(self):
        card = self.deck.save(self.identifier, CARD)
        self.deck.review(self.identifier, "got-it", 0, now=card["due_at"])
        self.assertTrue(self.deck.delete(self.identifier))
        self.assertEqual(self.deck.list(), [])
        self.assertIsNone(self.deck.review(self.identifier, "again", 1))


if __name__ == "__main__":
    unittest.main()
