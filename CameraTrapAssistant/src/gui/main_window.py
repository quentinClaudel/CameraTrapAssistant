import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import logging
from tkinter import ttk
import webbrowser
from PIL import Image, ImageTk
from pathlib import Path

# Import project utilities  
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.resource_manager import get_icon_path
from gui.utils.donation import show_support_nudge, create_support_link_label
from config.options_config import OptionsConfig
from core.run import runWithArgs
from gui.utils.logging import TkinterLogHandler
from gui.utils.main_loop import MainLoopDispatcher
from gui.utils.config import load_checkbox_state, save_checkbox_state, increment_run_count
from gui.utils.tooltip import CheckWithTooltip, LabelWithTooltip
from utils.time_utils.timeOffsetToTimezone import convert_to_timezone, time_offset_to_timezone



def on_main_thread(callback, *arguments):
    """
    Schedule a callback on the Tk main loop.

    Widgets and dialogs may only be touched from the thread running the main
    loop. On macOS a message box is a real AppKit alert, and AppKit terminates
    the process when a window is created on any other thread. Calling after()
    from the worker thread is not a fix on its own; see gui.utils.main_loop.
    """
    main_loop_dispatcher.post(callback, *arguments)


def run_in_thread(folder, options_config, lat, lon, csv_path=None):
    """
    Run the main processing in a background thread.

    Everything here runs off the main thread, so no Tk call may be made
    directly. Use on_main_thread for anything that touches the interface.
    """
    try:
        runWithArgs(folder, options_config, lat, lon, csv_path)
        on_main_thread(messagebox.showinfo, "Success", "Execution successful.")
    except Exception as e:
        on_main_thread(messagebox.showerror, "Error", f"Execution failure : {e}")
    finally:
        # The button is disabled for the duration of a run, so it has to be
        # restored however the run ended.
        on_main_thread(lambda: run_btn.config(state=tk.NORMAL))


def select_folder():
    """
    Handler for folder selection. Launches processing in a thread and saves checkbox state.
    """
    global folder
    folder = filedialog.askdirectory()
    if folder:
        label.config(text=f"{folder}")
        run_btn.config(state=tk.NORMAL)

