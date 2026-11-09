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


def published_decks():
    directory = Path(__file__).with_name("decks")
    topics = defaultdict(dict)
    with (directory / "annex-e-themes.tsv").open(encoding="utf-8", newline="") as source:
        for level, topic, keys in csv.reader(source, delimiter="\t"):
            for key in keys.split():
                if key in topics[level]:
                    raise ValueError(f"Multiple topics for {level}/{key}.")
                topics[level][key] = topic
    for level, description in LEVELS.items():
        cards = []
        with (directory / f"{level}.tsv").open(encoding="utf-8", newline="") as source:
            for key, fr, en, example, translation, *extra in csv.reader(source, delimiter="\t"):
                identifier = str(uuid5(NAMESPACE_URL, f"vocab-bot:published:{level}:{key}"))
                noun = fr.startswith(("le ", "la ", "les ", "un ", "une ", "l’", "l'"))
                topic = topics[level].get(key) or (extra[0] if extra else None)
                if topic is None:
                    if en.startswith("to "):
                        topic = "Core verbs"
                    elif noun:
                        topic = "Core nouns"
                    else:
                        topic = "Core expressions and other words"
                cards.append((identifier, {
                    "kind": "Phrase" if " " in fr and not noun else "Word",
                    "topic": topic,
                    "title": fr,
                    "cue": en,
                    "examples": [{"fr": example, "en": translation}],
                    "exercises": [{"prompt": f"Give the French for: {en}", "answer": fr}],
                }))
        yield {"id": level, "name": f"French {level.upper()}", "description": description, "cards": cards}
