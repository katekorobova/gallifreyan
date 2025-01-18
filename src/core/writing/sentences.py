import random
from itertools import repeat, takewhile
from tkinter import Canvas, Event
from typing import Optional

from PIL import Image

from .characters import CharacterType, LetterType, Character, Separator, Space
from .consonants import Consonant
from .vowels import Vowel
from .words import Word, SpaceWord, AbstractWord
from .. import repository
from ..utils import Point
from ...config import CANVAS_WIDTH, CANVAS_HEIGHT, DEFAULT_WORD_RADIUS


def get_character(text: str, typ: CharacterType, args: Optional[list]) -> Character:
    def get_letter(letter_text: str, letter_type: LetterType, *letter_args):
        if letter_type == LetterType.CONSONANT:
            return Consonant.get_consonant(letter_text, *letter_args)
        elif letter_type == LetterType.VOWEL:
            return Vowel.get_vowel(letter_text, *letter_args)
        else:
            raise ValueError(f"There is no such letter type: '{letter_type}' (symbol='{letter_text}')")

    if typ == CharacterType.LETTER:
        return get_letter(text, *args)
    elif typ == CharacterType.SEPARATOR:
        return Separator(text)
    elif typ == CharacterType.SPACE:
        return Space(text)
    else:
        raise ValueError(f"There is no such character type: '{typ}' (symbol='{text}')")


def split_into_words(characters: list[Character]) -> list[tuple[list[Character], bool]]:
    words: list[tuple[list[Character], bool]] = []
    is_space = False
    current_word = []
    for character in characters:
        if (character.character_type == CharacterType.SPACE) == is_space:
            current_word.append(character)
        else:
            if current_word:
                words.append((current_word, is_space))
            is_space = not is_space
            current_word = [character]
    if current_word:
        words.append((current_word, is_space))
    return words


def unique_words(items: list[AbstractWord]) -> list[AbstractWord]:
    """Return a list of unique items while preserving order."""
    seen = set()
    return [item for item in items if not (item in seen or seen.add(item))]