def run():
    # Increment run count and disable button during processing
    run_btn.config(state=tk.DISABLED)
    log_handler.clear()
    options_config = OptionsConfig(
        generate_data = data_var.get(),
        generate_stats = stats_var.get(),
        move_empty = move_empty_var.get(),
        move_undefined = move_undefined_var.get(),
        rename_files = rename_var.get(),
        add_gps = gps_var.get(),
        prediction_threshold = threshold_var.get(),
        get_gps_from_each_file = get_gps_each_var.get(),
        use_gps_only_for_data = use_gps_only_for_data_var.get(),
        combine_with_data= combine_with_data_var.get(),
        time_offset = time_offset_var.get()
    )
    save_checkbox_state(options_config)
    lat, lon = None, None
    csv_path = None
    logging.info(f"run on folder {folder}")
    if options_config.combine_with_data:
        csv_path = filedialog.askopenfilename(
            title="Select CSV file to combine with",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not csv_path:
            messagebox.showerror("Error", "You must select a CSV file to combine with data.")
            run_btn.config(state=tk.NORMAL)
            return
    if options_config.add_gps:
        # Open map window automatically to select coordinates and wait for user
        from gui.utils.map import open_map_window, load_map_state
        # Create a modal Toplevel window for the map
        map_window = open_map_window(root, coord_var)
        if map_window is not None:
            map_window.grab_set()
            root.wait_window(map_window)
        lat, lon, _ = load_map_state()
        if lat is None or lon is None:
            messagebox.showerror("Error", "Please select coordinates on the map before adding GPS data.")
            run_btn.config(state=tk.NORMAL)
            return
    try:
        new_count = increment_run_count()
        logging.info(f"Run button clicked {new_count} time(s)")
        # Every 5 runs, nudge support
        if new_count % 5 == 0:
            try:
                show_support_nudge(root)
            except Exception as e:
                logging.info(f"Support nudge dialog failed: {e}")
        else:
            logging.info("No support nudge this time.")
    except Exception as e:
        logging.warning(f"Could not update run_count: {e}")
    threading.Thread(target=run_in_thread, args=(folder, options_config, lat, lon, csv_path), daemon=True).start()


def main():
    """
    Main entry point for the DeepFaune GUI.
    Sets up the window, widgets, and logging.
    """
    global root, folder, label, log_text, log_handler, main_loop_dispatcher
    global data_var, stats_var, move_empty_var, move_undefined_var, rename_var, get_gps_each_var, use_gps_only_for_data_var, threshold_var, combine_with_data_var, time_offset_var
    global gps_var, coord_var
    root = tk.Tk()
    root.title("Camera Trap Assistant")
    root.minsize(240, 120)
    root.geometry("1000x600")

    # Every interface update produced by the analysis thread travels through
    # this dispatcher. Started here, on the thread that owns the main loop.
    main_loop_dispatcher = MainLoopDispatcher(root)
    main_loop_dispatcher.start()

    # Folder selection and launch row
    folder_frame = tk.Frame(root)
    try:
        def load_icon(filename: str, target_height: int) -> tk.PhotoImage | None:
            try:
                icon_path = get_icon_path(filename)
                img = Image.open(str(icon_path)).convert("RGBA")
                w, h = img.size
                if h > 0 and h != target_height:
                    new_w = max(1, round(w * (target_height / h)))
                    img = img.resize((new_w, target_height), Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                return None

        # Target ~18px tall to align nicely with buttons
        folder_icon = load_icon("folder.png", 18)
        run_icon = load_icon("run.png", 18)
    except Exception:
        folder_icon = None
        run_icon = None
    # Use grid for better expansion and height control
    folder_frame.columnconfigure(0, weight=1)
    label = tk.Label(
        folder_frame,
        text="No folder chosen...",
        font=("Arial", 10, "italic"),
        bg="white",
        bd=1,
        relief=tk.SUNKEN,
        anchor="e"
    )
    folder_btn = tk.Button(folder_frame, text=" Choose Folder ", image=folder_icon, compound=tk.LEFT, font=("Arial", 10, "bold"), command=select_folder)
    global run_btn
    run_btn = tk.Button(folder_frame, text="   Run   ", image=run_icon, compound=tk.LEFT, font=("Arial", 10, "bold"), command=run, state=tk.DISABLED)
    label.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=2, ipadx=10, ipady=0)
    folder_btn.grid(row=0, column=1, padx=(3, 5), pady=2, ipadx=8, ipady=4, sticky="e")
    run_btn.grid(row=0, column=2, padx=5, pady=2, ipadx=8, ipady=4, sticky="e")
    folder_frame.pack(pady=12, padx=10, fill="x", anchor="ne")
    folder_frame.folder_icon = folder_icon
    folder_frame.run_icon = run_icon

    # Options category title and separator
    options_title = tk.Label(root, text="Options", font=("Arial", 10, "bold"), anchor="w")
    options_title.pack(fill="x", padx=12, pady=(0, 0))
    options_separator = tk.Frame(root, height=1, bg="#cccccc", bd=0, relief=tk.FLAT)
    options_separator.pack(fill="x", padx=12, pady=(0, 8))

    # Load saved checkbox state
    options_config = load_checkbox_state()

    # --- Options Section ---
    # Variables
    data_var = tk.BooleanVar(value=options_config.generate_data)
    stats_var = tk.BooleanVar(value=options_config.generate_stats)
    move_empty_var = tk.BooleanVar(value=options_config.move_empty)
    move_undefined_var = tk.BooleanVar(value=options_config.move_undefined)
    rename_var = tk.BooleanVar(value=options_config.rename_files)
    gps_var = tk.BooleanVar(value=options_config.add_gps)
    get_gps_each_var = tk.BooleanVar(value=options_config.get_gps_from_each_file)
    use_gps_only_for_data_var = tk.BooleanVar(value=options_config.use_gps_only_for_data)
    combine_with_data_var = tk.BooleanVar(value=options_config.combine_with_data)
    time_offset_var = tk.StringVar(value=options_config.time_offset)
    threshold_var = tk.DoubleVar(value=options_config.prediction_threshold)

    # Main options frame
    options_frame = tk.Frame(root)
    options_frame.pack(pady=5, fill="x")

    # Folder sort row
    folder_sort_frame = tk.Frame(options_frame)
    tk.Label(folder_sort_frame, text="Folder sort :", width=32, anchor="w").pack(side=tk.LEFT)
    CheckWithTooltip(
        folder_sort_frame,
        "Empty results to subfolder",
        move_empty_var,
        "Moves all files with no detected animals to a subfolder named 'empty'."
    ).pack(side=tk.LEFT)
    CheckWithTooltip(
        folder_sort_frame,
        "Undefined results to subfolder",
        move_undefined_var,
        "Moves all files with a prediction score under the prediction threshold to a subfolder named 'undefined'.\nYou can adjust the prediction threshold by cliking on 'more'."
    ).pack(side=tk.LEFT)
    folder_sort_frame.pack(fill="x", pady=1, padx=30)

    # Files update row
    files_update_frame = tk.Frame(options_frame)
    tk.Label(files_update_frame, text="Files update :", width=32, anchor="w").pack(side=tk.LEFT)
    CheckWithTooltip(
        files_update_frame,
        "Rename with date and info",
        rename_var,
        "Renames files to include the date and prediction in the filename.\nBe sure you will not need the original files' name, as they will be lost."
    ).pack(side=tk.LEFT)
    CheckWithTooltip(
        files_update_frame,
        "Add GPS location",
        gps_var,
        "After clicking on 'Run', a map will open for you to select the GPS coordinates to add to all the files.\nHaving access to GPS data will allow for more information in the generated files in the data section.\nThe added GPS data will also be usable by other applications, such as Windows' photo viewer or Google photos.\nIf the files already have GPS data, it will be overwritten unless 'Use added GPS data without updating files' is checked."
    ).pack(side=tk.LEFT)
    files_update_frame.pack(fill="x", pady=1, padx=30)

    # Data generation row
    data_gen_frame = tk.Frame(options_frame)
    tk.Label(data_gen_frame, text="Data generation :", width=32, anchor="w").pack(side=tk.LEFT)
    CheckWithTooltip(
        data_gen_frame,
        "CSV file",
        data_var,
        "Generates a CSV file in a 'data' subfolder with all relevant information about the files and their corresponding prediction.\nIt is recommanded to keep this option checked, as the CSV file can be useful for debugging or future data analysis combinations."
    ).pack(side=tk.LEFT)
    CheckWithTooltip(
        data_gen_frame,
        "Statistics file",
        stats_var,
        "Generates a PDF file in a 'data' subfolder with various statistics and graphs about the files.\nIf you want to combine the data with previous results, check 'Combine data results with existing CSV' in 'more'."
    ).pack(side=tk.LEFT)
    data_gen_frame.pack(fill="x", pady=1, padx=30)

    # --- More (foldable) section ---
    def toggle_more():
        if more_content.winfo_ismapped():
            more_content.pack_forget()
            more_btn.config(text="more ▼")
        else:
            more_content.pack(fill="x", pady=(2, 0))
            more_btn.config(text="more ▲")

    more_btn = tk.Button(options_frame, text="more ▼", font=("Arial", 10, "italic bold"), bd=0, fg="#444", cursor="hand2", command=toggle_more)
    more_btn.pack(anchor="w", pady=(6, 0), padx=20)

    more_content = tk.Frame(options_frame)
    # Prediction threshold slider
    threshold_row = tk.Frame(more_content)
    LabelWithTooltip(
        threshold_row, 
        "Adjust prediction threshold", 
        "Adjust the prediction threshold used to determine if a prediction is valid or should be considered undefined.\nA higher threshold means more confidence in the predictions, but may result in more undefined results.",
        width = 200
    ).pack(side=tk.LEFT, anchor="s", pady=(0, 5))
    threshold_slider = tk.Scale(threshold_row, from_=0.0, to=1.0, orient=tk.HORIZONTAL, resolution=0.01, variable=threshold_var, showvalue=True, length=180)
    threshold_slider.pack(side=tk.LEFT, anchor="s")
    threshold_row.pack(fill="x", pady=2, padx=30)
    
    # Timezone offset selector
    timezone_row = tk.Frame(more_content)
    LabelWithTooltip(
        timezone_row, 
        "Time offset", 
        "Select the time offset to apply to the files' datetime.\nThe 'auto' value will attempt to keep the original timezone information if present, or else use the timezone of your machine.\nSelect an offset if you want to run the program on files with a different timezone than your machine's, or if you are getting unexpected date results.\nYou can test the selected offset on a file of your choice by clicking the 'Test file date' button.",
        width = 200
    ).pack(side=tk.LEFT)
    # Build list of offsets: auto, UTC-12:00 to UTC+14:00
    offsets = [f"UTC{sign}{abs(h):02d}:{abs(m):02d}" for h in range(-12, 15) for m in [0, 30] for sign in ["+" if h >= 0 else "-"] if not (h == 0 and sign == "-")]
    offsets = sorted(set(offsets), key=lambda x: (x != "auto", x))
    offsets.insert(0, "auto")
    timezone_combo = ttk.Combobox(
        timezone_row,
        textvariable=time_offset_var,
        values=offsets,
        state="readonly",
        width=12
    )
    timezone_combo.pack(side=tk.LEFT, padx=3)
    # Button to test selected file's date
    def test_selected_file_date():
        from models.fileManager import FileManager
        file_path = filedialog.askopenfilename(title="Select a video or photo file")
        if file_path:
            try:
                fm = FileManager([file_path])
                date = fm.getDates()[0]
                messagebox.showinfo("Selected File Date", f"Date for selected file after timezone conversion: {convert_to_timezone(date, time_offset_to_timezone(time_offset_var.get()))}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not get date: {e}")
        else:
            messagebox.showerror("Error", "No file selected.")
    test_date_btn = tk.Button(timezone_row, text="Test file date", command=test_selected_file_date, width=12, height=1, bd=1)
    test_date_btn.pack(side=tk.LEFT, padx=5)
    timezone_row.pack(fill="x", pady=2, padx=30)

    # More checkboxes
    CheckWithTooltip(
        more_content,
        "Get GPS data from each file independently",
        get_gps_each_var,
        "Get the GPS data from each file instead of using the same coordinates for all files.\nThis requires that the files already have GPS data, and will have no effect if the option 'add GPS location' is checked.\nBe aware that this will make the processing longer, as each file will need to be read to extract the GPS data.",
        width=320
    ).pack(anchor="w", padx=30, pady=(5, 0))
    CheckWithTooltip(
        more_content,
        "Use added GPS data without updating files",
        use_gps_only_for_data_var,
        "Use the added GPS location for data generation without modifying the files.\nThis is useful if you want to keep the original files unchanged, but still want to benefit from GPS data in the generated CSV and statistics.\nWill have no effect if the option 'Add GPS location' is not checked.",
        width=320
    ).pack(anchor="w", padx=30, pady=(5, 0))
    CheckWithTooltip(
        more_content,
        "Combine data results with existing CSV",
        combine_with_data_var,
        "Generates in the 'data' subfolder a CSV that combines the existing selected CSV data with this run's results.\nAlso generates the combined statistics PDF if the option 'Statistics file' is checked.\nThis is useful if you have previous data from other runs or sources that you want to include in the statistics.\nYou will be prompted to select the CSV file when you click 'Run'.",
        width=320
    ).pack(anchor="w", padx=30, pady=(5, 0))
    # Start folded
    more_content.pack_forget()

    # Map selection variable (no button/field, but still needed for map window)
    coord_var = tk.StringVar(value="No coordinates selected")

    # Logs category title and separator
    logs_title = tk.Label(root, text="Logs", font=("Arial", 10, "bold"), anchor="w")
    logs_title.pack(fill="x", padx=12, pady=(0, 0))
    logs_separator = tk.Frame(root, height=1, bg="#cccccc", bd=0, relief=tk.FLAT)
    logs_separator.pack(fill="x", padx=12, pady=(0, 8))

    # Log text area
    log_frame = tk.Frame(root)
    log_frame.pack(padx=10, pady=(0, 10), fill='both', expand=True)
    log_frame.rowconfigure(0, weight=1)
    log_frame.columnconfigure(0, weight=1)

    log_text = tk.Text(
        log_frame,
        height=10,
        width=60,
        state='disabled',
        wrap='word',
    )
    log_text.grid(row=0, column=0, sticky='nsew')

    log_scrollbar = ttk.Scrollbar(
        log_frame,
        orient=tk.VERTICAL,
        command=log_text.yview,
    )
    log_scrollbar.grid(row=0, column=1, sticky='ns')

    new_logs_button = tk.Button(
        log_frame,
        text="New logs",
        font=("Arial", 9, "bold"),
        padx=8,
        pady=2,
        cursor="hand2",
    )

    def set_new_logs_visible(visible):
        if visible:
            new_logs_button.place(
                relx=1.0,
                rely=1.0,
                x=-18,
                y=-8,
                anchor='se',
            )
            new_logs_button.lift()
        else:
            new_logs_button.place_forget()

    log_handler = TkinterLogHandler(
        log_text,
        on_unread_change=set_new_logs_visible,
        post_to_main_loop=main_loop_dispatcher.post,
    )
    new_logs_button.config(command=log_handler.scroll_to_bottom)

    def on_log_scroll(first_visible, last_visible):
        log_scrollbar.set(first_visible, last_visible)
        log_handler.on_view_changed(first_visible, last_visible)

    log_text.config(yscrollcommand=on_log_scroll)

    # Footer with support link (looks like a hyperlink)
    footer_frame = tk.Frame(root)
    def open_support(_evt=None):
        webbrowser.open("https://ko-fi.com/bernigaudnoe", new=1)
    def open_github(_evt=None):
        webbrowser.open("https://github.com/noebernigaud/CameraTrapAssistant", new=1)

    link_normal = "#1a73e8"   # Google blue
    link_hover = "#0b5ed7"    # darker on hover

    # Try to load GitHub icon for footer
    github_icon = None
    try:
        def load_footer_icon(filename: str, target_height: int) -> tk.PhotoImage | None:
            try:
                icon_path = get_icon_path(filename)
                img = Image.open(str(icon_path)).convert("RGBA")
                w, h = img.size
                if h > 0 and h != target_height:
                    new_w = max(1, round(w * (target_height / h)))
                    img = img.resize((new_w, target_height), Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                return None

        # Footer GitHub icon
        github_icon = load_footer_icon("github-mark.png", 18)
    except Exception:
        github_icon = None

    support_link = create_support_link_label(footer_frame)
    support_link.pack(side=tk.RIGHT, padx=10, pady=(0, 10))
    footer_frame.pack(side=tk.BOTTOM, fill="x")


    github_link = tk.Label(
        footer_frame,
        text="GitHub",
        fg=link_normal,
        cursor="hand2",
        font=("Arial", 10, "underline"),
        image=github_icon,
        compound=tk.LEFT,
        padx=4
    )
    github_link.image = github_icon  # Keep a reference to avoid image being garbage-collected
    github_link.bind("<Button-1>", open_github)
    github_link.bind("<Enter>", lambda e: github_link.config(fg=link_hover))
    github_link.bind("<Leave>", lambda e: github_link.config(fg=link_normal))
    github_link.pack(side=tk.RIGHT, padx=10, pady=(0, 10))

    # Attach the logging handler
    logging.getLogger().addHandler(log_handler)
    logging.getLogger().setLevel(logging.INFO)

    root.mainloop()


if __name__ == "__main__":
    main()
