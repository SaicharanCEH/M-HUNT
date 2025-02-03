import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import threading
import sys
import customtkinter as ctk

# Add a global variable to control the scan
scan_running = False
process = None


class CTkMarqueeProgressBar(ctk.CTkProgressBar):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.marquee_active = False

    def start_marquee(self, interval=10):
        self.marquee_active = True
        self.start()

    def stop_marquee(self):
        self.marquee_active = False
        self.stop()


def run_feroxbuster(target_url, wordlist_path, threads):
    global process, scan_running
    # Construct the feroxbuster command
    command = [
        "feroxbuster",
        "-u",
        target_url,
        "-w",
        wordlist_path,
        "-s",
        "200",
        "-n",
        "-t",
        str(threads),
        "--silent",
    ]

    # Run the command
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        while scan_running:
            line = process.stdout.readline()
            if not line:
                break
            root.after(0, lambda l=line: update_result(l, append=True))

        process.terminate()
        process.wait()

        if (
            process.returncode != 0 and process.returncode != -15
        ):  # -15 is the return code for SIGTERM
            error_output = process.stderr.read()
            return f"An error occurred: {error_output}"

        return "Scan completed or stopped."
    except Exception as e:
        return f"An exception occurred: {str(e)}"


def run_mhunt_threaded():
    global scan_running
    target_url = url_entry.get()
    wordlist_path = "C:/Users/padig/M-HUNT/M-HUNT/fuzz.txt"
    threads = thread_entry.get()

    # Validate inputs
    if not target_url:
        messagebox.showerror("Error", "Please enter a target URL.")
        return

    try:
        threads = int(threads)
    except ValueError:
        messagebox.showerror(
            "Error", "Invalid number of threads. Please enter a valid integer."
        )
        return

    # Clear previous results
    result_text.delete(1.0, tk.END)

    # Disable the scan button and enable the stop button
    scan_button.config(state="disabled")
    stop_button.config(state="normal")

    # Hide download button
    hide_download_button()

    # Show progress bar
    progress_bar.grid(column=0, row=4, columnspan=3, sticky=(tk.W, tk.E), pady=10)
    progress_bar.start_marquee()

    # Set scan_running to True
    scan_running = True

    # Run feroxbuster in a separate thread
    def run_scan():
        result = run_feroxbuster(target_url, wordlist_path, threads)
        # Update GUI in the main thread with final result
        root.after(0, lambda: update_result(result, append=True))
        root.after(0, scan_completed)
        root.after(0, show_download_button)  # Show download button after completion

    threading.Thread(target=run_scan, daemon=True).start()


def stop_scan():
    global scan_running, process
    scan_running = False
    if process:
        process.terminate()
    update_result("Scan stopped by user.\n", append=True)
    scan_completed()
    show_download_button()


def show_download_button():
    download_button.grid(column=1, row=3, pady=10)


def hide_download_button():
    download_button.grid_remove()


def download_results():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("Text files", "*.txt")]
    )
    if file_path:
        content = result_text.get(1.0, tk.END)
        # Filter out unwanted lines
        filtered_content = [
            line
            for line in content.splitlines()
            if line
            and "Scan stopped by user." not in line
            and "An error occurred:" not in line
        ]

        with open(file_path, "w") as file:
            file.write("\n".join(filtered_content))
        messagebox.showinfo("Success", f"Results saved to {file_path}")


def scan_completed():
    global scan_running
    scan_running = False
    scan_button.config(state="normal")
    stop_button.config(state="disabled")
    progress_bar.stop_marquee()
    progress_bar.grid_remove()
    show_download_button()  # Show download button after completion


def update_result(result, append=False):
    if not append:
        result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, result)
    result_text.see(tk.END)  # Scroll to the bottom


# Create main window
root = tk.Tk()
root.title("M-HUNT GUI")
root.geometry("700x500")
root.minsize(700, 500)  # Set minimum size
root.configure(bg="#f0f0f0")

# Create custom fonts
title_font = font.Font(family="Helvetica", size=16, weight="bold")
label_font = font.Font(family="Helvetica", size=12)
button_font = font.Font(family="Helvetica", size=10, weight="bold")

# Create and place widgets
frame = ttk.Frame(root, padding="20")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="M-HUNT GUI", font=title_font).grid(
    column=0, row=0, columnspan=3, pady=10
)

ttk.Label(frame, text="Target URL:", font=label_font).grid(
    column=0, row=1, sticky=tk.W, pady=5
)
url_entry = ttk.Entry(frame, width=50, font=label_font)
url_entry.grid(column=1, row=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

ttk.Label(frame, text="Threads:", font=label_font).grid(
    column=0, row=2, sticky=tk.W, pady=5
)
thread_entry = ttk.Entry(frame, width=10, font=label_font)
thread_entry.grid(column=1, row=2, sticky=tk.W, pady=5)

style = ttk.Style()
style.configure("TButton", font=button_font, padding=5)

scan_button = ttk.Button(
    frame, text="Start Scan", command=run_mhunt_threaded, style="TButton"
)
scan_button.grid(column=0, row=3, pady=10, sticky=tk.W)

stop_button = ttk.Button(
    frame, text="Stop Scan", command=stop_scan, state="disabled", style="TButton"
)
stop_button.grid(column=2, row=3, pady=10, sticky=tk.E)

download_button = ttk.Button(
    frame, text="Download Results", command=download_results, style="TButton"
)
download_button.grid(column=1, row=3, pady=10)
download_button.grid_remove()  # Hide download button initially

# Create a frame to hold the Text widget and Scrollbar
result_frame = ttk.Frame(frame)
result_frame.grid(column=0, row=7, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

# Create the Text widget and Scrollbar
result_text = tk.Text(result_frame, wrap=tk.WORD, width=80, height=15, font=label_font)
result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=result_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

result_text.config(yscrollcommand=scrollbar.set)

# Configure CustomTkinter
ctk.set_appearance_mode("light")  # Use light mode for consistency
ctk.set_default_color_theme("green")  # You can change this to match your preference

# Replace the progress bar creation with this CustomTkinter version
progress_bar = CTkMarqueeProgressBar(
    frame,
    orientation="horizontal",
    mode="indeterminate",
    width=600,
    height=20,
)
progress_bar.grid(column=0, row=4, columnspan=3, sticky=(tk.W, tk.E), pady=10)
progress_bar.grid_remove()  # Hide progress bar initially

# Configure grid weights
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)
frame.rowconfigure(7, weight=1)

# Start the GUI event loop
root.mainloop()
