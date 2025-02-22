import math
from itertools import repeat, takewhile
from tkinter import Canvas, Event
from typing import Optional

from PIL import Image

from .characters import CharacterType, Character, Separator, Space, CharacterInfo, TokenType
from .characters.consonants import Consonant
from .characters.digits import Digit
from .characters.marks import PunctuationMark
from .characters.vowels import Vowel
from .numbers import Number, NumberMark
from .punctuation import PunctuationToken
from .words import Word, SpaceToken, Token, InteractiveToken
from .. import repository
from ..tools import AnimationProperties
from ..utils import Point


def get_character(text: str, character_info: CharacterInfo) -> Character:
    """Create a Character instance based on its type and properties."""
    character_type = character_info.character_type
    character_factories = {
        CharacterType.CONSONANT: Consonant.get_consonant,
        CharacterType.VOWEL: Vowel.get_vowel,
        CharacterType.SEPARATOR: Separator,
        CharacterType.SPACE: Space,
        CharacterType.DIGIT: Digit.get_digit,
        CharacterType.NUMBER_MARK: NumberMark,
        CharacterType.PUNCTUATION_MARK: PunctuationMark,
    }
    return character_factories[character_type](text, *character_info.properties)

def split_into_groups(characters: list[Character]) -> list[tuple[list[Character], TokenType]]:
    """Split a list of characters into groups with types."""
    groups: list[tuple[list[Character], TokenType]] = []
    current_group = []
    current_type = TokenType.WORD
    for character in characters:
        token_type = character.character_type.token_type
        if token_type == current_type:
            current_group.append(character)
        else:
            if current_group:
                groups.append((current_group, current_type))
            current_type = token_type
            current_group = [character]

    if current_group:
        groups.append((current_group, current_type))
    return groups


def unique_tokens(items: list[Token]) -> list[Token]:
    """Return a list of unique words while preserving their original order."""
    seen = set()
    return [item for item in items if not (item in seen or seen.add(item))]


