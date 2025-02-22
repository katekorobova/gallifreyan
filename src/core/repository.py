from __future__ import annotations

import json
from typing import Optional

from .writing.characters import CharacterType, CharacterInfo
from ..config import SEPARATOR, SPACE

_repository: Optional[_CharacterRepository] = None  # Global repository instance


class _CharacterRepository:
    CONSONANTS_FILE = 'src/config/consonants.json'
    VOWELS_FILE = 'src/config/vowels.json'
    DIGITS_FILE = 'src/config/digits.json'
    PUNCTUATION_MARKS_FILE = 'src/config/punctuation_marks.json'
    NUMBER_MARKS_FILE = 'src/config/number_marks.json'

    def __init__(self):
        self.columns: dict[CharacterType, list[str]] = {CharacterType.NUMBER_MARK: []}
        self.tables: dict[CharacterType, list[list[str]]] = \
            {CharacterType.CONSONANT: [], CharacterType.VOWEL: []}
        self.borders: dict[CharacterType, list[str]] = \
            {CharacterType.CONSONANT: [], CharacterType.VOWEL: []}
        self.types: dict[CharacterType, list[str]] = \
            {CharacterType.CONSONANT: [], CharacterType.VOWEL: []}
        self.descriptions: dict[CharacterType, list[str]] = {CharacterType.NUMBER_MARK: []}

        self.all: dict[str, CharacterInfo] = {SEPARATOR: CharacterInfo(CharacterType.SEPARATOR, []),
                                              SPACE: CharacterInfo(CharacterType.SPACE, [])}
        self.disabled = set()

        # Load data for consonants and vowels
        self._load_table(CharacterType.CONSONANT)
        self._load_table(CharacterType.VOWEL)
        self._load_table(CharacterType.DIGIT)
        self._load_column(CharacterType.PUNCTUATION_MARK)
        self._load_column(CharacterType.NUMBER_MARK)

    def _load_table(self, character_type: CharacterType) -> None:
        """
        A helper method to load letters, borders, and types from a file.
        Updates corresponding tables and dictionaries.
        """
        match character_type:
            case CharacterType.CONSONANT:
                file_path = self.CONSONANTS_FILE
            case CharacterType.VOWEL:
                file_path = self.VOWELS_FILE
            case CharacterType.DIGIT:
                file_path = self.DIGITS_FILE
            case _:
                raise ValueError(f"Unable to load the characters with type: '{character_type}'")

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        table = data['characters']
        borders = data['borders']
        types = data['types']
        disabled = data['disabled']

        for row, border in zip(table, borders):
            for character, typ in zip(row, types):
                self.all[character] = CharacterInfo(character_type, [border, typ])

        self.disabled |= set(disabled)
        self.tables[character_type] = table
        self.borders[character_type] = borders
        self.types[character_type] = types

    def _load_column(self, character_type: CharacterType) -> None:
        match character_type:
            case CharacterType.PUNCTUATION_MARK:
                file_path = self.PUNCTUATION_MARKS_FILE
            case CharacterType.NUMBER_MARK:
                file_path = self.NUMBER_MARKS_FILE
            case _:
                raise ValueError(f"Unable to load the characters with type: '{character_type}'")

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        column = data['characters']
        borders = data['borders']
        descriptions = data['descriptions']
        disabled = data['disabled']

        for character, border in zip(column, borders):
            self.all[character] = CharacterInfo(character_type, [border])

        self.disabled |= set(disabled)
        self.columns[character_type] = column
        self.borders[character_type] = borders
        self.descriptions[character_type] = descriptions


def initialize():
    """Initializes the global character repository."""
    global _repository
    if _repository is not None:
        raise RuntimeError("Character repository has already been initialized.")
    _repository = _CharacterRepository()


def get():
    """Retrieves the global character repository."""
    if _repository is None:
        raise RuntimeError("Character repository has not been initialized.")
    return _repository
