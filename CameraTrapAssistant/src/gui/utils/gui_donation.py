import tkinter as tk
import webbrowser
from PIL import Image, ImageTk
from utils.resource_manager import get_icon_path

LINK_NORMAL = "#1a73e8"
LINK_HOVER = "#0b5ed7"

def load_icon_high_quality(filename: str, target_height: int = 18) -> tk.PhotoImage | None:
    """
    Load an icon from the global icons folder and resize with high-quality LANCZOS filter.
    Returns a Tk PhotoImage or None on failure.
    """
    try:
        img = Image.open(get_icon_path(filename)).convert("RGBA")
        w, h = img.size
        if h > 0 and h != target_height:
            new_w = max(1, round(w * (target_height / h)))
            img = img.resize((new_w, target_height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def create_support_link_label(parent: tk.Widget, text: str = "Support the App", url: str = "https://ko-fi.com/bernigaudnoe", target_height: int = 18) -> tk.Label:
    """
    Create a hyperlink-styled label for support with Ko‑fi icon and hover effects.
    """
    icon = load_icon_high_quality("kofi_symbol.png", target_height)
    lbl = tk.Label(
        parent,
        text=text,
        fg=LINK_NORMAL,
        cursor="hand2",
        font=("Arial", 10, "underline"),
        image=icon,
        compound=tk.LEFT,
        padx=4
    )
    lbl.image = icon  # prevent GC

    def _open(_evt=None):
        webbrowser.open(url, new=1)

    lbl.bind("<Button-1>", _open)
    lbl.bind("<Enter>", lambda e: lbl.config(fg=LINK_HOVER))
    lbl.bind("<Leave>", lambda e: lbl.config(fg=LINK_NORMAL))
    return lbl

def show_support_nudge(parent: tk.Tk) -> None:
    """
    Show a small, friendly dialog suggesting support every few runs.
    """
    top = tk.Toplevel(parent)
    top.title("Support Camera Trap Assistant")
    top.transient(parent)
    top.grab_set()
    top.resizable(False, False)
    try:
        # Center over parent
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w, h = 420, 140
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        top.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

    msg = tk.Label(
        top,
        text="Love using Camera Trap Assistant?" \
        "\nYour support helps fund new features for wildlife enthusiasts everywhere!",
        wraplength=380,
        justify="center",
        font=("Arial", 11)
    )
    msg.pack(padx=16, pady=(18, 12))

    btns = tk.Frame(top)
    btns.pack(pady=(0, 14))

    def close():
        top.destroy()

    later = tk.Button(btns, text="Maybe Later", command=close, width=16)
    later.pack(side=tk.LEFT, padx=6)
    # Hyperlink-styled support control with icon
    support_lbl = create_support_link_label(btns)
    support_lbl.pack(side=tk.LEFT, padx=6)
