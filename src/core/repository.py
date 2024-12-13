from __future__ import annotations

import json
from typing import Optional, List, Dict, Tuple

from .components.letters import LetterType

_repository: Optional[_CharacterRepository] = None  # Global repository instance


class _CharacterRepository:
    consonant_file_path = 'src/config/consonants.json'
    vowel_file_path = 'src/config/vowels.json'

    def __init__(self):
        self.letters: Dict[LetterType, Dict[str, Tuple[str, str]]] = {LetterType.CONSONANT: {}, LetterType.VOWEL: {}}
        self.tables: Dict[LetterType, List[List[str]]] = {LetterType.CONSONANT: [], LetterType.VOWEL: []}
        self.borders: Dict[LetterType, List[str]] = {LetterType.CONSONANT: [], LetterType.VOWEL: []}
        self.types: Dict[LetterType, List[str]] = {LetterType.CONSONANT: [], LetterType.VOWEL: []}
        self.all: Dict[str, Tuple[LetterType, str, str]] = {}

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

        # Determine which attributes to update based on letter type
        table_attr = 'consonant_table' if letter_type == LetterType.CONSONANT else 'vowel_table'
        table = data['letters']
        setattr(self, table_attr, table)

        borders = data['borders']
        types = data['types']

        # Populate dictionaries
        for i, row in enumerate(table):
            for j, letter in enumerate(row):
                border, typ = borders[i], types[j]
                self.letters[letter_type][letter] = (border, typ)
                self.all[letter] = (letter_type, border, typ)

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
