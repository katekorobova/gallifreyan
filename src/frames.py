import tkinter as tk
import traceback
from itertools import count, repeat
from typing import Dict, List

from PIL import Image, ImageTk

from letters import LetterType, Letter
from utils import Point, unique, ALEPH, FONT, WINDOW_BG, \
    BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_IMAGE_SIZE, \
    CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_BG
from writing import Syllable, WritingSystem, Consonant, Word


class LetterButton(tk.Button):

    def __init__(self, master: tk.Frame, letter: str, entry: tk.Entry):
        super().__init__(master, text=letter, font=FONT,
                         height=BUTTON_HEIGHT,
                         width=BUTTON_WIDTH,
                         command=LetterButton.get_button_command(letter, entry))

    @staticmethod
    def get_button_command(text: str, ent: tk.Entry):
        def button_command():
            ent.insert(tk.INSERT, text)

        return button_command


class ConsonantFrame(tk.Frame):

    def __init__(self, win: tk.Tk, borders: List[str], decorations: List[str],
                 letters: List[List[str]], entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self.images = []
        button = tk.Button(self, state='disabled')
        button.grid(row=0, column=0, sticky='news')
        for i, b in enumerate(borders):
            image = Image.open(f'images/{b}.png').resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
            image_tk = ImageTk.PhotoImage(image)
            self.images.append(image_tk)
            button = tk.Button(self, image=image_tk, state='disabled')
            button.grid(row=i + 1, column=0, sticky='news')
        for j, d in enumerate(decorations):
            image = Image.open(f'images/{d}.png').resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
            image_tk = ImageTk.PhotoImage(image)
            self.images.append(image_tk)
            button = tk.Button(self, image=image_tk, state='disabled')
            button.grid(row=0, column=j + 1, sticky='news')
        self.buttons: Dict[str, tk.Button] = {}
        for i in range(len(letters)):
            for j in range(len(letters[i])):
                letter = letters[i][j]
                button = LetterButton(self, letter, entry)
                self.buttons[letter] = button
                button.grid(row=i + 1, column=j + 1, sticky='news')


class VowelFrame(tk.Frame):

    def __init__(self, win: tk.Tk, borders: List[str], decorations: List[str],
                 letters: List[List[str]], entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self.images = []
        button = tk.Button(self, state='disabled')
        button.grid(row=0, column=0, sticky='news')
        for i, b in enumerate(borders):
            image = Image.open(f'images/{b}.png').resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
            image_tk = ImageTk.PhotoImage(image)
            self.images.append(image_tk)
            button = tk.Button(self, image=image_tk, state='disabled')
            button.grid(row=i + 1, column=0, sticky='news')
        for j, d in enumerate(decorations):
            image = Image.open(f'images/{d}.png').resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
            image_tk = ImageTk.PhotoImage(image)
            self.images.append(image_tk)
            button = tk.Button(self, image=image_tk, state='disabled')
            button.grid(row=0, column=j + 1, sticky='news')
        self.buttons: Dict[str, tk.Button] = {}
        for i in range(len(letters)):
            for j in range(len(letters[i])):
                letter = letters[i][j]
                button = LetterButton(self, letter, entry)
                self.buttons[letter] = button
                button.grid(row=i + 1, column=j + 1, stick='news')


class CanvasFrame(tk.Frame):

    def __init__(self, win: tk.Tk, writing_system: WritingSystem):
        super().__init__(win, bg=WINDOW_BG)
        self.writing_system = writing_system
        self.entry = tk.Entry(self, font=FONT,
                              validate='key',
                              validatecommand=(self.register(self.validate_text), '%d', '%i', '%P', '%S'))
        self.canvas = tk.Canvas(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=CANVAS_BG)
        self.canvas.bind('<Button-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.move)
        self.canvas.bind('<ButtonRelease-1>', self.release)

        self.entry.grid(row=0, column=0, stick='news')
        self.canvas.grid(row=1, column=0)
        self.syllables: List[Syllable | None] = []
        self.letters: List[Letter] = []
        # self.words: List[Word] = []
        self.word: Word | None = None

        self.pressed: Word | None = None

    def press(self, event):
        if self.word and self.word.press(Point(event.x, event.y)):
            self.pressed = self.word

    def move(self, event):
        if self.pressed:
            self.pressed.move(Point(event.x, event.y))
            self.redraw()

    def release(self, event):
        self.pressed = None

    def validate_text(self, action: str, str_index: str, text: str, inserted: str) -> bool:
        try:
            match action:
                case '0':
                    index = int(str_index)
                    first = self.syllables[index]
                    if index > 0 and self.syllables[index - 1] is first:
                        first.remove_starting_with(self.letters[index])

                    last = self.syllables[index + len(inserted) - 1]
                    if index + len(inserted) < len(self.letters) and \
                            self.syllables[index + len(inserted)] is last:
                        self.syllables[index + len(inserted)] = None
                        if index + len(inserted) < len(self.letters) - 1 and \
                                self.syllables[index + len(inserted) + 1] is last:
                            self.syllables[index + len(inserted) + 1] = None

                    self.letters[index: index + len(inserted)] = []
                    self.syllables[index: index + len(inserted)] = []

                    start = index
                    if index > 0:
                        # absorb first new letters
                        syllable = self.syllables[index - 1]
                        for i in range(index, len(self.letters)):
                            if syllable.add(self.letters[i]):
                                self.syllables[i] = syllable
                                start = i + 1
                            else:
                                break

                    self.redistribute(start)

                    syllables = unique(self.syllables)
                    if syllables:
                        self.word.set_syllables(syllables)
                        self.redraw()
                    else:
                        self.canvas.delete('all')
                        self.word = None
                        self.pressed = None
                    return True

                case '1':
                    valid = all(i in self.writing_system.letters for i in inserted)
                    if valid:
                        index = int(str_index)

                        inserted_letters = [Letter.get_letter(letter, *self.writing_system.letters[letter])
                                            for letter in inserted]

                        if index > 0:
                            # split the syllable
                            syllable = self.syllables[index - 1]
                            if index < len(self.letters) and syllable is self.syllables[index]:
                                syllable.remove_starting_with(self.letters[index])
                                self.syllables[index] = None
                                if index < len(self.letters) - 1 and syllable is self.syllables[index + 1]:
                                    self.syllables[index + 1] = None

                        self.letters[index: index] = inserted_letters
                        self.syllables[index: index] = repeat(None, len(inserted))

                        start = index
                        if index > 0:
                            # absorb first new letters
                            syllable = self.syllables[index - 1]
                            for i in range(index, len(self.letters)):
                                if syllable.add(self.letters[i]):
                                    self.syllables[i] = syllable
                                    start = i + 1
                                else:
                                    break

                        self.redistribute(start)

                        syllables = unique(self.syllables)
                        if self.word:
                            self.word.set_syllables(syllables)
                        else:
                            self.word = Word(Point(300, 300), syllables)
                        self.redraw()
                        return True

                    return valid
        except:
            traceback.print_exc()
        return False

    def redraw(self):
        self.canvas.delete('all')
        if self.word:
            self.word.create_image(self.canvas)

    def redistribute(self, start):
        syllable: Syllable | None = None
        cons2 = None
        for i, letter in zip(count(start), self.letters[start:]):
            match letter.letter_type:
                case LetterType.CONSONANT:
                    if syllable:
                        if not cons2 and syllable.add(letter):
                            cons2 = letter
                            self.syllables[i] = syllable
                        else:
                            if self.syllables[i] and self.syllables[i].cons1 is letter:
                                break
                            syllable = Syllable(letter)
                            cons2 = None
                            self.syllables[i] = syllable
                    else:
                        if self.syllables[i] and self.syllables[i].cons1 is letter:
                            break
                        syllable = Syllable(letter)
                        self.syllables[i] = syllable

                case LetterType.VOWEL:
                    if syllable:
                        syllable.add(letter)
                        self.syllables[i] = syllable
                        syllable = None
                        cons2 = None
                    else:
                        if self.syllables[i]:
                            break
                        self.syllables[i] = Syllable(
                            Consonant.get_consonant(ALEPH, *self.writing_system.consonants[ALEPH]), vowel=letter)
                case _:
                    raise ValueError(f'No such letter type: {letter.letter_type} (letter={letter.text})')
