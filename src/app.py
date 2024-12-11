import tkinter as tk
from frames import LetterFrame, CanvasFrame
from utils import PADX, PADY, WINDOW_BG
from writing import WritingSystem


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._configure_window()
        self._initialize_writing_system()
        self._create_frames()
        self._layout_frames()

    def _configure_window(self):
        """Set up the main application window."""
        self.title('Gallifreyan')
        self.config(bg=WINDOW_BG)
        icon = tk.PhotoImage(file='images/icon.png')
        self.iconphoto(False, icon)

    def _initialize_writing_system(self):
        """Initialize the writing system from configuration files."""
        self.writing_system = WritingSystem('config/consonants.json', 'config/vowels.json')

    def _create_frames(self):
        """Create all the frames used in the application."""
        self.canvas_frame = CanvasFrame(self, self.writing_system)
        self.consonant_frame = LetterFrame(
            self,
            self.writing_system.consonant_borders,
            self.writing_system.consonant_decorations,
            self.writing_system.consonant_table,
            self.canvas_frame.entry
        )
        self.vowel_frame = LetterFrame(
            self,
            self.writing_system.vowel_borders,
            self.writing_system.vowel_decorations,
            self.writing_system.vowel_table,
            self.canvas_frame.entry
        )

    def _layout_frames(self):
        """Place the frames in the application window using a grid layout."""
        self.canvas_frame.grid(row=0, column=1, rowspan=2, padx=PADX, pady=PADY)
        self.consonant_frame.grid(row=0, column=0, padx=PADX, pady=PADY)
        self.vowel_frame.grid(row=1, column=0, padx=PADX, pady=PADY)


if __name__ == '__main__':
    app = App()
    app.mainloop()
