import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Callable, Optional

from PIL import Image

from ...config import CYCLE

SAVE_ERROR = "Save Error"


def save_image(image: Optional[Image.Image], name: str, extension: str, callback: Callable[[Image.Image, str], None]):
    """Generic method to save the current canvas content as an image."""
    try:
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


class ProgressWindow(tk.Toplevel):
    """A pop-up window displaying progress updates."""

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.withdraw()
        self.title("Wait")
        self.transient(master)
        self.geometry("300x100+500+500")
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.label = tk.Label(self)
        self.label.pack()
        self.configure_progress_label(0)
        self.deiconify()

    def configure_progress_label(self, index: int):
        """Updates the label to display the current progress."""
        self.label.config(text="Your GIF is being processed: {:2.2f}%".format(99 * (index + 1) / CYCLE))
        self.label.master.update()
