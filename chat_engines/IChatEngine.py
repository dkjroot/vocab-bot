# Interface that all chat engines must implement
from abc import ABC, abstractmethod


class IChatEngine(ABC):

    @abstractmethod
    def __init__(self, settings, system_prompt):
        pass

    @abstractmethod
    def get_response(self, user_text):
        pass

    @abstractmethod
    def clear_conversation(system_prompt):
        pass
