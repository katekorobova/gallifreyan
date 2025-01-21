import logging
import tkinter as tk

from . import DefaultFrame, DefaultLabel, DefaultCanvas
from ...config import ITEM_BG, TEXT_COLOR, PADX, PADY, FONT
from ...core import repository
from ...core.writing.sentences import Sentence

padx = (0, PADX)
pady = (0, PADY)


class CanvasFrame(DefaultFrame):
    """
    A frame containing a canvas for drawing and an entry field for text input.
    This class manages user interactions with the canvas and the associated sentence object.
    """

    def __init__(self, win: tk.Tk):
        super().__init__(win)
        self.sentence = Sentence()

        label = DefaultLabel(self, text='Start Typing Your Transcription Here')

        # Entry widget with validation
        self.entry = tk.Entry(
            self, font=FONT, fg=TEXT_COLOR, bg=ITEM_BG, insertbackground=TEXT_COLOR,
            bd=2, relief=tk.RAISED, validate='key',
            validatecommand=(self.register(self._attempt_action), '%d', '%i', '%S'))

        # Canvas for drawing
        self.canvas = DefaultCanvas(self)

        label.grid(row=0, column=0, padx=PADX, sticky=tk.W)
        self.entry.grid(row=1, column=0, padx=PADX, sticky=tk.NSEW)
        self.canvas.grid(row=2, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)

        # Canvas event bindings
        self._bind_canvas_events()

    def perform_animation(self):
        """Trigger the animation process for the sentence and redraw the canvas."""
        self.sentence.perform_animation()
        self._redraw()

    def _bind_canvas_events(self):
        """Bind mouse events to canvas actions."""
        self.canvas.bind('<Button-1>', self._press)
        self.canvas.bind('<B1-Motion>', self._move)
        self.canvas.bind('<ButtonRelease-1>', self._release)

    def _press(self, event: tk.Event):
        """Handle mouse button press on canvas."""
        self.sentence.press(event)

    def _move(self, event: tk.Event):
        """Handle mouse drag movement."""
        if self.sentence.move(event):
            self._redraw()

    def _release(self, _):
        """Handle mouse button release."""
        self.sentence.release()

    def _redraw(self):
        """Update the displayed image."""
        self.sentence.put_image(self.canvas)

    def apply_color_changes(self):
        """Apply color changes to the sentence and update the displayed image."""
        self.sentence.apply_color_changes()
        self.sentence.put_image(self.canvas)

    def _attempt_action(self, action: str, str_index: str, inserted: str) -> bool:
        """Validate and process user input in the entry field."""
        try:
            index = int(str_index)
            match action:
                case '0':  # Deletion
                    self.sentence.remove_characters(index, inserted)
                    self._redraw()
                    return True

                case '1':  # Insertion
                    valid = all(i in repository.get().all for i in inserted)
                    if valid:
                        self.sentence.insert_characters(index, inserted)
                        self._redraw()
                        return True

                    return False

                case _:
                    return False

        except Exception as e:
            logging.exception(e)
            return False
