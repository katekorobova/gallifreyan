import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Callable

from PIL import Image

from .config import PADX, PADY, WINDOW_BG, CYCLE, DELAY
from .core import repository
from .core.components.characters import LetterType
from .core.frames import LettersFrame, CanvasFrame, SpecialCharactersFrame, ToolsFrame

SAVE_ERROR = "Save Error"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.animation_enabled = False
        self.animation_task_id: Optional[str] = None

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
        file_menu.add_command(label="Export as GIF", command=self._save_gif)
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
        self.consonants_frame = LettersFrame(LetterType.CONSONANT, self, self.canvas_frame.entry)
        self.vowels_frame = LettersFrame(LetterType.VOWEL, self, self.canvas_frame.entry)
        self.special_characters_frame = SpecialCharactersFrame(self, self.canvas_frame.entry)
        self.tools_frame = ToolsFrame(self, self._toggle_animation)

    def _layout_frames(self):
        """Place the frames in the application window using a grid layout."""
        self.consonants_frame.grid(row=0, column=0, columnspan=2, padx=PADX, pady=PADY, sticky='nw')
        self.vowels_frame.grid(row=1, column=0, rowspan=2, padx=PADX, pady=PADY, sticky='nw')
        self.special_characters_frame.grid(row=2, column=1, padx=PADX, pady=PADY, sticky='nw')
        self.canvas_frame.grid(row=0, column=2, rowspan=3, padx=PADX, pady=PADY, sticky='nw')

        self.tools_frame.grid(row=1, column=1, padx=PADX, pady=PADY, sticky='nw')
        self.rowconfigure(2, weight=1)
        self.columnconfigure(1, weight=1)

    def _animation_loop(self):
        self.canvas_frame.perform_animation()
        self.animation_task_id = self.after(DELAY, self._animation_loop)

    def _toggle_animation(self):
        if self.animation_enabled:
            self.after_cancel(self.animation_task_id)
            self.animation_enabled = False
        else:
            self.animation_task_id = self.after(DELAY, self._animation_loop)
            self.animation_enabled = True

    def _save_image(self, extension: str, callback: Callable[[Image.Image, str], None]):
        """Generic method to save the current canvas content as an image."""
        try:
            image = self.canvas_frame.sentence.get_image()
            name = self.canvas_frame.entry.get()

            if not image:
                messagebox.showerror(SAVE_ERROR, "The canvas is empty.")
                return

            filename = filedialog.asksaveasfilename(
                title=f"Save as {extension.upper()}",
                filetypes=[(f"{extension.upper()} Files", f"*.{extension}")],
                initialfile=name,
                defaultextension=f".{extension}")

            if not filename:
                return  # User cancelled the save dialog

            if not filename.lower().endswith(f".{extension}"):
                messagebox.showerror(SAVE_ERROR, f"File must have a .{extension} extension.")
                return

            callback(image, filename)
            messagebox.showinfo("Save Successful", f"Image saved as {filename}")
        except Exception as e:
            messagebox.showerror(SAVE_ERROR, f"Failed to save the image: {e}")

    def _save_png(self):
        """Save the current canvas content as a PNG file."""
        self._save_image("png", lambda image, filename: image.save(filename))

    def _save_gif(self):
        """Save the current canvas content as an animated GIF."""
        progress_window: Optional[tk.Toplevel] = None
        animation_enabled = self.animation_enabled
        if animation_enabled:
            self._toggle_animation()

        def save_gif(image, filename):
            nonlocal progress_window
            progress_window = ProgressWindow(self)

            images = []
            for i in range(1, CYCLE):
                self.canvas_frame.sentence.perform_animation()
                images.append(self.canvas_frame.sentence.get_image())
                progress_window.configure_progress_label(i)

            image.save(filename, save_all=True, append_images=images, duration=DELAY, loop=0)

        try:
            self._save_image("gif", save_gif)
        finally:
            if progress_window:
                progress_window.destroy()

            if animation_enabled:
                self._toggle_animation()


class ProgressWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.transient(master)
        self.geometry("300x100+500+500")
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.title("Wait")

        icon = tk.PhotoImage(file='src/assets/icon.png')
        self.iconphoto(False, icon)

        self.label = tk.Label(self)
        self.label.pack()
        self.configure_progress_label(0)

    def configure_progress_label(self, index: int):
        self.label.config(text="Your GIF is being processed: {:2.2f}%".format(99 * (index + 1) / CYCLE))
        self.label.master.update()


if __name__ == '__main__':
    app = App()
    app.mainloop()
