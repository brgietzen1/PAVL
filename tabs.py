import tkinter as tk
from tkinter import ttk, messagebox
from models import aircraft
from backend import write_mass_file, write_run_file, write_avl_file
from runner import run_avl
import os

# Provide a global reference so workspace can inject this
apply_inputs = None

class SurfaceTab:
    def __init__(self, parent_frame, tab_name, input_callback, apply_callback):
        global apply_inputs
        apply_inputs = apply_callback

        self.tab_name = tab_name
        self.tab_frame = ttk.Frame(parent_frame, padding="10")
        parent_frame.add(self.tab_frame, text=tab_name)

        self.left_frame = ttk.Frame(self.tab_frame, padding="10")
        self.left_frame.pack(side="left", fill="both", expand=True)
        self.listbox = tk.Listbox(self.left_frame, height=20, width=30)
        self.listbox.pack(side="top", fill="y")

        self.right_frame = ttk.Frame(self.tab_frame, padding="10")
        self.right_frame.pack(side="right", fill="y")

        self.mode_var = tk.StringVar()
        self.name_var = tk.StringVar()

        ttk.Label(self.right_frame, text="Mode:").grid(row=0, column=0, sticky="w")
        self.mode_combo = ttk.Combobox(
            self.right_frame, textvariable=self.mode_var,
            values=["Create", "Modify", "Delete"], state="readonly"
        )
        self.mode_combo.grid(row=0, column=1, sticky="ew")
        self.mode_combo.current(0)

        ttk.Label(self.right_frame, text="Name:").grid(row=1, column=0, sticky="w")
        self.name_entry = ttk.Entry(self.right_frame, textvariable=self.name_var)
        self.name_entry.grid(row=1, column=1, sticky="ew")

        self.input_button = ttk.Button(self.right_frame, text="Input Properties", command=lambda: input_callback(self))
        self.input_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.apply_button = ttk.Button(self.right_frame, text="Apply", command=lambda: apply_callback(self))
        self.apply_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)

    def on_listbox_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            selected_name = self.listbox.get(selection[0])
            self.name_var.set(selected_name)

    def on_mode_change(self, event):
        if self.mode_var.get() == "Delete":
            self.input_button.grid_remove()
        else:
            self.input_button.grid()

    def update_listbox(self, items):
        self.listbox.delete(0, tk.END)
        for name in items:
            self.listbox.insert(tk.END, name)

    def get_selected_name(self):
        return self.name_var.get().strip()

