import tkinter as tk
from tkinter import filedialog, messagebox

from .config import PADX, PADY, WINDOW_BG
from .core import repository
from .core.components.characters import LetterType
from .core.frames import LetterFrame, CanvasFrame, SeparatorFrame

SAVE_ERROR = "Save Error"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._initialize_character_repository()
        self._create_frames()
        self._layout_frames()
        self._configure_window()

    def _configure_window(self):
        """Set up the main application window."""
        icon = tk.PhotoImage(file='src/assets/icon.png')
        self.iconphoto(False, icon)

        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Export as PNG", command=self._save_png)
        menu_bar.add_cascade(label="File", menu=file_menu)

        self.title('Gallifreyan')
        self.config(menu=menu_bar, bg=WINDOW_BG)
        self.update_idletasks()

        window_width = self.winfo_width()
        window_height = self.winfo_height()
        menu_height = self.winfo_rooty() - self.winfo_y()
        self.geometry(f"{window_width}x{window_height + menu_height}")

    @staticmethod
    def _initialize_character_repository():
        """Initialize the character repository from configuration files."""
        repository.initialize()

    def _create_frames(self):
        """Create all the frames used in the application."""
        self.canvas_frame = CanvasFrame(self)
        self.consonant_frame = LetterFrame(LetterType.CONSONANT, self, self.canvas_frame.entry)
        self.vowel_frame = LetterFrame(LetterType.VOWEL, self, self.canvas_frame.entry)
        self.separator_frame = SeparatorFrame('-', self, self.canvas_frame.entry)

    def _layout_frames(self):
        """Place the frames in the application window using a grid layout."""
        self.canvas_frame.grid(row=0, column=2, rowspan=2, padx=PADX, pady=PADY)
        self.consonant_frame.grid(row=0, column=0, columnspan=2, padx=PADX, pady=PADY)
        self.vowel_frame.grid(row=1, column=0, padx=PADX, pady=PADY)
        self.separator_frame.grid(row=1, column=1, padx=PADX, pady=PADY)

    def _save_png(self):
        """Save the current canvas content as a PNG file."""
        image = self.canvas_frame.get_image()
        name = self.canvas_frame.entry.get()

        if image is None:
            messagebox.showerror(SAVE_ERROR, "The canvas is empty.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save as",
            filetypes=[("PNG Files", "*.png")],
            initialfile=name, defaultextension=".png")

        if not filename:
            return  # User cancelled the save dialog

        if not filename.lower().endswith(".png"):
            messagebox.showerror(SAVE_ERROR, "File must have a .png extension.")
            return

        try:
            image.save(filename)
            messagebox.showinfo("Save Successful", f"Image saved as {filename}")
        except Exception as e:
            messagebox.showerror(SAVE_ERROR, f"Failed to save the image: {e}")


if __name__ == '__main__':
    app = App()
    app.mainloop()
