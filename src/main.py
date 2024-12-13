import tkinter as tk

from .core import repository
from .core.components.letters import LetterType
from .core.frames import LetterFrame, CanvasFrame
from .config import PADX, PADY, WINDOW_BG


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._configure_window()
        self._initialize_character_repository()
        self._create_frames()
        self._layout_frames()

    def _configure_window(self):
        """Set up the main application window."""
        self.title('Gallifreyan')
        self.config(bg=WINDOW_BG)
        icon = tk.PhotoImage(file='src/assets/icon.png')
        self.iconphoto(False, icon)

    @staticmethod
    def _initialize_character_repository():
        """Initialize the character repository from configuration files."""
        repository.initialize()

    def _create_frames(self):
        """Create all the frames used in the application."""
        self.canvas_frame = CanvasFrame(self)
        self.consonant_frame = LetterFrame(LetterType.CONSONANT, self, self.canvas_frame.entry)
        self.vowel_frame = LetterFrame(LetterType.VOWEL, self, self.canvas_frame.entry)

    def _layout_frames(self):
        """Place the frames in the application window using a grid layout."""
        self.canvas_frame.grid(row=0, column=1, rowspan=2, padx=PADX, pady=PADY)
        self.consonant_frame.grid(row=0, column=0, padx=PADX, pady=PADY)
        self.vowel_frame.grid(row=1, column=0, padx=PADX, pady=PADY)


if __name__ == '__main__':
    app = App()
    app.mainloop()
