import tkinter as tk
from tkinter import *
from tkinter import ttk, filedialog
import workspace as wk

def new_geometry():
    wk.open_main_window()
    root.withdraw()

def load_geometry():
    file_path = filedialog.askopenfilename(filetypes=[("PAVL Session Files", "*.pavl")])
    if file_path:
        print(f"Loading Geometry from: {file_path}")
        # Placeholder: load session and open main GUI window
        # e.g., session_data = load_session(file_path)
        # open_main_window(session_data)

def quit_program():
    root.destroy()

root = Tk()
root.title("Main Menu")
root.geometry("400x300") # initial window size
root.iconbitmap("assets/icon1.ico")

# Make window expandable and responsive
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

mainframe = ttk.Frame(root, padding="20")
mainframe.grid(column=0, row=0, sticky=(N, S, E, W))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

# Inner frame to hold content and center it
button_frame = ttk.Frame(mainframe)
button_frame.grid(column=0, row=0, sticky="")
button_frame.columnconfigure(0, weight=1)

# Title Label
tk.Label(
    button_frame,
    text="PAVL",
    font=("Helvetica", 24, "bold"),
    fg="#1F4E79"
).grid(column=0, row=0, pady=(0, 20))

# Buttons
ttk.Button(button_frame, text="New Geometry", command=new_geometry).grid(column=0, row=1, pady=5, padx=20, sticky=(W, E))
ttk.Button(button_frame, text="Load Geometry", command=load_geometry).grid(column=0, row=2, pady=5, padx=20, sticky=(W, E))
ttk.Button(button_frame, text="Quit", command=quit_program).grid(column=0, row=3, pady=5, padx=20, sticky=(W, E))

root.mainloop()