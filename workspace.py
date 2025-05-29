# File: workspace.py

import tkinter as tk
from tkinter import ttk, messagebox
import os
from models import Aircraft, MassProperty, GeometrySurface, SimulationCase, aircraft, property_drafts, validate_property_fields
from input_windows import MassPropertyEditor
from input_windows import GeometryPropertyEditor
from tabs import SurfaceTab, AnalysisTab, ResultsTab
from input_windows import SimulationCaseEditor


RESULTS_DIR = os.path.join(os.getcwd(), "results")
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# ======== Input Functions ========
def geometry_input_window(tab, force_object_load=False):
    name = tab.get_selected_name()
    mode = tab.mode_var.get()
    if not name:
        messagebox.showwarning("Missing Name", "Please enter a name before inputting properties.")
        return
    if mode == "Delete":
        return

    GeometryPropertyEditor(tab.tab_frame, name)

def properties_input_window(tab, force_object_load=False):
    name = tab.get_selected_name()
    mode = tab.mode_var.get()
    if not name:
        messagebox.showwarning("Missing Name", "Please enter a name before inputting properties.")
        return
    if mode == "Delete":
        return

    existing = None
    if force_object_load and name in aircraft.mass_properties:
        prop = aircraft.mass_properties[name]
        existing = {
            'Mass': str(prop.mass), 'X': str(prop.x), 'Y': str(prop.y), 'Z': str(prop.z),
            'Ixx': str(prop.Ixx), 'Iyy': str(prop.Iyy), 'Izz': str(prop.Izz),
            'Ixy': str(prop.Ixy), 'Ixz': str(prop.Ixz), 'Iyz': str(prop.Iyz)
        }
    elif not force_object_load and name in property_drafts:
        existing = property_drafts[name]
    elif name in aircraft.mass_properties:
        prop = aircraft.mass_properties[name]
        existing = {
            'Mass': str(prop.mass), 'X': str(prop.x), 'Y': str(prop.y), 'Z': str(prop.z),
            'Ixx': str(prop.Ixx), 'Iyy': str(prop.Iyy), 'Izz': str(prop.Izz),
            'Ixy': str(prop.Ixy), 'Ixz': str(prop.Ixz), 'Iyz': str(prop.Iyz)
        }

    MassPropertyEditor(tab.tab_frame, name, existing)


def case_input_window(tab, force_object_load=False):
    name = tab.get_selected_name()
    mode = tab.mode_var.get()
    if not name:
        messagebox.showwarning("Missing Name", "Please enter a name before inputting properties.")
        return
    if mode == "Delete":
        return

    existing = None
    if force_object_load and name in aircraft.simulation_cases:
        case = aircraft.simulation_cases[name]
        existing = {
            "Mach": str(case.Mach),
            "Rho": str(case.rho),
            "Cdo": str(case.Cdo),
            "AOA Mode": case.aoa_mode,
            "AOA Val": str(case.aoa_val),
            "Elevator Mode": case.elevator_mode or "",
            "Elevator Val": str(case.elevator_val) if case.elevator_val is not None else "",
            "Flap Mode": case.flap_mode or "",
            "Flap Val": str(case.flap_val) if case.flap_val is not None else ""
        }
    elif name in property_drafts:
        existing = property_drafts[name]

    SimulationCaseEditor(tab.tab_frame, name, existing)