class AnalysisTab:
    def __init__(self, parent_frame):
        self.tab_frame = ttk.Frame(parent_frame, padding="10")
        parent_frame.add(self.tab_frame, text="Analysis")

        row = 0

        ttk.Label(self.tab_frame, text="Job Name").grid(column=1, row=row, sticky="w")
        row += 1
        self.job_name_entry = ttk.Entry(self.tab_frame)
        self.job_name_entry.grid(column=1, row=row)
        row += 1

        ttk.Label(self.tab_frame, text="Sref:").grid(column=1, row=row, sticky="w")
        row += 1
        self.sref_entry = ttk.Entry(self.tab_frame)
        self.sref_entry.grid(column=1, row=row)
        row += 1

        ttk.Label(self.tab_frame, text="Cref:").grid(column=1, row=row, sticky="w")
        row += 1
        self.cref_entry = ttk.Entry(self.tab_frame)
        self.cref_entry.grid(column=1, row=row)
        row += 1

        ttk.Label(self.tab_frame, text="Bref:").grid(column=1, row=row, sticky="w")
        row += 1
        self.bref_entry = ttk.Entry(self.tab_frame)
        self.bref_entry.grid(column=1, row=row)
        row += 1

        ttk.Label(self.tab_frame, text="Units:").grid(column=1, row=row, sticky="w")
        row += 1
        self.units_combo = ttk.Combobox(self.tab_frame, values=["MKS", "FPS"], state="readonly")
        self.units_combo.grid(column=1, row=row)
        row += 1

        ttk.Label(self.tab_frame, text="Surface Geometries").grid(column=1, row=row, sticky="w")
        ttk.Label(self.tab_frame, text="Existing Cases").grid(column=3, row=row, sticky="w")
        row += 1

        self.geom_listbox = tk.Listbox(self.tab_frame, height=5)
        self.geom_listbox.grid(column=1, row=row)

        self.existing_cases = tk.Listbox(self.tab_frame, height=5)
        self.existing_cases.grid(column=3, row=row)
        row += 1

        ttk.Label(self.tab_frame, text="Mass Components").grid(column=1, row=row+2, sticky="w")
        row += 1
        self.mass_listbox = tk.Listbox(self.tab_frame, height=5)
        self.mass_listbox.grid(column=1, row=row+2)
        row += 1

        self.add_case_button = ttk.Button(self.tab_frame, text="Add Case", command=self.add_case)
        self.add_case_button.grid(column=3, row=row - 2)

        self.add_all_button = ttk.Button(self.tab_frame, text="Add All Cases", command=self.add_all_cases)
        self.add_all_button.grid(column=3, row=row - 1)

        ttk.Label(self.tab_frame, text="Cases to Run").grid(column=3, row=row, sticky="w")
        row += 1
        self.cases_to_run = tk.Listbox(self.tab_frame, height=5)
        self.cases_to_run.grid(column=3, row=row)
        row += 1

        self.delete_case_button = ttk.Button(self.tab_frame, text="Delete Case", command=self.delete_case)
        self.delete_case_button.grid(column=3, row=row)
        row += 1

        self.delete_all_button = ttk.Button(self.tab_frame, text="Delete All Cases", command=self.delete_all_cases)
        self.delete_all_button.grid(column=3, row=row)
        row += 1

        self.run_button = ttk.Button(self.tab_frame, text="Run AVL", command=self.run_avl_simulation)
        self.run_button.grid(column=2, row=row)

        self.refresh_lists()

    def run_avl_simulation(self):
        job_name = self.job_name_entry.get().strip()
        if not job_name:
            messagebox.showwarning("Missing Job Name", "Please enter a job name before running AVL.")
            return

        try:
            sref = float(self.sref_entry.get())
            cref = float(self.cref_entry.get())
            bref = float(self.bref_entry.get())
            units = self.units_combo.get()

            if not units:
                raise ValueError("Units selection is required.")
            if sref <= 0 or cref <= 0 or bref <= 0:
                raise ValueError("Sref, Cref, and Bref must be positive.")

            aircraft.Sref = sref
            aircraft.Cref = cref
            aircraft.Bref = bref
            aircraft.units = units

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        selected_cases = self.cases_to_run.get(0, tk.END)
        if not selected_cases:
            messagebox.showerror("No Case Selected", "Please add at least one case to run.")
            return

        case_name = selected_cases[0]
        if case_name not in aircraft.simulation_cases:
            messagebox.showerror("Invalid Case", f"Simulation case '{case_name}' not found.")
            return

        sim_case = aircraft.simulation_cases[case_name]
        results_dir = "results"

        try:
            write_mass_file(job_name, aircraft, sim_case, os.path.join(results_dir, f"{job_name}.mass"))
            write_run_file(job_name, sim_case, os.path.join(results_dir, f"{job_name}.run"))
            write_avl_file(job_name, aircraft, sim_case, None, os.path.join(results_dir, f"{job_name}.avl"))
            run_avl(job_name, results_dir)
            aircraft.session_jobs.add(job_name)
            parent = self.tab_frame.master
            if hasattr(parent, 'results_tab'):
                parent.results_tab.refresh_job_list()
        except Exception as e:
            messagebox.showerror("Error", f"AVL simulation failed: {e}")

    def refresh_lists(self):
        self.geom_listbox.delete(0, tk.END)
        for name in aircraft.geometry:
            self.geom_listbox.insert(tk.END, name)

        self.mass_listbox.delete(0, tk.END)
        for name in aircraft.mass_properties:
            self.mass_listbox.insert(tk.END, name)

        self.existing_cases.delete(0, tk.END)
        for name in aircraft.simulation_cases:
            self.existing_cases.insert(tk.END, name)

    def add_case(self):
        selected = self.existing_cases.curselection()
        for i in selected:
            case = self.existing_cases.get(i)
            if case not in self.cases_to_run.get(0, tk.END):
                self.cases_to_run.insert(tk.END, case)

    def add_all_cases(self):
        for case in self.existing_cases.get(0, tk.END):
            if case not in self.cases_to_run.get(0, tk.END):
                self.cases_to_run.insert(tk.END, case)

    def delete_case(self):
        selected = self.cases_to_run.curselection()
        for i in reversed(selected):
            self.cases_to_run.delete(i)

    def delete_all_cases(self):
        self.cases_to_run.delete(0, tk.END)


