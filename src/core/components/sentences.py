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
from ...config import CANVAS_WIDTH, CANVAS_HEIGHT, WORD_IMAGE_RADIUS


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


class Sentence:
    def __init__(self):
        self.words: list[Word] = []
        self.pressed: Optional[Word] = None
        self._ids_for_removal: list[int] = []
        self.words_by_indices: list[Optional[AbstractWord]] = []
        self.characters: list[Character] = []

    def press(self, event: Event):
        """Handle mouse button press on canvas."""
        for word in reversed(self.words):
            if word and word.press(Point(event.x, event.y)):
                self.pressed = word
                return

    def perform_animation(self):
        direction_sign = 1
        for word in self.words:
            word.perform_animation(direction_sign)
            direction_sign = -direction_sign

    def move(self, event: Event) -> bool:
        """Handle mouse drag movement."""
        if self.pressed:
            self.pressed.move(Point(event.x, event.y))
            return True
        return False

    def release(self):
        """Handle mouse button release."""
        self.pressed = None

    def put_image(self, canvas: Canvas):
        for item_id in self._ids_for_removal:
            canvas.delete(item_id)
            self._ids_for_removal.clear()
        for word in self.words:
            word.put_image(canvas)

    def remove_characters(self, index: int, deleted: str):
        """Remove letters from the sentence."""
        end_index = index + len(deleted)
        self._split_word(index)
        self._split_word(end_index)

        self.words = [word for word in self.words if word not in self.words_by_indices[index:end_index]]
        self.characters[index:end_index] = []
        self.words_by_indices[index:end_index] = []

        # Absorb any following characters into the preceding word
        preceding_word = self.words_by_indices[index - 1] if index > 0 else None
        self._absorb_following(index, preceding_word)

    def insert_characters(self, index: int, inserted: str):
        """Insert characters at a specific index and update words."""
        end_index = index + len(inserted)
        characters = [get_character(character, *repository.get().all[character])
                      for character in inserted]

        words = split_into_words(characters)
        word = self.words_by_indices[index - 1] if index > 0 else None
        if word and len(words) == 1 and \
                word.insert_characters(index - self.words_by_indices.index(word), characters):
            self.characters[index: index] = characters
            self.words_by_indices[index:index] = repeat(word, len(characters))
            return

        self._split_word(index)
        word_chars, is_space = words[0]
        word_len = len(word_chars)

        if not word or not word.insert_characters(index - self.words_by_indices.index(word), word_chars):
            word = self._new_word(is_space, word_chars)
        self.words_by_indices[index:index] = repeat(word, word_len)

        current_index = index + word_len
        for word_chars, is_space in words[1:]:
            word_len = len(word_chars)
            word = self._new_word(is_space, word_chars)
            self.words_by_indices[current_index:current_index] = repeat(word, word_len)
            current_index += word_len

        self.characters[index: index] = characters
        self._absorb_following(end_index, word)

    def _new_word(self, is_space, characters: list[Character]) -> Word:
        if is_space:
            word = SpaceWord(characters)
        else:
            word = Word(Point(random.randint(WORD_IMAGE_RADIUS, CANVAS_WIDTH - WORD_IMAGE_RADIUS),
                              random.randint(WORD_IMAGE_RADIUS, CANVAS_HEIGHT - WORD_IMAGE_RADIUS)), characters)
            self.words.append(word)
        return word

    def _absorb_following(self, index: int, preceding_word: Optional[AbstractWord]):
        if index >= len(self.characters):
            return

        following_word = self.words_by_indices[index]
        if following_word:
            following_characters = following_word.characters
            following_len = len(following_characters)
            if preceding_word and preceding_word \
                    .insert_characters(index - self.words_by_indices.index(preceding_word), following_characters):
                self.words_by_indices[index: index + following_len] = repeat(preceding_word, following_len)
                if isinstance(following_word, Word):
                    self.words.remove(following_word)
                    self._ids_for_removal.append(following_word.canvas_item_id)
        else:
            remaining = [self.characters[i] for i in takewhile(
                lambda i: not self.words_by_indices[i], range(index, len(self.characters)))]
            is_space = all(char.character_type == CharacterType.SPACE for char in remaining)
            remaining_len = len(remaining)
            if not preceding_word or not preceding_word \
                    .insert_characters(index - self.words_by_indices.index(preceding_word), remaining):
                preceding_word = self._new_word(is_space, remaining)
            self.words_by_indices[index: index + remaining_len] = repeat(preceding_word, remaining_len)

    def get_image(self) -> Optional[Image.Image]:
        if not self.words:
            return None

        image = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT))
        for word in self.words:
            word_image = word.get_image()
            image.paste(word_image, tuple(word.center - Word.IMAGE_CENTER), word_image)
        return image

    def _split_word(self, index: int):
        """Split the word at the specified index, updating words as needed."""
        if 0 < index < len(self.words_by_indices):
            word = self.words_by_indices[index - 1]
            if word and word is self.words_by_indices[index]:
                word.remove_starting_with(index - self.words_by_indices.index(word))
                for i in range(index, len(self.characters)):
                    if word is self.words_by_indices[i]:
                        self.words_by_indices[i] = None
                    else:
                        return