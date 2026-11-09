# Published deck coverage

## Frequent French lemmas

The reference ranks 5,000 single-word lemmas by subtitle frequency in Lexique 4.10.
The ranking sums observed form frequencies by lemma, excludes proper nouns
and filters out isolated letters apart from à, ô and y.
It keeps accents and joins FLELex/Beacco's
receptive levels by spelling. If FLELex gives a spelling several levels, the
earliest one is used. C1, C2 and unclassified lemmas stay in the reference.
These are corpus-based study targets with approximate levels.

| Target level | Target lemmas | In the matching deck | In that deck or earlier | In any published deck |
| --- | ---: | ---: | ---: | ---: |
| A1 | 1,143 | 203/1143 (17.8%) | 203/1143 (17.8%) | 253/1143 (22.1%) |
| A2 | 491 | 75/491 (15.3%) | 80/491 (16.3%) | 89/491 (18.1%) |
| B1 | 1,208 | 88/1208 (7.3%) | 102/1208 (8.4%) | 109/1208 (9.0%) |
| B2 | 1,301 | 66/1301 (5.1%) | 83/1301 (6.4%) | 83/1301 (6.4%) |
| C1 | 164 | — | — | 1/164 (0.6%) |
| C2 | 140 | — | — | 0/140 (0.0%) |
| Unclassified | 553 | — | — | 5/553 (0.9%) |

Across the whole reference, the published decks match **540/5000 (10.8%)**.

The match is based on the card headword. Articles are stripped from single
nouns and noun forms are reduced to the lemma when Lexique gives a unique match.
Multiword expressions and words found only in example sentences do not count.
A match means the spelling is taught somewhere in the deck, regardless of sense.

### Cumulative frequency targets

These are project planning checkpoints, separate from the FLELex level labels.
They measure what the cards teach and do not measure a learner's proficiency.

| Checkpoint | Frequency window | In decks through this level | In any published deck |
| --- | --- | ---: | ---: |
| A1 | First 800 | 172/800 (21.5%) | 270/800 (33.8%) |
| A2 | First 1,000 | 239/1000 (23.9%) | 315/1000 (31.5%) |
| B1 | First 2,000 | 409/2000 (20.4%) | 459/2000 (22.9%) |
| B2 | First 5,000 | 540/5000 (10.8%) | 540/5000 (10.8%) |

## Annex E vocabulary themes

Cards are mapped by hand to the themes their headwords teach directly.
A theme counts as represented at one card. Three cards is a separate depth
marker for this project. Theme counts measure breadth and depth of vocabulary
practice. Annex E also lists grammar, discourse and communication goals.

| Deck | Cards | Themes represented | Themes with 3+ cards |
| --- | ---: | ---: | ---: |
| A1 | 237 | 16/16 (100.0%) | 16/16 (100.0%) |
| A2 | 166 | 13/13 (100.0%) | 13/13 (100.0%) |
| B1 | 170 | 11/11 (100.0%) | 11/11 (100.0%) |
| B2 | 173 | 13/13 (100.0%) | 13/13 (100.0%) |

### A1

| Vocabulary theme | Cards |
| --- | ---: |
| Calendar, seasons and celebrations | 17 |
| Weights, measures and quantities | 3 |
| Personal and everyday objects | 4 |
| Numbers and civil status | 16 |
| Countries and nationalities | 3 |
| Jobs and work | 3 |
| Family and social relationships | 11 |
| Daily activities | 7 |
| Leisure and sport | 3 |
| Transport | 6 |
| Holidays and travel | 4 |
| Housing and furnishings | 5 |
| Places, shops and services in town | 9 |
| Food and cooking | 8 |
| Clothes and accessories | 5 |
| Weather | 3 |

### A2

| Vocabulary theme | Cards |
| --- | ---: |
| Personal and everyday objects | 7 |
| Customs and traditions | 3 |
| Work and professional life | 7 |
| Family and social relationships | 6 |
| Appearance, character and personality | 5 |
| Health | 14 |
| Daily activities | 10 |
| Leisure and sport | 5 |
| Holidays and travel | 16 |
| Housing, furniture and equipment | 11 |
| Food and cooking | 10 |
| Clothes and accessories | 7 |
| Education and training | 9 |

### B1

| Vocabulary theme | Cards |
| --- | ---: |
| Customs and traditions | 5 |
| Work and professional life | 21 |
| Relationships, appearance and personality | 8 |
| Feelings and emotions | 7 |
| Health | 9 |
| Daily activities | 7 |
| Leisure, sport and travel | 17 |
| Fashion | 4 |
| Arts and culture | 9 |
| Media and current affairs | 15 |
| Education and training | 10 |

### B2

| Vocabulary theme | Cards |
| --- | ---: |
| Customs and traditions | 4 |
| Work and professional life | 13 |
| Specialist vocabulary | 15 |
| Feelings and emotions | 6 |
| Fashion | 4 |
| Arts and culture | 5 |
| Media and current affairs | 10 |
| Social trends and issues | 10 |
| Environment, climate and ecology | 11 |
| Education and training | 4 |
| Economics | 7 |
| Information and communications technology | 8 |
| Politics and social values | 9 |

## Sources

- [Lexique 4.10](https://www.lexique.org/), New, Pallier and collaborators. CC BY-SA 4.0.
- [FLELex / Beacco](https://cental.uclouvain.be/cefrlex/flelex/download/), Pintard and François (2020). CC BY-NC-SA 4.0.
- [Eaquals/CIEP French Core Inventory, Annex E](https://www.eaquals.org/wp-content/uploads/Inventaire_ONLINE_full.pdf).

## Rebuild this report

Put the [Lexique ZIP](https://www.lexique.org/databases/Lexique410/Lexique4.1.zip)
and [FLELex/Beacco TSV](https://cental.uclouvain.be/cefrlex/static/resources/fr/FleLex_TT_Beacco.tsv)
in `data/coverage/`, then run:

```sh
python scripts/deck_coverage.py --report decks/COVERAGE.md
```

The script also writes the full ranked reference and deck matches to
`data/coverage/top-5000.tsv`. The source datasets and combined list stay
in the ignored local data folder. The report contains aggregate counts.
