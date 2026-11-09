# Third-party dependencies, models, and data

Reviewed 20 October 2026 from the checked-out source imports and configuration.
Dependencies are installed separately; no third-party library source, model
weights, generated speech, or word list is tracked in this tree. There is no
pinned manifest/lockfile, so this is an inventory rather than clearance of a
particular installed/transitive/native environment.

| Library | Credit/source | Code license |
| --- | --- | --- |
| OpenAI Python SDK | [OpenAI and contributors](https://github.com/openai/openai-python) | Apache-2.0 |
| Google Gen AI SDK | [Google and contributors](https://github.com/googleapis/python-genai) | Apache-2.0. Gemini service terms are separate. |
| gTTS | [Pierre Nicolas Durette and contributors](https://pypi.org/project/gTTS/) | MIT; online service terms separate |
| pydub | [James Robert and contributors](https://pypi.org/project/pydub/) | MIT |
| PyTorch | [PyTorch contributors](https://github.com/pytorch/pytorch/blob/main/LICENSE) | BSD-3-Clause and bundled component notices |
| Coqui TTS (`TTS.api`) | [Coqui and contributors](https://github.com/coqui-ai/TTS) | MPL-2.0; trained models have separate licenses |
| FFmpeg/ffprobe, if used for pydub decoding/playback | [FFmpeg authors](https://ffmpeg.org/legal.html) | LGPL-2.1-or-later or GPL depending on exact build |

These library code licenses permit use with GPLv3 while preserving their own
conditions, notices, and source obligations. Platform audio/CUDA dependencies and
user-selected LLMs need their own review before redistribution.

## Coqui models selected by the optional adapter

- **English/multilingual: `tts_models/multilingual/multi-dataset/xtts_v2`.**
  [Model by Coqui](https://huggingface.co/coqui/XTTS-v2), under the
  [Coqui Public Model License](https://huggingface.co/coqui/XTTS-v2/raw/main/LICENSE.txt).
  This is a noncommercial model license, including restrictions on output and
  direct or indirect payment arising from model/output use. Pass on the terms
  or their URL when sharing the model or its output. It is not GPL or open source.
- **French: `tts_models/fr/mai/tacotron2-DDC`.** Coqui's
  [model catalogue](https://github.com/coqui-ai/TTS/blob/dev/TTS/.models.json)
  credits Eren Golge and labels this model's license "MPL" (without a version
  in that entry). Its default vocoder is
  `vocoder_models/universal/libri-tts/fullband-melgan`. Verify the full license
  in the exact downloaded model and vocoder archives before redistribution;
  no copies of these assets are included in this repository.

Publishing the adapter source under GPL does not change those model terms.
Do not treat a free download, the TTS library's MPL license, or a general Buy Me
a Coffee link as permission to monetize XTTS audio. Use a separately licensed
model/output path for paid or revenue-generating uses unless permission is secured.

## Word lists and other optional resources

The README links to Leipzig University's Wortschatz download page but does not
identify the exact French corpus/version or archive license. No such list is
tracked. Keep its original terms, source, author credits, and a record of pruning
before publishing a derived word list or dataset. Permission has not been
established merely by citing the download site.

The macOS speech adapter uses system tools and voices supplied by Apple.
Refer to the [licence for your version of macOS](https://www.apple.com/legal/sla/)
for the terms on generated audio.

## Published vocabulary metadata

- `decks/frequency-index.tsv` maps a subset of the project's Lexique 4.10
  ranks to card keys. The ranks use aggregated subtitle frequencies, with
  proper nouns and most isolated letters filtered out. The Lexique-derived
  metadata is shared under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  [Lexique, Boris New, Christophe Pallier and collaborators](https://www.lexique.org/).
- `decks/frequency-source-levels.tsv` contains the corresponding FLELex /
  Beacco labels. The project matches by spelling and keeps the earliest
  available label, marking unmatched entries as Unclassified. The labels
  are shared under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
  [FLELex / Beacco, Pintard and François (2020)](https://cental.uclouvain.be/cefrlex/flelex/download/).

The French and English prompts, examples and explanations in
`decks/frequency-cards.tsv` are original project content.
