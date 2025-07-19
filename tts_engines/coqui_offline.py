from tts_engines.ITTS import ITTS
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
import os
import torch
from TTS.api import TTS as CoquiTTS

device = "cuda" if torch.cuda.is_available() else "cpu"

class TTS(ITTS):
    def __init__(self, en_model_name="tts_models/multilingual/multi-dataset/xtts_v2", fr_model_name="tts_models/fr/mai/tacotron2-DDC"):
        self.tts_en = CoquiTTS(en_model_name).to(device)
        self.tts_fr = CoquiTTS(fr_model_name).to(device)

    def speak(self, text, lang="en", out_path="out.wav"):
        #  print(self.tts.speakers)
        #  ['Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema', 'Alison Dietlinde', 'Ana Florence', 'Annmarie Nele', 'Asya Anara', 'Brenda Stern', 'Gitta Nikolina', 'Henriette Usha', 'Sofia Hellen', 'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper', 'Badr Odhiambo', 'Dionisio Schuyler', 'Royston Min', 'Viktor Eka', 'Abrahan Mack', 'Adde Michal', 'Baldur Sanjin', 'Craig Gutsy', 'Damien Black', 'Gilberto Mathias', 'Ilkin Urbano', 'Kazuhiko Atallah', 'Ludvig Milivoj', 'Suad Qasim', 'Torcull Diarmuid', 'Viktor Menelaos', 'Zacharie Aimilios', 'Nova Hogarth', 'Maja Ruoho', 'Uta Obando', 'Lidiya Szekeres', 'Chandra MacFarland', 'Szofi Granger', 'Camilla Holmström', 'Lilya Stainthorpe', 'Zofija Kendrick', 'Narelle Moon', 'Barbora MacLean', 'Alexandra Hisakawa', 'Alma María', 'Rosemary Okafor', 'Ige Behringer', 'Filip Traverse', 'Damjan Chapman', 'Wulf Carlevaro', 'Aaron Dreschner', 'Kumar Dahl', 'Eugenio Mataracı', 'Ferran Simen', 'Xavier Hayasaka', 'Luis Moray', 'Marcos Rudaski']

        print(self.tts_fr.speakers)
        #print(CoquiTTS.list_models())

        if lang == "fr":
            self.tts_fr.tts_to_file(
                text=text,
                file_path=out_path
            )
        else:
            self.tts_en.tts_to_file(
                text=text,
                speaker="Craig Gutsy",
                language=lang,
                file_path=out_path
            )

        sound = AudioSegment.from_wav(out_path)
        play(sound)