class ResultsTab:
    def __init__(self, parent_frame):
        self.tab_frame = ttk.Frame(parent_frame, padding="10")
        parent_frame.add(self.tab_frame, text="Results")

        text_frame = ttk.Frame(self.tab_frame)
        text_frame.grid(row=1, column=1, rowspan=5, padx=10, pady=10, sticky="nsew")

        self.output_text = tk.Text(text_frame, wrap="none", width=60, height=30, state="disabled")
        self.output_text.grid(row=0, column=0, sticky="nsew")

        x_scroll = ttk.Scrollbar(text_frame, orient="horizontal", command=self.output_text.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.output_text.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.output_text.config(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)


        self.mode_var = tk.StringVar(value="Access")
        self.mode_combo = ttk.Combobox(
            self.tab_frame, textvariable=self.mode_var,
            values=["Access", "Delete"], state="readonly"
        )
        self.mode_combo.grid(column=2, row=1, pady=(10, 0))
        self.mode_combo.bind("<<ComboboxSelected>>", self.update_mode)

        ttk.Label(self.tab_frame, text="Existing Jobs").grid(column=2, row=2, sticky="w")
        self.job_listbox = tk.Listbox(self.tab_frame, height=15, width=40)
        self.job_listbox.grid(column=2, row=3, padx=5)

        self.action_button = ttk.Button(self.tab_frame, text="Display", command=self.handle_action)
        self.action_button.grid(column=2, row=4, pady=5)

        self.refresh_job_list()

    def update_mode(self, event):
        self.action_button.config(text="Display" if self.mode_var.get() == "Access" else "Delete")

    def refresh_job_list(self):
        self.job_listbox.delete(0, tk.END)
        for file in os.listdir("results"):
            if file.endswith(".sim"):
                jobname = os.path.splitext(file)[0]
                if jobname in aircraft.session_jobs:
                    self.job_listbox.insert(tk.END, jobname)

    def handle_action(self):
        selected = self.job_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a job.")
            return

        job_name = self.job_listbox.get(selected[0])
        sim_path = os.path.join("results", job_name + ".sim")

        if self.mode_var.get() == "Access":
            self.display_job(sim_path)
        elif self.mode_var.get() == "Delete":
            self.delete_job(sim_path)

    def display_job(self, filepath):
        try:
            with open(filepath, 'r') as file:
                content = file.read()
            self.output_text.config(state='normal')
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, content)
            self.output_text.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Error", f"Could not read job file: {e}")

    def delete_job(self, filepath):
        filename = os.path.basename(filepath)
        confirm = messagebox.askyesno("Delete File", f"Are you sure you want to delete the following file: {filename}?")
        if confirm:
            try:
                os.remove(filepath)
                self.refresh_job_list()
                self.output_text.config(state='normal')
                self.output_text.delete(1.0, tk.END)
                self.output_text.config(state='disabled')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {e}")
