"""Audit the shipped decks against Lexique/FLELex and Annex E vocabulary themes."""

import argparse
from collections import defaultdict
import csv
from hashlib import sha256
import io
from pathlib import Path
import re
import sys
import unicodedata
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from published_decks import FREQUENCY_TIERS, published_decks

DATA = ROOT / "data" / "coverage"
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
LIMIT = 5000
WORD = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*\Z")
# These source spellings are kept as ranks while the cards teach standard French.
STANDARD_SPELLINGS = {
    "no": "nô",
    "trés": "très",
    "déja": "déjà",
    "tit": "p'tit",
    "age": "âge",
    "media": "média",
    "aprés": "après",
    "est-ce-que": "est-ce que",
}
ARTICLE = re.compile(r"^(?:(?:le|la|les|un|une) |l')")


def normalise(word):
    return unicodedata.normalize("NFC", word.strip()).casefold().replace("’", "'").replace("‑", "-")


def frequency_list(archive):
    scores = defaultdict(dict)
    noun_forms = defaultdict(set)
    with ZipFile(archive) as source, source.open("Lexique4.1/Lexique4.1.tsv") as binary:
        rows = csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8-sig"), delimiter="\t")
        for row in rows:
            lemma = normalise(row["4_Lemme"])
            category = row["5_Cgram"]
            if (not WORD.fullmatch(lemma) or category.startswith("NOMpr")
                    or (len(lemma) == 1 and lemma not in {"à", "ô", "y"})):
                continue
            form = normalise(row["1_Mot"])
            # Sum observed form frequencies. Some near-miss spellings share
            # another lemma's published aggregate, so ranking by it inflates them.
            frequency = float(row["10_FreqMot"] or 0)
            entry = (form, category)
            scores[lemma][entry] = max(frequency, scores[lemma].get(entry, 0))
            if category == "NOM":
                noun_forms[form].add(lemma)
    totals = {lemma: sum(by_category.values()) for lemma, by_category in scores.items()}
    ranked = sorted(totals, key=lambda lemma: (-totals[lemma], lemma))[:LIMIT]
    if len(ranked) != LIMIT:
        raise ValueError(f"Expected {LIMIT} distinct lemmas.")
    return ranked, noun_forms


def level_labels(path):
    labels = {}
    with path.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            level = row["level"]
            word = normalise(row["word"])
            if level in LEVELS and (word not in labels or LEVELS.index(level) < LEVELS.index(labels[word])):
                labels[word] = level
    return labels


def card_lemma(title, noun_forms):
    word = normalise(title)
    if word in {"l'un", "l'une"}:
        return word
    article = ARTICLE.match(word)
    if article and WORD.fullmatch(word[article.end():]):
        noun = word[article.end():]
        candidates = noun_forms.get(noun, ())
        if len(candidates) == 1:
            return next(iter(candidates))
        return noun
    return word if WORD.fullmatch(word) else None


def load_decks():
    decks = {}
    for level in LEVELS[:4]:
        with (ROOT / "decks" / f"{level.lower()}.tsv").open(encoding="utf-8", newline="") as source:
            rows = list(csv.reader(source, delimiter="\t"))
        decks[level] = {key: title for key, title, *_ in rows}
        if len(decks[level]) != len(rows):
            raise ValueError(f"Duplicate card key in {level}.")
    return decks


def theme_counts(decks):
    themes = defaultdict(dict)
    with (ROOT / "decks" / "annex-e-themes.tsv").open(encoding="utf-8", newline="") as source:
        for level, name, keys in csv.reader(source, delimiter="\t"):
            level = level.upper()
            keys = keys.split()
            if name in themes[level] or len(keys) != len(set(keys)) or set(keys) - decks[level].keys():
                raise ValueError(f"Invalid theme mapping in {level}: {name}")
            themes[level][name] = len(keys)
    return themes


def ratio(numerator, denominator):
    return f"{numerator}/{denominator} ({numerator / denominator:.1%})" if denominator else "—"


