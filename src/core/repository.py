from __future__ import annotations

import json
from typing import Optional

from .components.characters import LetterType, CharacterType
from ..config import SYLLABLE_SEPARATOR

_repository: Optional[_CharacterRepository] = None  # Global repository instance


class _CharacterRepository:
    consonant_file_path = 'src/config/consonants.json'
    vowel_file_path = 'src/config/vowels.json'

    def __init__(self):
        self.consonants: dict[str, tuple[str, str]] = {}
        self.vowels: dict[str, tuple[str, str]] = {}
        self.disabled: dict[LetterType, list[str]] = {LetterType.CONSONANT: [], LetterType.VOWEL: []}
        self.tables: dict[LetterType, list[list[str]]] = {LetterType.CONSONANT: [], LetterType.VOWEL: []}
        self.borders: dict[LetterType, list[str]] = {LetterType.CONSONANT: [], LetterType.VOWEL: []}
        self.types: dict[LetterType, list[str]] = {LetterType.CONSONANT: [], LetterType.VOWEL: []}
        self.all: dict[str, tuple[CharacterType, Optional[list]]] = {
            SYLLABLE_SEPARATOR: (CharacterType.SEPARATOR, None)}

        # Load data for consonants and vowels
        self._load_letters(self.consonant_file_path, LetterType.CONSONANT)
        self._load_letters(self.vowel_file_path, LetterType.VOWEL)

    def _load_letters(self, file_path: str, letter_type: LetterType) -> None:
        """
        A helper method to load letters, borders, and types from a file.
        Updates corresponding tables and dictionaries.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        table = data['letters']
        borders = data['borders']
        types = data['types']
        disabled = data['disabled']

        # Populate dictionaries
        letters: dict[str, tuple[str, str]] = {}
        for i, row in enumerate(table):
            for j, letter in enumerate(row):
                border, typ = borders[i], types[j]
                letters[letter] = (border, typ)
                if letter not in disabled:
                    self.all[letter] = CharacterType.LETTER, [letter_type, border, typ]

        # Determine which attributes to update based on letter type
        if letter_type == LetterType.CONSONANT:
            table_attr = 'consonant_table'
            letters_attr = 'consonants'
        else:
            table_attr = 'vowel_table'
            letters_attr = 'vowels'

        setattr(self, letters_attr, letters)
        setattr(self, table_attr, table)

        self.disabled[letter_type] = disabled
        self.tables[letter_type] = table
        self.borders[letter_type] = borders
        self.types[letter_type] = types


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