class Sentence:
    """Represents a sentence composed of multiple words, supporting editing and rendering."""

    def __init__(self):
        """Initialize an empty Sentence object."""
        self.tokens_by_indices: list[Optional[Token]] = []
        self.visible_tokens: list[InteractiveToken] = []
        self.pressed_token: Optional[InteractiveToken] = None
        self.characters: list[Character] = []

    # =============================================
    # Mouse events
    # =============================================
    def press(self, event: Event) -> None:
        """Handle mouse button press on canvas."""
        point = Point(event.x, event.y)
        for token in reversed(self.visible_tokens):
            if token and token.press(point):
                self.pressed_token = token
                return

    def move(self, event: Event) -> bool:
        """Handle mouse drag movement."""
        if self.pressed_token:
            point = Point(event.x, event.y)
            self.pressed_token.move(point)
            return True
        return False

    def release(self) -> None:
        """Handle mouse button release."""
        self.pressed_token = None

    # =============================================
    # Deletion
    # =============================================
    def remove_characters(self, index: int, deleted: str) -> None:
        """Remove letters from the sentence."""
        end_index = index + len(deleted)
        removed_tokens = unique_tokens(self.tokens_by_indices[index:end_index])

        first_token = removed_tokens[0]
        first_token_start = self.tokens_by_indices.index(first_token)

        if len(removed_tokens) == 1:
            first_token.remove_characters(index - first_token_start, end_index - first_token_start)
        else:
            second_token = removed_tokens[1]
            second_token_start = self.tokens_by_indices.index(second_token)
            first_token.remove_characters(index - first_token_start, second_token_start - first_token_start)

            last_token = removed_tokens[-1]
            last_token_start = self.tokens_by_indices.index(last_token)
            last_token.remove_characters(0, end_index - last_token_start)

        self._clean_up_removed(index, end_index)
        self._absorb_following_token(index)

    def _absorb_following_token(self, index: int) -> None:
        """Merge the token at the given index with the preceding token if possible."""
        if not 0 < index < len(self.characters):
            return

        preceding_token = self.tokens_by_indices[index - 1]
        following_token = self.tokens_by_indices[index]
        if preceding_token is following_token:
            return

        following_characters = following_token.characters
        following_len = len(following_characters)

        if preceding_token.insert_characters(
                index - self.tokens_by_indices.index(preceding_token), following_characters):
            self.tokens_by_indices[index: index + following_len] = repeat(preceding_token, following_len)
            if following_token in self.visible_tokens:
                # noinspection PyTypeChecker
                self.visible_tokens.remove(following_token)

    def _clean_up_removed(self, index: int, end_index: int) -> None:
        """Remove characters and words in the given range and update the word list."""
        self.characters[index:end_index] = []
        self.tokens_by_indices[index:end_index] = []
        self.visible_tokens = [word for word in self.visible_tokens if word in self.tokens_by_indices]

    # =============================================
    # Insertion
    # =============================================
    def insert_characters(self, index: int, inserted: str):
        """Insert characters at the specified index and update words accordingly."""
        characters = [get_character(char, repository.get().all[char]) for char in inserted]
        self.characters[index: index] = characters

        groups_with_types = split_into_groups(characters)
        if len(groups_with_types) == 1:
            self._insert_single_token(index, *groups_with_types[0])
        else:
            self._insert_multiple_tokens(index, groups_with_types)

    def _insert_single_token(self, index: int, group_characters: list[Character], group_type: TokenType):
        """Insert a single token at the specified index, merging with adjacent words if possible."""
        group_length = len(group_characters)
        preceding_token = self.tokens_by_indices[index - 1] if index > 0 else None
        following_token = self.tokens_by_indices[index] if index < len(self.tokens_by_indices) else None

        if preceding_token and preceding_token.insert_characters(
                index - self.tokens_by_indices.index(preceding_token), group_characters):
            self.tokens_by_indices[index:index] = repeat(preceding_token, group_length)
        elif following_token and following_token.insert_characters(0, group_characters):
            self.tokens_by_indices[index:index] = repeat(following_token, group_length)
        else:
            self._split_token(index)
            token = self._new_token(group_characters, group_type)
            self.tokens_by_indices[index:index] = repeat(token, group_length)
            self._absorb_nones(index + group_length, token)

    def _insert_multiple_tokens(self, index: int, groups_with_types: list[tuple[list[Character], TokenType]]):
        """Insert multiple words at the specified index."""
        self._split_token(index)
        preceding_token = self.tokens_by_indices[index - 1] if index > 0 else None
        following_token = self.tokens_by_indices[index] if index < len(self.tokens_by_indices) else None

        group_characters, group_type = groups_with_types[0]
        group_length = len(group_characters)

        if preceding_token and preceding_token.insert_characters(
                index - self.tokens_by_indices.index(preceding_token), group_characters):
            self.tokens_by_indices[index:index] = repeat(preceding_token, group_length)
        else:
            token = self._new_token(group_characters, group_type)
            self.tokens_by_indices[index:index] = repeat(token, group_length)

        current_index = index + group_length
        for group_characters, group_type in groups_with_types[1:-1]:
            group_length = len(group_characters)
            token = self._new_token(group_characters, group_type)
            self.tokens_by_indices[current_index:current_index] = repeat(token, group_length)
            current_index += group_length

        group_characters, group_type = groups_with_types[-1]
        group_length = len(group_characters)

        if following_token and following_token.insert_characters(0, group_characters):
            self.tokens_by_indices[current_index: current_index] = repeat(following_token, group_length)
        else:
            token = self._new_token(group_characters, group_type)
            self.tokens_by_indices[current_index: current_index] = repeat(token, group_length)
            self._absorb_nones(current_index + group_length, token)

    def _split_token(self, index: int):
        """Split the token at the specified index, updating words as needed."""
        if 0 < index < len(self.tokens_by_indices):
            token = self.tokens_by_indices[index - 1]
            if token and token is self.tokens_by_indices[index]:
                token.remove_starting_with(index - self.tokens_by_indices.index(token))
                for i in range(index, len(self.tokens_by_indices)):
                    if token is self.tokens_by_indices[i]:
                        self.tokens_by_indices[i] = None
                    else:
                        break

    def _new_token(self, group_characters: list[Character], token_type: TokenType) -> Token:
        """Create a new token from the given characters."""
        match token_type:
            case TokenType.SPACE:
                token = SpaceToken(group_characters)
            case TokenType.WORD:
                token = Word(group_characters)
                self.visible_tokens.append(token)
            case TokenType.NUMBER:
                token = Number(group_characters)
                self.visible_tokens.append(token)
            case TokenType.PUNCTUATION:
                token = PunctuationToken(group_characters)
                self.visible_tokens.append(token)
            case _:
                raise ValueError(f"No such word type: '{token_type}'")
        return token

    def _absorb_nones(self, index: int, preceding_token: Token):
        """Absorb trailing None entries in tokens_by_indices into the preceding token."""
        if index >= len(self.characters):
            return

        remaining_characters = [self.characters[i] for i in takewhile(
            lambda i: not self.tokens_by_indices[i], range(index, len(self.characters)))]
        remaining_length = len(remaining_characters)

        if preceding_token.insert_characters(
                index - self.tokens_by_indices.index(preceding_token), remaining_characters):
            token = preceding_token
        else:
            token_type = self.characters[index].character_type.token_type
            token = self._new_token(remaining_characters, token_type)

        self.tokens_by_indices[index: index + remaining_length] = repeat(token, remaining_length)

    # =============================================
    # Drawing
    # =============================================
    def get_image(self, start: Point, end: Point) -> Optional[Image.Image]:
        """Generate an image representing the sentence."""
        image = Image.new('RGBA', (end - start).tuple())
        for token in self.visible_tokens:
            token.paste_image(image, start)
        return image

    def put_image(self, canvas: Canvas):
        """Render the sentence onto a given Tkinter canvas."""
        to_be_removed = list(canvas.find_all())
        for token in self.visible_tokens:
            token.put_image(canvas, to_be_removed)

        for item in to_be_removed:
            canvas.delete(item)

    def apply_color_changes(self):
        """Apply any color scheme changes to the sentence."""
        for token in self.visible_tokens:
            token.apply_color_changes()

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self):
        """Apply animation effects to the sentence."""
        angle = 2 * math.pi / AnimationProperties.cycle
        for token in self.visible_tokens:
            token.perform_animation(angle)
            angle = -angle
