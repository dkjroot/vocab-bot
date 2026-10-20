# Licensing

Copyright in the project's original contributions belongs to Dave (GitHub:
[`dkjroot`](https://github.com/dkjroot)) and the respective contributors.
Third-party authors retain copyright in their own work.

Except for separately identified third-party components and assets, this
project's original code and documentation are free software: you may redistribute
them and/or modify them under the **GNU General Public License, version 3**
(`GPL-3.0-only`), published by the Free Software Foundation. The complete license
is in [LICENSE](LICENSE). The software is provided without warranty;
see that license for details. This notice grants version 3, without an
"or any later version" option.

## The maintainer's request and your legal rights

The README asks people to keep the software freely available, avoid profiting
from paid copies or services built around it, use the official GitHub repository,
and send voluntary development support directly to the maintainer. These are
requests, not added license conditions. Commercial use, charging for copies,
lawful forks, and redistribution remain permitted by GPLv3. Recipients keep
their license rights; donations and maintainer approval are not prerequisites.

When conveying covered software, comply with the GPL's applicable notice,
licensing, and corresponding-source requirements. A GitHub link alone is not
necessarily enough for a binary distribution. Merely running a hosted service
does not by itself trigger the GPL's source-distribution requirements. See the
[GNU licensing FAQ](https://www.gnu.org/licenses/gpl-faq.html).

Third-party packages, data, media, model weights, and external services retain
their own terms. A dependency's license label or this document does not replace
its actual license. Preserve all applicable copyright notices, license texts,
attributions, and any required source or change notices when redistributing them.
Optional external services may charge users independently of this free software.

## Library code and separately licensed models

The application code is GPLv3. Imported library code has its own compatible
licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). There is no pinned
dependency manifest in this checkout, so an exact installed/transitive dependency
set has not been certified. Do not infer a model's license from its Python client.

**The optional Coqui English TTS adapter selects XTTS-v2 by default. That model is
not open source.** Its [Coqui Public Model License](https://huggingface.co/coqui/XTTS-v2/raw/main/LICENSE.txt)
restricts the model and its outputs to noncommercial uses and requires passing on
its terms or their URL. No model weights or generated audio are tracked here, and
publishing the adapter's source does not relicense the model. Do not bundle those
weights or use their output in paid videos, monetized content, or a donation-funded
service without permission covering that use. The maintainer's general support
link does not grant an exception to the model terms. The separate French model
and any replacement voice/vocoder need their own license review.

The README's Leipzig word list link identifies a download site, not a specific
licensed corpus release. No word list is tracked. Before bundling or publishing a
trimmed/pruned list, record its exact archive, corpus/version, upstream terms,
attribution, and modifications. A download link alone does not establish reuse
permission. The advertised MeloTTS alternative is not implemented in this tree;
its library, selected models and dictionaries would need review before inclusion.