def report(decks, ranked, targets, matches, themes, frequency, total_cards):
    all_matches = set().union(*matches.values(), *frequency.values())
    lines = [
        "# Published deck coverage", "",
        f"There are **{total_cards:,} unique cards** in the published catalogue.", "",
        "## Frequent French lemmas", "",
        "The reference ranks 5,000 single-word lemmas by subtitle frequency in Lexique 4.10.",
        "The ranking sums observed form frequencies by lemma, excludes proper nouns",
        "and filters out isolated letters apart from à, ô and y.",
        "It keeps accents and joins FLELex/Beacco's",
        "receptive levels by spelling. If FLELex gives a spelling several levels, the",
        "earliest one is used. C1, C2 and unclassified lemmas stay in the reference.",
        "These are corpus-based study targets with approximate levels.", "",
        "| Target level | Target lemmas | In the matching deck | In that deck or earlier | In any published deck |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    cumulative = set()
    for level, words in targets.items():
        same = matches.get(level, set())
        cumulative.update(same)
        level_coverage = [ratio(len(words & cards), len(words)) for cards in (same, cumulative)] \
            if level in decks else ["—", "—"]
        lines.append(f"| {level} | {len(words):,} | {' | '.join(level_coverage)} | "
                     f"{ratio(len(words & all_matches), len(words))} |")
    lines.extend([
        "", f"Across the whole reference, the published decks match **{ratio(len(all_matches), LIMIT)}**.",
        "", "The match is based on the card headword. Articles are stripped from single",
        "nouns and noun forms are reduced to the lemma when Lexique gives a unique match.",
        "Ordinary multiword cards and words found only in examples do not count.",
        "A few explicit matches teach the standard spelling of a frozen corpus entry.",
        "The audit tracks headwords and placements. Corpus counts can combine senses.", "",
        "### Cumulative frequency targets", "",
        "These are project planning checkpoints, separate from the FLELex level labels.",
        "They measure what the cards teach and do not measure a learner's proficiency.", "",
        "| Core frequency tier | In this tier | In any published collection |",
        "| --- | ---: | ---: |",
    ])
    for size in FREQUENCY_TIERS:
        window = set(ranked[:size])
        lines.append(f"| First {size:,} | {ratio(len(frequency[size]), size)} | "
                     f"{ratio(len(window & all_matches), size)} |")
    contiguous = next((index for index, word in enumerate(ranked)
                       if word not in frequency[LIMIT]), LIMIT)
    if contiguous and contiguous not in FREQUENCY_TIERS:
        lines.extend(["", f"Every rank from 1 through **{contiguous:,}** is covered in Core frequency."])
    lines.extend([
        "", "## Annex E vocabulary themes", "",
        "Cards are mapped by hand to the themes their headwords teach directly.",
        "A theme counts as represented at one card. Three cards is a separate depth",
        "marker for this project. Theme counts measure breadth and depth of vocabulary",
        "practice. Annex E also lists grammar, discourse and communication goals.", "",
        "| Deck | Cards | Themes represented | Themes with 3+ cards |",
        "| --- | ---: | ---: | ---: |",
    ])
    for level, cards in decks.items():
        counts = themes[level].values()
        lines.append(f"| {level} | {len(cards)} | {ratio(sum(n > 0 for n in counts), len(counts))} | "
                     f"{ratio(sum(n >= 3 for n in counts), len(counts))} |")
    for level in decks:
        lines.extend(["", f"### {level}", "", "| Vocabulary theme | Cards |", "| --- | ---: |"])
        lines.extend(f"| {name} | {count} |" for name, count in themes[level].items())
    lines.extend([
        "", "## Sources", "",
        "- [Lexique 4.10](https://www.lexique.org/), New, Pallier and collaborators. CC BY-SA 4.0.",
        "- [FLELex / Beacco](https://cental.uclouvain.be/cefrlex/flelex/download/), Pintard and François (2020). CC BY-NC-SA 4.0.",
        "- [Eaquals/CIEP French Core Inventory, Annex E](https://www.eaquals.org/wp-content/uploads/Inventaire_ONLINE_full.pdf).",
        "", "## Rebuild this report", "",
        "Put the [Lexique ZIP](https://www.lexique.org/databases/Lexique410/Lexique4.1.zip)",
        "and [FLELex/Beacco TSV](https://cental.uclouvain.be/cefrlex/static/resources/fr/FleLex_TT_Beacco.tsv)",
        "in `data/coverage/`, then run:", "",
        "```sh", "python scripts/deck_coverage.py --report decks/COVERAGE.md", "```", "",
        "The audit checks the source archives and all 5,000 ranked entries against",
        "[the frozen checksums](coverage-checksums.tsv). It writes current collection",
        "matches and separate worklists for missing headwords and placements under",
        "`data/coverage/`.",
    ])
    return "\n".join(lines) + "\n"


def checked_reference(lexique, flelex):
    with (ROOT / "decks" / "coverage-checksums.tsv").open(encoding="utf-8") as source:
        checksums = dict(csv.reader(source, delimiter="\t"))
    for path, key in ((lexique, "Lexique4.1.zip"), (flelex, "FleLex_TT_Beacco.tsv")):
        if sha256(path.read_bytes()).hexdigest() != checksums[key]:
            raise ValueError(f"{path} differs from the frozen coverage source.")
    ranked, nouns = frequency_list(lexique)
    labels = level_labels(flelex)
    rows = [(rank, word, labels.get(word, "Unclassified")) for rank, word in enumerate(ranked, 1)]
    reference = "rank\tlemma\tlevel\n" + "".join(f"{rank}\t{word}\t{label}\n" for rank, word, label in rows)
    if sha256(reference.encode()).hexdigest() != checksums["rank-lemma-level.tsv"]:
        raise ValueError("The 5,000 ranked lemmas or source labels have changed.")
    return rows, nouns


def audit(rows, nouns):
    catalog = list(published_decks())
    cards = {identifier: card for deck in catalog for identifier, card in deck["cards"]}
    ranked = [word for _, word, _ in rows]
    ranks = {word: rank for rank, word, _ in rows}
    card_words = {}
    for identifier, card in cards.items():
        word = card_lemma(card["title"], nouns)
        if "frequency_rank" in card:
            rank = card["frequency_rank"]
            _, expected, label = rows[rank - 1]
            # The reference spells out oe, while the cards use the French ligature.
            literal = ARTICLE.sub("", normalise(card["title"]))
            spellings = {expected, expected.replace("oe", "œ"), STANDARD_SPELLINGS.get(expected, expected)}
            if not spellings.intersection((word, literal)) or card["source_level"] != label:
                raise ValueError(f"Rank {rank} expects {expected} ({label}), got {card['title']}.")
            word = expected
        if word in ranks:
            card_words[identifier] = word
    members = {deck["id"]: {identifier for identifier, _ in deck["cards"]} | set(deck["members"])
               for deck in catalog}
    collection_words = {deck_id: {card_words[identifier] for identifier in ids if identifier in card_words}
                        for deck_id, ids in members.items()}
    frequency = {size: collection_words[f"core-{size}"] for size in FREQUENCY_TIERS}
    for size, words in frequency.items():
        if any(ranks[word] > size for word in words):
            raise ValueError(f"Core frequency tier {size} includes an out-of-range card.")
    matches = {level: collection_words[level.lower()] for level in LEVELS[:4]}
    targets = {level: set() for level in (*LEVELS, "Unclassified")}
    identifiers = defaultdict(list)
    for identifier, word in card_words.items():
        identifiers[word].append(identifier)
    reference_rows, missing, placements = [], [], []
    for rank, word, label in rows:
        targets[label].add(word)
        present = [deck_id for deck_id, words in collection_words.items() if word in words]
        reference_rows.append((rank, word, label, ",".join(present)))
        expected = [f"core-{size}" for size in FREQUENCY_TIERS if rank <= size]
        if label in LEVELS[:4]:
            expected.append(label.lower())
        gaps = [deck_id for deck_id in expected if deck_id not in present]
        if not gaps:
            continue
        ids = identifiers[word]
        topic = cards[ids[0]]["topic"] if ids else ("Core nouns" if word in nouns else "Core vocabulary")
        status = "Review placement" if ids else "Write and review"
        worklist = placements if ids else missing
        worklist.append((rank, word, label, ",".join(ids), ",".join(gaps), topic, status))

    DATA.mkdir(parents=True, exist_ok=True)
    worklist_header = ("rank", "lemma", "level", "card_ids", "missing_placements", "proposed_topic", "qa_status")
    for filename, header, entries in (
        ("top-5000.tsv", ("rank", "lemma", "level", "published_decks"), reference_rows),
        ("missing-headwords.tsv", worklist_header, missing),
        ("placement-fixes.tsv", worklist_header, placements),
    ):
        with (DATA / filename).open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output, delimiter="\t", lineterminator="\n")
            writer.writerow(header)
            writer.writerows(entries)
    themes = theme_counts(load_decks())
    return report({level: members[level.lower()] for level in LEVELS[:4]},
                  ranked, targets, matches, themes, frequency, len(cards))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lexique", type=Path, default=DATA / "Lexique4.1.zip")
    parser.add_argument("--flelex", type=Path, default=DATA / "FleLex_TT_Beacco.tsv")
    parser.add_argument("--report", type=Path, help="Write the Markdown report to this path")
    args = parser.parse_args()
    result = audit(*checked_reference(args.lexique, args.flelex))
    if args.report:
        args.report.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
