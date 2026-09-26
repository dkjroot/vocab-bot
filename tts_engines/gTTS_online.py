from tts_engines.ITTS import ITTS
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO


class TTS(ITTS):
    def __init__(self):
        pass

    def speak(self, text, lang, out_path, region=None):
        regions = {
            "en": "co.uk",
            "fr": "fr"
        }
        tld = region if region else regions.get(lang, "com")
        mp3_fp = BytesIO()
        tts = gTTS(text, lang=lang, tld=tld)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio = AudioSegment.from_file(mp3_fp, format="mp3")
        audio.export(out_path, format="wav")
        play(audio)
