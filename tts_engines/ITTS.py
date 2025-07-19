# Interface that all TTS engines must implement
from abc import ABC, abstractmethod


class ITTS(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def speak(self, text, lang, region, out_path):
        pass
