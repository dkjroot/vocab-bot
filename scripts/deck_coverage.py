"""Audit the shipped decks against Lexique/FLELex and Annex E vocabulary themes."""

import argparse
from collections import defaultdict
import csv
import io
from pathlib import Path
import re
import unicodedata
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "coverage"
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
LIMIT = 5000
WORD = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*\Z")
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


def report(decks, ranked, targets, matches, themes):
    all_matches = set().union(*matches.values())
    lines = [
        "# Published deck coverage", "",
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
        "Multiword expressions and words found only in example sentences do not count.",
        "A match means the spelling is taught somewhere in the deck, regardless of sense.", "",
        "### Cumulative frequency targets", "",
        "These are project planning checkpoints, separate from the FLELex level labels.",
        "They measure what the cards teach and do not measure a learner's proficiency.", "",
        "| Checkpoint | Frequency window | In decks through this level | In any published deck |",
        "| --- | --- | ---: | ---: |",
    ])
    cumulative.clear()
    for level, size in zip(LEVELS[:4], (800, 1000, 2000, 5000), strict=True):
        cumulative.update(matches[level])
        window = set(ranked[:size])
        lines.append(f"| {level} | First {size:,} | {ratio(len(window & cumulative), size)} | "
                     f"{ratio(len(window & all_matches), size)} |")
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
        "The script also writes the full ranked reference and deck matches to",
        "`data/coverage/top-5000.tsv`. The source datasets and combined list stay",
        "in the ignored local data folder. The report contains aggregate counts.",
    ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lexique", type=Path, default=DATA / "Lexique4.1.zip")
    parser.add_argument("--flelex", type=Path, default=DATA / "FleLex_TT_Beacco.tsv")
    parser.add_argument("--report", type=Path, help="Write the Markdown report to this path")
    args = parser.parse_args()
    ranked, nouns = frequency_list(args.lexique)
    labels = level_labels(args.flelex)
    decks = load_decks()
    targets = {level: set() for level in (*LEVELS, "Unclassified")}
    for word in ranked:
        targets[labels.get(word, "Unclassified")].add(word)
    reference = set(ranked)
    matches = {level: {card_lemma(title, nouns) for title in cards.values()} & reference
               for level, cards in decks.items()}
    result = report(decks, ranked, targets, matches, theme_counts(decks))
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "top-5000.tsv").open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(("rank", "lemma", "level", "published_decks"))
        for rank, word in enumerate(ranked, start=1):
            covered_by = ",".join(level for level, words in matches.items() if word in words)
            writer.writerow((rank, word, labels.get(word, "Unclassified"), covered_by))
    if args.report:
        args.report.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