# ======== Apply Dispatcher ========
def apply_inputs(tab):
    name = tab.get_selected_name()
    mode = tab.mode_var.get()
    tab_type = tab.tab_name

    if not name:
        messagebox.showwarning("Warning", "Name cannot be empty.")
        return

    target_dict = {
        "Geometry": aircraft.geometry,
        "Properties": aircraft.mass_properties,
        "Cases": aircraft.simulation_cases
    }.get(tab_type)

    if target_dict is None:
        messagebox.showerror("Error", f"Unknown tab: {tab_type}")
        return

    if mode == "Create":
        if name in target_dict:
            result = messagebox.askyesnocancel("Duplicate Name", f"'{name}' already exists. Overwrite?")
            if result is None or not result:
                return
        if tab_type == "Geometry":
            from input_windows import apply_geometry_surface
            apply_geometry_surface(tab)
            return

        elif tab_type == "Properties":
            draft = property_drafts.get(name)
            if not draft:
                messagebox.showerror("Error", f"No property data found for '{name}'. Please enter values.")
                return
            valid, error_msg = validate_property_fields(draft)
            if not valid:
                messagebox.showerror("Invalid Input", error_msg)
                return
            
            try:
                mass_val = float(draft.get("Mass", 0))
                inertia_vals = [float(draft.get(k, 0)) for k in ['Ixx', 'Iyy', 'Izz', 'Ixy', 'Ixz', 'Iyz']]
            except ValueError:
                messagebox.showerror("Invalid Input", "Mass and inertia fields must be valid numbers.")
                return

            if mass_val <= 0 or any(i < 0 for i in inertia_vals):
                messagebox.showerror("Invalid Input", "Mass must be > 0 and/or inertia values must be ≥ 0.")
                return


            target_dict[name] = MassProperty(
                name,
                float(draft.get("Mass", 0)),
                float(draft.get("X", 0)),
                float(draft.get("Y", 0)),
                float(draft.get("Z", 0)),
                float(draft.get("Ixx", 0)),
                float(draft.get("Iyy", 0)),
                float(draft.get("Izz", 0)),
                float(draft.get("Ixy", 0)),
                float(draft.get("Ixz", 0)),
                float(draft.get("Iyz", 0))
            )

        elif tab_type == "Cases":
            draft = property_drafts.get(name)
            if not draft:
                messagebox.showerror("Error", f"No case data found for '{name}'. Please enter values.")
                return

            try:
                # 1. Check all required fields are filled
                required_fields = ["Mach", "Rho", "Cdo", "AOA Mode", "AOA Val"]
                for key in required_fields:
                    if key not in draft or draft[key].strip() == "":
                        raise ValueError(f"{key} must be filled.")

                # 2. Attempt to cast all values to float
                Mach = float(draft["Mach"])
                rho = float(draft["Rho"])
                cdo = float(draft["Cdo"])
                aoa_mode = draft["AOA Mode"]
                aoa_val = float(draft["AOA Val"])

                elevator_mode = draft.get("Elevator Mode") or None
                elevator_val = float(draft["Elevator Val"]) if "Elevator Val" in draft and draft["Elevator Val"].strip() else None

                flap_mode = draft.get("Flap Mode") or None
                flap_val = float(draft["Flap Val"]) if "Flap Val" in draft and draft["Flap Val"].strip() else None

                # 3. Check Mach and Rho and Cdo are positive
                if Mach < 0 or rho <= 0 or cdo < 0:
                    raise ValueError("Mach and Rho must be positive.")

                # 4. Disallow AOA and Elevator both being set to "Cm"
                if aoa_mode == "Cm" and elevator_mode == "Cm":
                    raise ValueError("AOA and Elevator modes cannot both be set to 'Cm'.")

                # Assign to aircraft
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))
                return
            
            target_dict[name] = SimulationCase(
                name=name,
                Mach=Mach,
                rho=rho,
                Cdo=cdo,
                aoa_mode=aoa_mode,
                aoa_val=aoa_val,
                elevator_mode=elevator_mode,
                elevator_val=elevator_val,
                flap_mode=flap_mode,
                flap_val=flap_val
            )


    elif mode == "Modify":
        if name not in target_dict:
            messagebox.showwarning("Error", f"No entry named '{name}' exists.")
            return
        
        if tab_type == 'Geometry':
            from input_windows import apply_geometry_surface
            apply_geometry_surface(tab)
            return
        
        if tab_type == "Properties":
            draft = property_drafts.get(name)
            if not draft:
                messagebox.showerror("Error", f"No property data found for '{name}'. Please enter values.")
                return
            valid, error_msg = validate_property_fields(draft)
            if not valid:
                messagebox.showerror("Invalid Input", error_msg)
                return
            
            try:
                mass_val = float(draft.get("Mass", 0))
                inertia_vals = [float(draft.get(k, 0)) for k in ['Ixx', 'Iyy', 'Izz', 'Ixy', 'Ixz', 'Iyz']]
            except ValueError:
                messagebox.showerror("Invalid Input", "Mass and inertia fields must be valid numbers.")
                return

            if mass_val <= 0 or any(i < 0 for i in inertia_vals):
                messagebox.showerror("Invalid Input", "Mass must be > 0 and/or inertia values must be ≥ 0.")
                return

            target_dict[name] = MassProperty(
                name,
                float(draft.get("Mass", 0)),
                float(draft.get("X", 0)),
                float(draft.get("Y", 0)),
                float(draft.get("Z", 0)),
                float(draft.get("Ixx", 0)),
                float(draft.get("Iyy", 0)),
                float(draft.get("Izz", 0)),
                float(draft.get("Ixy", 0)),
                float(draft.get("Ixz", 0)),
                float(draft.get("Iyz", 0))
            )
        
        elif tab_type == "Cases":
            draft = property_drafts.get(name)
            if not draft:
                messagebox.showerror("Error", f"No case data found for '{name}'. Please enter values.")
                return

            try:
                # 1. Check all required fields are filled
                required_fields = ["Mach", "Rho", "Cdo","AOA Mode", "AOA Val"]
                for key in required_fields:
                    if key not in draft or draft[key].strip() == "":
                        raise ValueError(f"{key} must be filled.")

                # 2. Attempt to cast all values to float
                Mach = float(draft["Mach"])
                rho = float(draft["Rho"])
                cdo = float(draft["Cdo"])
                aoa_mode = draft["AOA Mode"]
                aoa_val = float(draft["AOA Val"])

                elevator_mode = draft.get("Elevator Mode") or None
                elevator_val = float(draft["Elevator Val"]) if "Elevator Val" in draft and draft["Elevator Val"].strip() else None

                flap_mode = draft.get("Flap Mode") or None
                flap_val = float(draft["Flap Val"]) if "Flap Val" in draft and draft["Flap Val"].strip() else None

                # 3. Check Mach and Rho are positive
                if Mach < 0 or rho <= 0 or cdo < 0:
                    raise ValueError("Mach and Rho must be positive.")

                # 4. Disallow AOA and Elevator both being set to "Cm"
                if aoa_mode == "Cm" and elevator_mode == "Cm":
                    raise ValueError("AOA and Elevator modes cannot both be set to 'Cm'.")

                # Assign to aircraft
                target_dict[name] = SimulationCase(
                    name=name,
                    Mach=Mach,
                    rho=rho,
                    Cdo=cdo,
                    aoa_mode=aoa_mode,
                    aoa_val=aoa_val,
                    elevator_mode=elevator_mode,
                    elevator_val=elevator_val,
                    flap_mode=flap_mode,
                    flap_val=flap_val
                )

            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))
                return

    elif mode == "Delete":
        if name not in target_dict:
            messagebox.showwarning("Error", f"No entry named '{name}' exists.")
            return
        del target_dict[name]

    tab.update_listbox(target_dict.keys())

    if hasattr(tab.tab_frame.master, 'analysis_tab'):
        tab.tab_frame.master.analysis_tab.refresh_lists()
    if hasattr(tab.tab_frame.master, 'results_tab'):
        tab.tab_frame.master.results_tab.refresh_job_list()

