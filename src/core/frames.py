import tkinter as tk
from dataclasses import dataclass
from itertools import count, repeat
from typing import Dict, List, Optional

from PIL import Image, ImageTk

from src.utils import Point, unique, ALEPH, FONT, WINDOW_BG, \
    BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_IMAGE_SIZE, \
    CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_BG, \
    WORD_INITIAL_POSITION, BUTTON_BG
from .characters import CharacterRepository
from .components import LetterType, Letter, Consonant, Vowel, Syllable, Word


def get_letter(text: str, typ: LetterType, border: str, decoration_code: str):
    match typ:
        case LetterType.CONSONANT:
            return Consonant.get_consonant(text, border, decoration_code)
        case LetterType.VOWEL:
            return Vowel.get_vowel(text, border, decoration_code)
        case _:
            raise ValueError(f'There is no such letter type: {typ} (letter={text})')


class LetterButton(tk.Button):
    def __init__(self, master: tk.Frame, letter: str, entry: tk.Entry):
        super().__init__(master, text=letter, font=FONT,
                         height=BUTTON_HEIGHT, width=BUTTON_WIDTH,
                         command=lambda: entry.insert(tk.INSERT, letter))


class LetterFrame(tk.Frame):
    def __init__(self, win: tk.Tk, borders: List[str], decorations: List[str],
                 letters: List[List[str]], entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self.images = []
        self.buttons: Dict[str, tk.Button] = {}

        self._initialize_grid(borders, decorations)
        self._add_buttons(letters, entry)

    def _initialize_grid(self, borders: List[str], decorations: List[str]):
        tk.Label(self, relief='raised', bg=BUTTON_BG).grid(row=0, column=0, sticky='news')

        for i, border in enumerate(borders):
            self._add_image_button(f'assets/images/borders/{border}.png', row=i + 1, column=0)

        for j, decoration in enumerate(decorations):
            self._add_image_button(f'assets/images/decorations/{decoration}.png', row=0, column=j + 1)

    def _add_image_button(self, path: str, row: int, column: int):
        image = Image.open(path).resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
        image_tk = ImageTk.PhotoImage(image)
        self.images.append(image_tk)
        tk.Label(self, image=image_tk, bg=BUTTON_BG, relief='raised').grid(row=row, column=column, sticky='news')

    def _add_buttons(self, letters: List[List[str]], entry: tk.Entry):
        for i, row in enumerate(letters):
            for j, letter in enumerate(row):
                button = LetterButton(self, letter, entry)
                self.buttons[letter] = button
                button.grid(row=i + 1, column=j + 1, sticky='news')


class CanvasFrame(tk.Frame):

    def __init__(self, win: tk.Tk, writing_system: CharacterRepository):
        super().__init__(win, bg=WINDOW_BG)
        self.writing_system = writing_system

        # Entry widget with validation
        self.entry = tk.Entry(
            self, font=FONT, validate='key',
            validatecommand=(self.register(self._attempt_action), '%d', '%i', '%S')
        )
        self.entry.grid(row=0, column=0, sticky='news')

        # Canvas for drawing
        self.canvas = tk.Canvas(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=CANVAS_BG)
        self.canvas.grid(row=1, column=0)

        # Canvas event bindings
        self._bind_canvas_events()

        # State management
        self.syllables: List[Optional[Syllable]] = []
        self.letters: List[Letter] = []
        self.word: Optional[Word] = None
        self.pressed: Optional[Word] = None

    def _bind_canvas_events(self):
        """Bind mouse events to canvas actions."""
        self.canvas.bind('<Button-1>', self._press)
        self.canvas.bind('<B1-Motion>', self._move)
        self.canvas.bind('<ButtonRelease-1>', self._release)

    def _press(self, event: tk.Event):
        """Handle mouse button press on canvas."""
        if self.word and self.word.press(Point(event.x, event.y)):
            self.pressed = self.word

    def _move(self, event: tk.Event):
        """Handle mouse drag movement."""
        if self.pressed:
            self.pressed.move(Point(event.x, event.y))
            self._redraw()

    def _release(self, _):
        """Handle mouse button release."""
        self.pressed = None

    def _redraw(self):
        self.canvas.delete('all')
        if self.word:
            self.word.create_image(self.canvas)

    def _attempt_action(self, action: str, str_index: str, inserted: str) -> bool:
        match action:
            case '0':  # Deletion
                self._remove_letters(str_index, inserted)
                return True

            case '1':  # Insertion
                return self._attempt_insertion(str_index, inserted)

            case _:
                return False

    def _remove_letters(self, str_index: str, deleted: str):
        """Remove letters from the word and update syllables."""
        index = int(str_index)
        first = self.syllables[index]
        if index > 0 and self.syllables[index - 1] is first:
            first.remove_starting_with(self.letters[index])

        last = self.syllables[index + len(deleted) - 1]
        if index + len(deleted) < len(self.letters) and \
                self.syllables[index + len(deleted)] is last:
            self.syllables[index + len(deleted)] = None
            if index + len(deleted) < len(self.letters) - 1 and \
                    self.syllables[index + len(deleted) + 1] is last:
                self.syllables[index + len(deleted) + 1] = None

        self.letters[index: index + len(deleted)] = []
        self.syllables[index: index + len(deleted)] = []

        start = self._absorb_new_letters(index)
        self._redistribute(start)

        syllables = unique(self.syllables)
        if syllables:
            self.word.set_syllables(syllables)
            self._redraw()
        else:
            self.canvas.delete('all')
            self.word = None
            self.pressed = None

    def _attempt_insertion(self, str_index: str, inserted: str):
        """Attempt to insert letters at a specific index and update syllables."""
        valid = all(i in self.writing_system.letters for i in inserted)
        if not valid:
            return False

        index = int(str_index)
        inserted_letters = [get_letter(letter, *self.writing_system.letters[letter])
                            for letter in inserted]

        self._split_syllable(index)
        self.letters[index: index] = inserted_letters
        self.syllables[index: index] = repeat(None, len(inserted))

        start = self._absorb_new_letters(index)
        self._redistribute(start)

        syllables = unique(self.syllables)
        if self.word:
            self.word.set_syllables(syllables)
        else:
            self.word = Word(Point(*WORD_INITIAL_POSITION), syllables)
        self._redraw()
        return True

    def _split_syllable(self, index: int):
        """Split the syllable at the specified index, updating syllables as needed."""
        if index > 0:
            syllable = self.syllables[index - 1]
            if index < len(self.letters) and syllable is self.syllables[index]:
                syllable.remove_starting_with(self.letters[index])
                self.syllables[index] = None
                if index < len(self.letters) - 1 and syllable is self.syllables[index + 1]:
                    self.syllables[index + 1] = None

    def _absorb_new_letters(self, index: int) -> int:
        """Absorb newly inserted letters into existing syllables."""
        start = index
        if index > 0:
            syllable = self.syllables[index - 1]
            for i in range(index, len(self.letters)):
                if syllable.add(self.letters[i]):
                    self.syllables[i] = syllable
                    start = i + 1
                else:
                    break
        return start

    @dataclass
    class RedistributionState:
        syllable: Optional[Syllable] = None
        cons2: Optional[Consonant] = None
        completed = False

    def _redistribute(self, start: int) -> None:
        """Redistribute syllables starting from a given index."""
        state = self.RedistributionState()
        for i, letter in zip(count(start), self.letters[start:]):
            if isinstance(letter, Consonant):
                self._process_consonant(i, letter, state)
            elif isinstance(letter, Vowel):
                self._process_vowel(i, letter, state)
            else:
                raise ValueError(f"No such letter type: {letter.letter_type} (letter={letter.text})")
            if state.completed:
                break

    def _process_consonant(self, index: int, letter: Consonant, state: RedistributionState) -> None:
        """Process consonant letters and update syllables."""
        if state.syllable:
            if not state.cons2 and state.syllable.add(letter):
                state.cons2 = letter
                self.syllables[index] = state.syllable
            else:
                if self._check_syllable_start(index, letter):
                    state.completed = True
                else:
                    state.syllable = Syllable(letter)
                    state.cons2 = None
                    self.syllables[index] = state.syllable
        else:
            if self._check_syllable_start(index, letter):
                state.completed = True
            else:
                state.syllable = Syllable(letter)
                self.syllables[index] = state.syllable

    def _process_vowel(self, index: int, letter: Vowel, state: RedistributionState) -> None:
        """Process vowel letters and update syllables."""
        if state.syllable:
            state.syllable.add(letter)
            self.syllables[index] = state.syllable
            state.syllable = None
            state.cons2 = None
        else:
            if self.syllables[index]:
                state.completed = True
            else:
                aleph = Consonant.get_consonant(ALEPH, *self.writing_system.consonants[ALEPH])
                self.syllables[index] = Syllable(aleph, vowel=letter)

    def _check_syllable_start(self, index, letter) -> bool:
        return self.syllables[index] and self.syllables[index].cons1 is letter
