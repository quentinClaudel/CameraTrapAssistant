"""Main entry point for Camera Trap Assistant."""

import multiprocessing
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def _show_startup_error(message: str) -> None:
    # Always report on the error stream first. A packaged application that only
    # opens a dialog gives a release build no way to say what went wrong.
    print(message, file=sys.stderr)
    try:
        from tkinter import messagebox

        messagebox.showerror("Camera Trap Assistant", message)
    except Exception:
        pass


def main():
    """Main entry point - launches the GUI."""
    from utils.model_manager import format_model_problems, validate_models

    model_problems = validate_models()
    if model_problems:
        _show_startup_error(format_model_problems(model_problems))
        return 1

    try:
        from gui.main_window import main as gui_main

        if "--smoke-test" in sys.argv:
            from PIL import Image
            from gui.utils.config import load_checkbox_state
            from models.classifTools import Classifier
            from models.detectTools import Detector, DFYOLO_NAME, MDSYOLO_NAME
            from utils.exiftool_interface import exiftool_is_available, run_exiftool
            from utils.resource_manager import get_icon_path

            load_checkbox_state()
            for icon_name in (
                "folder.png",
                "run.png",
                "github-mark.png",
                "kofi_symbol.png",
            ):
                with Image.open(get_icon_path(icon_name)) as icon:
                    icon.verify()
            if not exiftool_is_available():
                raise FileNotFoundError("Bundled ExifTool was not found")
            exiftool_version = run_exiftool(["-ver"])
            if exiftool_version.returncode != 0 or not exiftool_version.stdout.strip():
                raise RuntimeError(
                    f"Bundled ExifTool failed: {exiftool_version.stderr.strip()}"
                )
            Classifier(device="cpu")
            Detector(name=DFYOLO_NAME, device="cpu")
            Detector(name=MDSYOLO_NAME, device="cpu")
            return 0
        gui_main()
    except ImportError as e:
        if "--smoke-test" in sys.argv:
            # A failing release build needs the full import chain, not a summary.
            import traceback

            traceback.print_exc()
        _show_startup_error(
            f"Could not load an application dependency:\n\n{e}\n\n"
            "Install the application again from the official release."
        )
        return 1
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