class Sentence:
    def __init__(self):
        self.words: list[Word] = []
        self.pressed: Optional[Word] = None
        self._ids_for_removal: list[int] = []
        self.words_by_indices: list[Optional[AbstractWord]] = []
        self.characters: list[Character] = []

    # =============================================
    # Mouse events
    # =============================================
    def press(self, event: Event):
        """Handle mouse button press on canvas."""
        for word in reversed(self.words):
            if word and word.press(Point(event.x, event.y)):
                self.pressed = word
                return

    def move(self, event: Event) -> bool:
        """Handle mouse drag movement."""
        if self.pressed:
            self.pressed.move(Point(event.x, event.y))
            return True
        return False

    def release(self):
        """Handle mouse button release."""
        self.pressed = None

    # =============================================
    # Deletion
    # =============================================
    def remove_characters(self, index: int, deleted: str):
        """Remove letters from the sentence."""
        end_index = index + len(deleted)
        deleted_words = unique_words(self.words_by_indices[index:end_index])

        first_word = deleted_words[0]
        first_word_start = self.words_by_indices.index(first_word)

        if len(deleted_words) == 1:
            first_word.remove_characters(index - first_word_start, end_index - first_word_start)
        else:
            second_word = deleted_words[1]
            second_word_start = self.words_by_indices.index(second_word)
            first_word.remove_characters(index - first_word_start, second_word_start - first_word_start)

            last_word = deleted_words[-1]
            last_word_start = self.words_by_indices.index(last_word)
            last_word.remove_characters(0, end_index - last_word_start)

        self._clean_up_removed(index, end_index)
        self._absorb_following_word(index)

    def _absorb_following_word(self, index: int):
        if not 0 < index < len(self.characters):
            return

        preceding_word = self.words_by_indices[index - 1]
        following_word = self.words_by_indices[index]
        if preceding_word is following_word:
            return

        following_characters = following_word.characters
        following_len = len(following_characters)

        if preceding_word.insert_characters(index - self.words_by_indices.index(preceding_word),
                                            following_characters):
            self.words_by_indices[index: index + following_len] = repeat(preceding_word, following_len)
            if isinstance(following_word, Word):
                self.words.remove(following_word)
                self._ids_for_removal.append(following_word.canvas_item_id)

    def _clean_up_removed(self, index: int, end_index: int):
        self.characters[index:end_index] = []
        self.words_by_indices[index:end_index] = []
        self.words = [word for word in self.words if
                      (word in self.words_by_indices or self._ids_for_removal.append(word.canvas_item_id))]

    # =============================================
    # Insertion
    # =============================================
    def insert_characters(self, index: int, inserted: str):
        """Insert characters at a specific index and update words."""
        characters = [get_character(char, *repository.get().all[char]) for char in inserted]
        self.characters[index: index] = characters

        words_with_space_indicators = split_into_words(characters)
        if len(words_with_space_indicators) == 1:
            self._insert_single_word(index, *words_with_space_indicators[0])
        else:
            self._insert_multiple_words(index, words_with_space_indicators)

    def _insert_single_word(self, index: int, word_chars: list[Character], is_space: bool):
        """Insert a single word at a specific index."""
        word_len = len(word_chars)
        preceding_word = self.words_by_indices[index - 1] if index > 0 else None
        following_word = self.words_by_indices[index] if index < len(self.words_by_indices) else None

        if preceding_word and preceding_word.insert_characters(
                index - self.words_by_indices.index(preceding_word), word_chars):
            self.words_by_indices[index:index] = repeat(preceding_word, word_len)
        elif following_word and following_word.insert_characters(0, word_chars):
            self.words_by_indices[index:index] = repeat(following_word, word_len)
        else:
            self._split_word(index)
            word = self._new_word(word_chars, is_space)

            self.words_by_indices[index:index] = repeat(word, word_len)
            self._absorb_nones(index + word_len, word)

    def _insert_multiple_words(self, index: int, words_with_space_indicators: list[tuple[list[Character], bool]]):
        """Insert multiple words at a specific index."""
        self._split_word(index)
        preceding_word = self.words_by_indices[index - 1] if index > 0 else None
        following_word = self.words_by_indices[index] if index < len(self.words_by_indices) else None

        word_chars, is_space = words_with_space_indicators[0]
        word_len = len(word_chars)

        if preceding_word and preceding_word.insert_characters(
                index - self.words_by_indices.index(preceding_word), word_chars):
            self.words_by_indices[index:index] = repeat(preceding_word, word_len)
        else:
            word = self._new_word(word_chars, is_space)
            self.words_by_indices[index:index] = repeat(word, word_len)

        current_index = index + word_len
        for word_chars, is_space in words_with_space_indicators[1:-1]:
            word_len = len(word_chars)
            word = self._new_word(word_chars, is_space)
            self.words_by_indices[current_index:current_index] = repeat(word, word_len)
            current_index += word_len

        word_chars, is_space = words_with_space_indicators[-1]
        word_len = len(word_chars)

        if following_word and following_word.insert_characters(0, word_chars):
            self.words_by_indices[current_index: current_index] = repeat(following_word, word_len)
        else:
            word = self._new_word(word_chars, is_space)
            self.words_by_indices[current_index: current_index] = repeat(word, word_len)
            self._absorb_nones(current_index + word_len, word)

    def _split_word(self, index: int):
        """Split the word at the specified index, updating words as needed."""
        if 0 < index < len(self.words_by_indices):
            word = self.words_by_indices[index - 1]
            if word and word is self.words_by_indices[index]:
                word.remove_starting_with(index - self.words_by_indices.index(word))
                for i in range(index, len(self.words_by_indices)):
                    if word is self.words_by_indices[i]:
                        self.words_by_indices[i] = None
                    else:
                        return

    def _new_word(self, characters: list[Character], is_space) -> Word:
        if is_space:
            word = SpaceWord(characters)
        else:
            word = Word(Point(random.randint(DEFAULT_WORD_RADIUS, CANVAS_WIDTH - DEFAULT_WORD_RADIUS),
                              random.randint(DEFAULT_WORD_RADIUS, CANVAS_HEIGHT - DEFAULT_WORD_RADIUS)), characters)
            self.words.append(word)
        return word

    def _absorb_nones(self, index: int, preceding_word: AbstractWord):
        if index >= len(self.characters):
            return

        remaining = [self.characters[i] for i in takewhile(
            lambda i: not self.words_by_indices[i], range(index, len(self.characters)))]
        is_space = all(char.character_type == CharacterType.SPACE for char in remaining)
        remaining_len = len(remaining)

        if preceding_word.insert_characters(index - self.words_by_indices.index(preceding_word), remaining):
            word = preceding_word
        else:
            word = self._new_word(remaining, is_space)

        self.words_by_indices[index: index + remaining_len] = repeat(word, remaining_len)

    # =============================================
    # Drawing
    # =============================================
    def get_image(self) -> Optional[Image.Image]:
        if not self.words:
            return None

        image = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT))
        for word in self.words:
            word_image = word.get_image()
            image.paste(word_image, tuple(word.center - Word.IMAGE_CENTER), word_image)
        return image

    def put_image(self, canvas: Canvas):
        for item_id in self._ids_for_removal:
            canvas.delete(item_id)
            self._ids_for_removal.clear()
        for word in self.words:
            word.put_image(canvas)

    def apply_color_changes(self):
        for word in self.words:
            word.apply_color_changes()

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self):
        direction_sign = 1
        for word in self.words:
            word.perform_animation(direction_sign)
            direction_sign = -direction_sign
