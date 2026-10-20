# Third-party dependencies, models, and data

Reviewed 20 October 2026 from the checked-out source imports and configuration.
Dependencies are installed separately; no third-party library source, model
weights, generated speech, or word list is tracked in this tree. There is no
pinned manifest/lockfile, so this is an inventory rather than clearance of a
particular installed/transitive/native environment.

| Library | Credit/source | Code license |
| --- | --- | --- |
| OpenAI Python SDK | [OpenAI and contributors](https://github.com/openai/openai-python) | Apache-2.0 |
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

The README mentions MeloTTS/melotts-plus and UniDic, but no corresponding adapter
is implemented here. Do not assume their model/dictionary licenses from that
installation note. For any future distribution, inventory exact dependencies,
voices, dictionaries and assets and keep required notices/source. See
[LICENSING.md](LICENSING.md).