# ======== Tab Switching Cleanup ========
def on_tab_changed(event):
    property_drafts.clear()
    selected_tab = event.widget.nametowidget(event.widget.select())
    if hasattr(selected_tab, 'refresh_lists'):
        selected_tab.refresh_lists()
    elif hasattr(selected_tab, 'refresh_job_list'):
        selected_tab.refresh_job_list()

# ======== Main Window Launcher ========
def open_main_window():
    main_window = tk.Toplevel()
    main_window.title("PAVL Workspace")
    main_window.geometry("800x600")
    main_window.iconbitmap("assets/icon1.ico")

    menu_bar = tk.Menu(main_window)
    main_window.config(menu=menu_bar)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="New", command=lambda: None)
    file_menu.add_command(label="Open", command=lambda: None)
    file_menu.add_command(label="Save", command=lambda: None)
    file_menu.add_command(label="Save As", command=lambda: None)
    menu_bar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="Documentation", command=lambda: messagebox.showinfo("Documentation", "Idk figure it out."))
    menu_bar.add_cascade(label="Help", menu=help_menu)

    tab_control = ttk.Notebook(main_window)
    geometry_tab = SurfaceTab(tab_control, "Geometry", geometry_input_window, apply_inputs)
    properties_tab = SurfaceTab(tab_control, "Properties", properties_input_window, apply_inputs)
    case_tab = SurfaceTab(tab_control, "Cases", case_input_window, apply_inputs)
    analysis_tab = AnalysisTab(tab_control)
    results_tab = ResultsTab(tab_control)

    tab_control.analysis_tab = analysis_tab
    tab_control.results_tab = results_tab

    tab_control.pack(expand=1, fill="both")
    tab_control.bind("<<NotebookTabChanged>>", on_tab_changed)

    def on_geometry_listbox_select(event):
        if geometry_tab.mode_var.get() != "Delete":
            geometry_input_window(geometry_tab, force_object_load=True)

    def on_properties_listbox_select(event):
        if properties_tab.mode_var.get() != "Delete":
            properties_input_window(properties_tab, force_object_load=True)

    def on_case_listbox_select(event):
        if case_tab.mode_var.get() != "Delete":
            case_input_window(case_tab, force_object_load=True)

    geometry_tab.listbox.bind("<Double-1>", on_geometry_listbox_select)
    properties_tab.listbox.bind("<Double-1>", on_properties_listbox_select)
    case_tab.listbox.bind("<Double-1>", on_case_listbox_select)
