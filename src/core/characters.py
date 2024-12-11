import json
from typing import Dict, List, Tuple

from .components import LetterType


class CharacterRepository:
    def __init__(self, consonant_file: str, vowel_file: str):
        self.consonant_table: List[List[str]] = []
        self.consonant_borders: List[str] = []
        self.consonant_decorations: List[str] = []

        self.vowel_table: List[List[str]] = []
        self.vowel_borders: List[str] = []
        self.vowel_decorations: List[str] = []

        self.consonants: Dict[str, Tuple[str, str]] = {}
        self.vowels: Dict[str, Tuple[str, str]] = {}
        self.letters: Dict[str, Tuple[LetterType, str, str]] = {}

        # Load data for consonants and vowels
        self._load_letters(consonant_file, LetterType.CONSONANT)
        self._load_letters(vowel_file, LetterType.VOWEL)

    def _load_letters(self, file_path: str, letter_type: LetterType) -> None:
        """
        A helper method to load letters, borders, and decorations from a file.
        Updates corresponding tables and dictionaries.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Determine which attributes to update based on letter type
        table_attr = 'consonant_table' if letter_type == LetterType.CONSONANT else 'vowel_table'
        table = data['letters']
        setattr(self, table_attr, table)

        borders = data['borders']
        decorations = data['decorations']

        # Populate dictionaries
        for i, row in enumerate(table):
            for j, letter in enumerate(row):
                border, decoration = borders[i], decorations[j]
                if letter_type == LetterType.CONSONANT:
                    self.consonants[letter] = (border, decoration)
                else:
                    self.vowels[letter] = (border, decoration)

                self.letters[letter] = (letter_type, border, decoration)

        if letter_type == LetterType.CONSONANT:
            self.consonant_table = table
            self.consonant_borders = borders
            self.consonant_decorations = decorations
        else:
            self.vowel_table = table
            self.vowel_borders = borders
            self.vowel_decorations = decorations
