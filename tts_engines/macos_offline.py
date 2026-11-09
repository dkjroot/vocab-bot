"""Render and play speech using installed macOS voices."""

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import wave

from tts_engines.ITTS import ITTS


class TTS(ITTS):
    def __init__(self):
        if sys.platform != "darwin":
            raise RuntimeError("The macOS speech engine requires a Mac.")
        self.voices = {
            "en": os.getenv("VOCAB_BOT_EN_VOICE") or "Daniel (English (UK))",
            "fr": os.getenv("VOCAB_BOT_FR_VOICE") or "Thomas",
        }

    def speak(self, text, lang, out_path, region=None):
        self.render(text, lang, out_path)
        subprocess.run(["/usr/bin/afplay", str(Path(out_path).resolve())], check=True)

    def render(self, text, lang, out_path):
        if lang not in self.voices:
            raise ValueError(f"The macOS speech engine does not support {lang!r}.")
        voice = self.voices[lang]
        output = Path(out_path).resolve()
        with TemporaryDirectory(dir=output.parent) as temp_dir:
            sample = Path(temp_dir) / "speech.wav"
            try:
                subprocess.run(
                    ["/usr/bin/say", "-v", voice, "--file-format=WAVE",
                     "--data-format=LEI16@22050", "-o", str(sample), "-f", "-"],
                    input=text,
                    encoding="utf-8",
                    check=True,
                    timeout=30,
                )
                with wave.open(str(sample)) as audio:
                    if not audio.readframes(1):
                        raise wave.Error("The speech file contains no audio.")
            except (subprocess.SubprocessError, FileNotFoundError, EOFError, wave.Error) as error:
                raise RuntimeError(
                    f"Could not synthesise speech with {voice!r}. Run `say -v '?'` to list voices."
                ) from error
            sample.replace(output)
