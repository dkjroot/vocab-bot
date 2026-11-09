"""Load the vocabulary packs shipped with the project."""

import csv
from collections import defaultdict
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

LEVELS = {
    "a1": "Introductions, daily routines, time and numbers, food, shopping and getting around.",
    "a2": "Shopping and returns, holidays, housing, health, cooking, work and study.",
    "b1": "Job interviews, education, outings, relationships, culture, news and opinions.",
    "b2": "Meetings and argument, evidence and media, society, economics, climate and technology.",
}


FREQUENCY_TIERS = (800, 1000, 2000, 5000)
SOURCE_LEVELS = {*map(str.upper, LEVELS), "C1", "C2", "Unclassified"}


def published_id(collection, key):
    return str(uuid5(NAMESPACE_URL, f"vocab-bot:published:{collection}:{key}"))


def make_card(fr, en, example, translation, topic, notes="", alternatives=()):
    noun = fr.startswith(("le ", "la ", "les ", "un ", "une ", "l’", "l'"))
    return {
        "kind": "Phrase" if " " in fr and not noun else "Word",
        "topic": topic,
        "title": fr,
        "cue": en,
        "notes": notes,
        "examples": [{"fr": example, "en": translation}],
        "exercises": [{"prompt": f"Give the French for: {en}", "answer": fr,
                       "alternatives": list(alternatives)}],
    }


def published_decks():
    directory = Path(__file__).with_name("decks")
    topics = defaultdict(dict)
    with (directory / "annex-e-themes.tsv").open(encoding="utf-8", newline="") as source:
        for level, topic, keys in csv.reader(source, delimiter="\t"):
            for key in keys.split():
                if key in topics[level]:
                    raise ValueError(f"Multiple topics for {level}/{key}.")
                topics[level][key] = topic
    decks = {level: {"id": level, "name": f"French {level.upper()}",
                     "description": description, "cards": [], "members": []}
             for level, description in LEVELS.items()}
    for ceiling in FREQUENCY_TIERS:
        deck_id = f"core-{ceiling}"
        decks[deck_id] = {
            "id": deck_id, "name": f"First {ceiling:,}",
            "description": f"The first {ceiling:,} ranked French headwords. Tiers are cumulative.",
            "cards": [], "members": [],
        }
    existing = {}
    for level in LEVELS:
        with (directory / f"{level}.tsv").open(encoding="utf-8", newline="") as source:
            for key, fr, en, example, translation, *extra in csv.reader(source, delimiter="\t"):
                identifier = published_id(level, key)
                noun = fr.startswith(("le ", "la ", "les ", "un ", "une ", "l’", "l'"))
                topic = topics[level].get(key) or (extra[0] if extra else None)
                if topic is None:
                    if en.startswith("to "):
                        topic = "Core verbs"
                    elif noun:
                        topic = "Core nouns"
                    else:
                        topic = "Core expressions and other words"
                card = make_card(fr, en, example, translation, topic)
                if (level, key) in existing:
                    raise ValueError(f"Duplicate card key in {level}: {key}.")
                existing[level, key] = card
                decks[level]["cards"].append((identifier, card))

    authored = {}
    with (directory / "frequency-cards.tsv").open(encoding="utf-8", newline="") as source:
        for rank, fr, en, example, translation, topic, *extra in csv.reader(source, delimiter="\t"):
            if rank in authored:
                raise ValueError(f"Duplicate frequency card at rank {rank}.")
            notes = extra[0] if extra else ""
            alternatives = extra[1:] if extra else []
            authored[rank] = make_card(fr, en, example, translation, topic, notes, alternatives)
    with (directory / "frequency-source-levels.tsv").open(encoding="utf-8", newline="") as source:
        source_levels = dict(csv.reader(source, delimiter="\t"))
    previous_rank = 0
    with (directory / "frequency-index.tsv").open(encoding="utf-8", newline="") as source:
        for rank, *legacy in csv.reader(source, delimiter="\t"):
            label = source_levels.pop(rank, None)
            if not previous_rank < int(rank) <= FREQUENCY_TIERS[-1] or label not in SOURCE_LEVELS:
                raise ValueError(f"Invalid frequency index entry at rank {rank}.")
            previous_rank = int(rank)
            tiers = [f"core-{ceiling}" for ceiling in FREQUENCY_TIERS if int(rank) <= ceiling]
            if legacy:
                level, key = legacy
                identifier = published_id(level, key)
                card = existing[level, key]
                if "frequency_rank" in card:
                    raise ValueError(f"Card {level}/{key} has multiple ranks.")
            else:
                card = authored.pop(rank, None)
                if card is None:
                    raise ValueError(f"Missing frequency card at rank {rank}.")
                identifier = published_id("frequency", rank)
                decks[label.lower() if label.lower() in LEVELS else tiers[0]]["cards"].append((identifier, card))
            card.update(frequency_rank=int(rank), source_level=label)
            for deck_id in tiers:
                decks[deck_id]["members"].append(identifier)
            if legacy and label.lower() in LEVELS and level != label.lower():
                decks[label.lower()]["members"].append(identifier)
    if source_levels:
        raise ValueError(f"Source levels missing from the index: {', '.join(source_levels)}.")
    if authored:
        raise ValueError(f"Frequency cards missing from the index: {', '.join(authored)}.")
    yield from decks.values()
