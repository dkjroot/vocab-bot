from tts_engines.ITTS import ITTS
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO


class TTS(ITTS):
    def __init__(self):
        pass

    def speak(self, text, lang="en", out_path="output.wav"):
        regions = {
            "en": "co.uk",
            "fr": "fr"
        }
        mp3_fp = BytesIO()
        tts = gTTS(text, lang=lang, tld=regions[lang])
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio = AudioSegment.from_file(mp3_fp, format="mp3")
        audio.export(out_path, format="wav")
        play(audio)
