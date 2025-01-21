from __future__ import annotations

import json
from typing import Optional

from .writing.characters import CharacterType
from ..config import SEPARATOR, SPACE

_repository: Optional[_CharacterRepository] = None  # Global repository instance


class _CharacterRepository:
    CONSONANT_FILE_PATH = 'src/config/consonants.json'
    VOWEL_FILE_PATH = 'src/config/vowels.json'

    def __init__(self):
        self.consonants: dict[str, tuple[str, str]] = {}
        self.vowels: dict[str, tuple[str, str]] = {}
        self.digits: dict[str, tuple[str, str]] = {}

        self.disabled: dict[CharacterType, list[str]] = \
            {CharacterType.CONSONANT: [], CharacterType.VOWEL: []}
        self.tables: dict[CharacterType, list[list[str]]] = \
            {CharacterType.CONSONANT: [], CharacterType.VOWEL: []}
        self.borders: dict[CharacterType, list[str]] = \
            {CharacterType.CONSONANT: [], CharacterType.VOWEL: []}
        self.types: dict[CharacterType, list[str]] = \
            {CharacterType.CONSONANT: [], CharacterType.VOWEL: []}
        self.all: dict[str, tuple[CharacterType, Optional[tuple[str, str]]]] = {
            SEPARATOR: (CharacterType.SEPARATOR, None),
            SPACE: (CharacterType.SPACE, None)}

        # Load data for consonants and vowels
        self._load_characters(CharacterType.CONSONANT)
        self._load_characters(CharacterType.VOWEL)

    def _load_characters(self, character_type: CharacterType) -> None:
        """
        A helper method to load letters, borders, and types from a file.
        Updates corresponding tables and dictionaries.
        """
        if character_type == CharacterType.CONSONANT:
            file_path = self.CONSONANT_FILE_PATH
            table_attr = 'consonant_table'
            letters_attr = 'consonants'
        else:
            file_path = self.VOWEL_FILE_PATH
            table_attr = 'vowel_table'
            letters_attr = 'vowels'

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        table = data['characters']
        borders = data['borders']
        types = data['types']
        disabled = data['disabled']

        # Populate dictionaries
        letters: dict[str, tuple[str, str]] = {}
        for row, border in zip(table, borders):
            for letter, typ in zip(row, types):
                letters[letter] = (border, typ)
                if letter not in disabled:
                    self.all[letter] = character_type, (border, typ)

        setattr(self, letters_attr, letters)
        setattr(self, table_attr, table)

        self.disabled[character_type] = disabled
        self.tables[character_type] = table
        self.borders[character_type] = borders
        self.types[character_type] = types


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
