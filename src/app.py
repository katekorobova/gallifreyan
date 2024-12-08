import tkinter as tk

from frames import CanvasFrame, ConsonantFrame, VowelFrame
from utils import PADX, PADY, WINDOW_BG
from writing import WritingSystem


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Gallifreyan')
        self.config(bg=WINDOW_BG)
        icon = tk.PhotoImage(file='images/icon.png')
        self.iconphoto(False, icon)

        writing_system = WritingSystem('config/consonants.json', 'config/vowels.json')

        self.canvas_frame = CanvasFrame(self, writing_system)
        self.consonant_frame = ConsonantFrame(self, writing_system.consonant_borders,
                                              writing_system.consonant_decorations,
                                              writing_system.consonant_table, self.canvas_frame.entry)
        self.vowel_frame = VowelFrame(self, writing_system.vowel_borders, writing_system.vowel_decorations,
                                      writing_system.vowel_table, self.canvas_frame.entry)

        self.canvas_frame.grid(row=0, column=1, rowspan=2, padx=PADX, pady=PADY)
        self.consonant_frame.grid(row=0, column=0, padx=PADX, pady=PADY)
        self.vowel_frame.grid(row=1, column=0, padx=PADX, pady=PADY)


if __name__ == '__main__':
    app = App()
    app.mainloop()
