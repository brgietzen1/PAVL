# File: input_windows.py

import tkinter as tk
from tkinter import ttk, messagebox
from models import property_drafts, GeometrySurface, aircraft
import math

# New GeometryPropertyEditor class
import tkinter as tk
from tkinter import ttk, messagebox
from models import property_drafts, GeometrySurface, aircraft
import numpy as np

class GeometryPropertyEditor:
    def __init__(self, parent, name, existing_values=None):
        # Load draft if no explicit values are passed
        if existing_values is None and name in property_drafts:
            existing_values = property_drafts[name]
        elif existing_values is None and name in aircraft.geometry:
            # Load from existing saved object if it exists
            gs = aircraft.geometry[name]
            existing_values = {
                "X Loc": str(gs.x),
                "Y Loc": str(gs.y),
                "Z Loc": str(gs.z),
                "Incidence": str(gs.incidence),
                "Twist": str(gs.twist),
                "NACA Airfoil": gs.naca_airfoil,
                "Sections": gs.sections,
                "Controls": gs.control_surfaces
            }
        self.name = name
        self.sections = []
        self.controls = []

        self.top = tk.Toplevel(parent)
        self.top.title("Input Properties")
        self.top.iconbitmap("assets/icon1.ico")

        self.header_frame = ttk.Frame(self.top)
        self.header_frame.pack(pady=5)
        self.create_output_labels(self.header_frame)

        self.canvas = tk.Canvas(self.top, borderwidth=0)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.vsb = tk.Scrollbar(self.top, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4, 4), window=self.scroll_frame, anchor="nw",
                                  tags="self.scroll_frame")

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.create_static_entries(self.scroll_frame)

        self.type_var = tk.StringVar()
        ttk.Label(self.scroll_frame, text="Geometry Type:").grid(row=11, column=0, sticky="w")
        self.type_combo = ttk.Combobox(self.scroll_frame, textvariable=self.type_var,
                                       values=["Section", "Control Surface"], state="readonly")
        self.type_combo.grid(row=11, column=1)
        self.add_button = ttk.Button(self.scroll_frame, text="Add", command=self.add_geometry_type)
        self.add_button.grid(row=11, column=2)

        self.section_container = ttk.Frame(self.scroll_frame)
        self.section_container.grid(row=12, column=0, columnspan=3, pady=5, sticky="ew")
        self.control_container = ttk.Frame(self.scroll_frame)
        self.control_container.grid(row=13, column=0, columnspan=3, pady=5, sticky="ew")

        self.bottom_frame = ttk.Frame(self.top)
        self.bottom_frame.pack(pady=10)
        ttk.Button(self.bottom_frame, text="OK", command=self.save_draft).pack(side="left", padx=5)
        ttk.Button(self.bottom_frame, text="Cancel", command=self.top.destroy).pack(side="left", padx=5)

        if existing_values:
            self.load_existing_values(existing_values)

    def create_output_labels(self, parent):
        self.output_vars = {key: tk.StringVar(value="-") for key in ["Total Span", "Total AR", "Projected Span", "MAC", "Total Area"]}
        for i, (label, var) in enumerate(self.output_vars.items()):
            ttk.Label(parent, text=label + ":").grid(row=i, column=0, sticky="e", padx=5)
            ttk.Label(parent, textvariable=var).grid(row=i, column=1, sticky="w", padx=5)

    def create_static_entries(self, parent):
        self.static_vars = {}
        fields = ["X Loc", "Y Loc", "Z Loc", "Incidence", "Twist", "NACA Airfoil"]
        for i, field in enumerate(fields):
            ttk.Label(parent, text=field + ":").grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(parent)
            entry.grid(row=i, column=1, sticky="ew", columnspan=2)
            self.static_vars[field] = entry

    def add_geometry_type(self):
        geom_type = self.type_var.get()
        if geom_type == "Section":
            self.add_section()
        elif geom_type == "Control Surface":
            self.add_control_surface()

    def add_section(self, chord_mode="Taper+Root", sweep_mode="LE"):
        index = len(self.sections) + 1
        frame = ttk.LabelFrame(self.section_container, text=f"Section {index}", padding=5)
        frame.pack(fill="x", pady=2)

        fields = ["Span", "Taper", "Root C", "Tip C", "LE Sweep", "C/4 Sweep", "Dihedral"]
        entries = {}
        radio_vars = {"Chord": tk.StringVar(value=chord_mode), "Sweep": tk.StringVar(value=sweep_mode)}

        for i, label in enumerate(fields):
            # Radio buttons and label layout
            if label in ["Taper", "Root C", "Tip C"]:
                ttk.Radiobutton(frame, variable=radio_vars["Chord"], value="Taper+Root" if label == "Tip C" else
                                ("Taper+Tip" if label == "Root C" else "Root+Tip"), command=lambda rv=radio_vars, e=entries: self.update_chord_states(rv, e)).grid(row=i, column=0)
            elif label in ["LE Sweep", "C/4 Sweep"]:
                ttk.Radiobutton(frame, variable=radio_vars["Sweep"], value="LE" if label == "LE Sweep" else "C4", command=lambda rv=radio_vars, e=entries: self.update_sweep_states(rv, e)).grid(row=i, column=0)
            else:
                ttk.Label(frame, text="").grid(row=i, column=0)  # Empty cell

            ttk.Label(frame, text=label).grid(row=i, column=1, sticky="w")
            entry = ttk.Entry(frame)
            entry.grid(row=i, column=2)
            entry.bind("<FocusOut>", lambda e: self.update_summary_labels())
            entries[label] = entry

        

        delete_btn = ttk.Button(frame, text="Delete", command=lambda idx=index-1: self.delete_section(idx))
        delete_btn.grid(row=len(fields), column=1, columnspan=2, pady=5)
        self.sections.append({"frame": frame, "entries": entries, "radios": radio_vars})
        delete_btn.grid(row=len(fields), column=1, columnspan=2, pady=5)

        self.update_chord_states(radio_vars, entries)
        self.update_sweep_states(radio_vars, entries)
       

    def delete_section(self, idx):
        if 0 <= idx < len(self.sections):
            self.sections[idx]["frame"].destroy()
            self.sections.pop(idx)
            for i, section in enumerate(self.sections):
                section["frame"].config(text=f"Section {i+1}")

    def add_control_surface(self):
        index = len(self.controls) + 1
        frame = ttk.LabelFrame(self.control_container, text=f"Control Surface {index}", padding=5)
        frame.pack(fill="x", pady=2)

        ttk.Label(frame, text="Control Type:").grid(row=0, column=0)
        control_type = ttk.Combobox(frame, values=["Aileron", "Elevator", "Rudder", "Flap"], state="readonly")
        control_type.grid(row=0, column=1)

        entries = {}
        labels = ["Hinge Loc", "Inboard Loc", "Outboard Loc"]
        for i, label in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=i+1, column=0)
            entry = ttk.Entry(frame, validate="focusout",
                              validatecommand=(frame.register(self.validate_fraction), "%P"))
            entry.grid(row=i+1, column=1)
            entries[label] = entry

        delete_btn = ttk.Button(frame, text="Delete", command=lambda idx=index-1: self.delete_control(idx))
        delete_btn.grid(row=len(labels)+1, column=0, columnspan=2, pady=5)
        self.controls.append({"frame": frame, "entries": entries, "type": control_type})

    def delete_control(self, idx):
        if 0 <= idx < len(self.controls):
            self.controls[idx]["frame"].destroy()
            self.controls.pop(idx)
            for i, control in enumerate(self.controls):
                control["frame"].config(text=f"Control Surface {i+1}")

    def validate_fraction(self, value):
        try:
            val = float(value)
            return 0 <= val <= 1
        except ValueError:
            return False

    def save_draft(self):
        try:
            draft = {
                "X Loc": self.static_vars["X Loc"].get(),
                "Y Loc": self.static_vars["Y Loc"].get(),
                "Z Loc": self.static_vars["Z Loc"].get(),
                "Incidence": self.static_vars["Incidence"].get(),
                "Twist": self.static_vars["Twist"].get(),
                "NACA Airfoil": self.static_vars["NACA Airfoil"].get(),
                "Sections": [],
                "Controls": []
            }

            prev_tip = None  # To store the tip chord of the previous section

            for i, s in enumerate(self.sections):
                section_vals = {}
                for k, v in s["entries"].items():
                    if not v.instate(['disabled']):
                        value = v.get().strip()
                        if not value:
                            raise ValueError(f"'{k}' must be filled for each section.")
                        section_vals[k] = value
                    else:
                        v.delete(0, tk.END)

                chord_mode = s["radios"]["Chord"].get()
                section_vals["ChordMode"] = chord_mode
                section_vals["SweepMode"] = s["radios"]["Sweep"].get()

                # Resolve root and tip chords
                root_c = tip_c = None
                if chord_mode == "Taper+Root":
                    root_c = float(section_vals["Root C"])
                    tip_c = root_c * float(section_vals["Taper"])
                elif chord_mode == "Taper+Tip":
                    tip_c = float(section_vals["Tip C"])
                    root_c = tip_c / float(section_vals["Taper"])
                elif chord_mode == "Root+Tip":
                    root_c = float(section_vals["Root C"])
                    tip_c = float(section_vals["Tip C"])

                # Continuity check
                if prev_tip is not None and abs(root_c - prev_tip) > 1e-6:
                    raise ValueError(f"Chord discontinuity between sections {i} and {i+1}: previous tip {prev_tip:.4f}, current root {root_c:.4f}")

                prev_tip = tip_c
                draft["Sections"].append(section_vals)

            for j,c in enumerate(self.controls):

                required_keys = ["Hinge Loc", "Inboard Loc", "Outboard Loc"]
                if not all(k in c["entries"] for k in required_keys):
                    print(f"[ERROR] Control {j} is missing keys: {c['entries'].keys()}")
                    continue    

                control_vals = {k: c["entries"][k].get() for k in c["entries"]}
                control_type = c["type"].get()
                if any(not v.strip() for v in control_vals.values()) or not control_type:
                    raise ValueError("All control surface fields must be filled")
                control_vals["Control Type"] = control_type
                control_vals["Control Name"] = f"{self.name}_{control_type.lower()}_{j + 1}"
                draft["Controls"].append(control_vals)

            property_drafts[self.name] = draft
            self.top.destroy()

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))

    
    def disable_and_clear(self, entry):
        #print("Clearing:", entry)
        entry.config(state="disabled")
        entry.delete(0, tk.END)

    def update_chord_states(self, radio_vars, entries):
        mode = radio_vars["Chord"].get()
        print(f"[ChordMode] Setting to: {mode}")

        if "Taper" in mode:
            entries["Taper"].config(state="normal")
            print("Taper: ENABLED")
        else:
            self.disable_and_clear(entries["Taper"])
            print("Taper: DISABLED + CLEARED")
    
        if "Root" in mode:
            entries["Root C"].config(state="normal")
            print("Root C: ENABLED")
        else:
            self.disable_and_clear(entries["Root C"])
            print("Root C: DISABLED + CLEARED")

        if "Tip" in mode:
            entries["Tip C"].config(state="normal")
            print("Tip C: ENABLED")
        else:
            self.disable_and_clear(entries["Tip C"])
            print("Tip C: DISABLED + CLEARED")

    def update_sweep_states(self, radio_vars, entries):
        mode = radio_vars["Sweep"].get()
        if mode == "LE":
            entries["LE Sweep"].config(state="normal")
            self.disable_and_clear(entries["C/4 Sweep"])
        else:
            entries["C/4 Sweep"].config(state="normal")
            self.disable_and_clear(entries["LE Sweep"])

    def load_existing_values(self, values):
        import copy
        for field, entry in self.static_vars.items():
            entry.insert(0, values.get(field, ""))

        for sec in values.get("Sections", []):
            self.add_section(chord_mode=sec.get("ChordMode", "Taper+Root"), sweep_mode=sec.get("SweepMode", "LE"))
            for k, v in sec.items():
                if k not in ["ChordMode", "SweepMode"]:
                    self.sections[-1]["entries"][k].insert(0, v)

            # Apply saved radio state
            sec_radios = self.sections[-1]["radios"]
            sec_radios["Chord"].set(sec.get("ChordMode", "Taper+Root"))
            sec_radios["Sweep"].set(sec.get("SweepMode", "LE"))

            self.update_chord_states(sec_radios, self.sections[-1]["entries"])
            self.update_sweep_states(sec_radios, self.sections[-1]["entries"])

        for con in values.get("Controls", []):
            # Check before adding anything to GUI
            if not all(k in con for k in ["Hinge Loc", "Inboard Loc", "Outboard Loc"]):
                print(f"[Warning] Skipping malformed control: {con}")
                continue

            self.add_control_surface()
            self.controls[-1]["type"].set(con.get("Control Type", ""))
            for k in ["Hinge Loc", "Inboard Loc", "Outboard Loc"]:
                self.controls[-1]["entries"][k].delete(0, tk.END)
                self.controls[-1]["entries"][k].insert(0, con.get(k, ""))



    def update_summary_labels(self):
        total_span = 0.0
        total_proj_span = 0.0
        total_area = 0.0
        mac_weighted = 0.0

        for sec in self.sections:
            try:
                e = sec["entries"]
                span = float(e["Span"].get()) if not e["Span"].instate(['disabled']) else 0.0
                root = float(e["Root C"].get()) if not e["Root C"].instate(['disabled']) else None
                tip = float(e["Tip C"].get()) if not e["Tip C"].instate(['disabled']) else None
                taper = float(e["Taper"].get()) if not e["Taper"].instate(['disabled']) else None
                dihedral = float(e["Dihedral"].get()) if not e["Dihedral"].instate(['disabled']) else 0.0

                if root is not None and tip is not None:
                    area = 0.5 * span * (root + tip)
                    mac = (2/3) * root * ((1 + tip/root + (tip/root)**2)/(1 + tip/root))
                
                elif taper is not None and root is not None:
                    c_tip = taper * root
                    area = 0.5 * span * (root + c_tip)
                    mac = (2/3) * root * ((1 + c_tip/root + (c_tip/root)**2)/(1 + c_tip/root))

                elif taper is not None and tip is not None:
                    c_root = tip/taper
                    area = 0.5 * span * (c_root + tip)
                    mac = (2/3) * c_root * ((1 + tip/c_root + (tip/c_root)**2)/(1 + tip/c_root))

                else:
                    area = 0.0
                    mac = 0.0

                total_span += span
                total_proj_span += span * np.cos(np.radians(dihedral))
                total_area += area
                mac_weighted += area * mac

            except Exception:
                continue

        total_mac = mac_weighted / total_area if total_area > 0 else 0.0
        total_ar = total_span**2 / total_area if total_area > 0 else 0.0

        self.output_vars["Total Span"].set(f"{total_span:.2f}")
        self.output_vars["Total AR"].set(f"{total_ar:.2f}")
        self.output_vars["Projected Span"].set(f"{total_proj_span:.2f}")
        self.output_vars["Total Area"].set(f"{total_area:.2f}")
        self.output_vars["MAC"].set(f"{total_mac:.2f}")

# ============ Apply logic for GeometrySurface ============
def apply_geometry_surface(tab):
    from models import GeometrySurface, property_drafts, aircraft

    name = tab.get_selected_name()
    if not name:
        messagebox.showwarning("Warning", "Name cannot be empty.")
        return

    if name not in property_drafts:
        messagebox.showerror("Error", f"No draft data found for '{name}'. Please enter values.")
        return

    try:
        draft = property_drafts[name]
        gs = GeometrySurface(name)
        gs.x = float(draft["X Loc"])
        gs.y = float(draft["Y Loc"])
        gs.z = float(draft["Z Loc"])
        gs.incidence = float(draft["Incidence"])
        gs.twist = float(draft["Twist"])
        gs.naca_airfoil = draft["NACA Airfoil"]
        gs.sections = draft["Sections"]
        gs.control_surfaces = draft["Controls"]

        aircraft.geometry[name] = gs
        tab.update_listbox(aircraft.geometry.keys())
        

    except Exception as e:
        messagebox.showerror("Error", f"Failed to apply geometry: {e}")


class MassPropertyEditor:
    def __init__(self, parent, name, existing_values=None):
        self.top = tk.Toplevel(parent)
        self.top.title("Input Properties")
        self.top.iconbitmap("assets/icon1.ico")

        self.entries = {}
        self.required_fields = ['Mass', 'X', 'Y', 'Z']
        self.inertia_fields = ['Ixx', 'Iyy', 'Izz', 'Ixy', 'Ixz', 'Iyz']
        labels = self.required_fields + self.inertia_fields

        for i, label in enumerate(labels):
            field_frame = ttk.Frame(self.top, padding=2, borderwidth=2)
            if label in self.required_fields:
                field_frame.config(relief="solid")
            field_frame.grid(row=i, column=0, columnspan=2, padx=5, pady=2, sticky="ew")

            ttk.Label(field_frame, text=label).grid(row=0, column=0, sticky='w', padx=5)
            entry = ttk.Entry(field_frame)
            entry.grid(row=0, column=1, padx=5)
            self.entries[label] = entry

        if existing_values:
            for key, entry in self.entries.items():
                entry.delete(0, tk.END)
                entry.insert(0, existing_values.get(key, ""))

        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        ok_btn = ttk.Button(button_frame, text="OK", command=self.save)
        ok_btn.grid(row=0, column=0, padx=5)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.top.destroy)
        cancel_btn.grid(row=0, column=1, padx=5)

        self.name = name

    def save(self):
        field_values = {key: entry.get().strip() for key, entry in self.entries.items()}

        # Only fill in default 0.0 for missing inertia fields
        for k in self.inertia_fields:
            if not field_values.get(k):
                field_values[k] = "0.0"

        # Do NOT override missing required fields; validation occurs at Apply
        property_drafts[self.name] = field_values
        self.top.destroy()


class SimulationCaseEditor:
    def __init__(self, parent, name, existing_values=None):
        from models import property_drafts, aircraft

        self.name = name
        self.top = tk.Toplevel(parent)
        self.top.title("Input Properties")
        self.top.iconbitmap("assets/icon1.ico")

        # === Frame Layout ===
        main = ttk.Frame(self.top, padding=10)
        main.grid(row=0, column=0, sticky="nsew")

        # Mach & Rho & Cdo
        ttk.Label(main, text="Mach:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.mach_entry = ttk.Entry(main)
        self.mach_entry.grid(row=0, column=1, padx=5)

        ttk.Label(main, text="Rho:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.rho_entry = ttk.Entry(main)
        self.rho_entry.grid(row=1, column=1, padx=5)

        ttk.Label(main, text="Cdo:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.cdo_entry = ttk.Entry(main)
        self.cdo_entry.grid(row=2, column=1, padx=5)

        ttk.Label(main, text="").grid(row=3, column=0)  # blank row

        # === AOA ===
        row = 4
        ttk.Label(main, text="AOA").grid(row=row, column=0, sticky="e", padx=5)
        self.aoa_mode = tk.StringVar(value="Angle")
        self.aoa_combo = ttk.Combobox(main, textvariable=self.aoa_mode, values=["Angle", "CL", "Cm"], state="readonly")
        self.aoa_combo.grid(row=row, column=1, padx=5)
        ttk.Label(main, text="=").grid(row=row, column=2)
        self.aoa_val = ttk.Entry(main)
        self.aoa_val.grid(row=row, column=3, padx=5)
        row += 1

        # Detect elevator/flap presence
        self.has_elevator = any(
            ctrl.get("Control Type") == "Elevator"
            for surf in aircraft.geometry.values()
            for ctrl in getattr(surf, "control_surfaces", [])
        )
        self.has_flap = any(
            ctrl.get("Control Type") == "Flap"
            for surf in aircraft.geometry.values()
            for ctrl in getattr(surf, "control_surfaces", [])
        )

        # Always define variables and widgets
        self.elevator_mode = tk.StringVar()
        self.elevator_val = ttk.Entry(main)

        if self.has_elevator:
            ttk.Label(main, text="Elevator").grid(row=row, column=0, sticky="e", padx=5)
            self.elevator_mode.set("Deflection")
            self.elevator_combo = ttk.Combobox(main, textvariable=self.elevator_mode, values=["Deflection", "Cm"], state="readonly")
            self.elevator_combo.grid(row=row, column=1, padx=5)
            ttk.Label(main, text="=").grid(row=row, column=2)
            self.elevator_val.grid(row=row, column=3, padx=5)
            row += 1
        else:
            self.elevator_mode.set("")
            self.elevator_combo = None
            self.elevator_val.grid_forget()

        self.flap_mode = tk.StringVar()
        self.flap_val = ttk.Entry(main)

        if self.has_flap:
            ttk.Label(main, text="Flap").grid(row=row, column=0, sticky="e", padx=5)
            self.flap_mode.set("Deflection")
            self.flap_combo = ttk.Combobox(main, textvariable=self.flap_mode, values=["Deflection"], state="readonly")
            self.flap_combo.grid(row=row, column=1, padx=5)
            ttk.Label(main, text="=").grid(row=row, column=2)
            self.flap_val.grid(row=row, column=3, padx=5)
            row += 1
        else:
            self.flap_mode.set("")
            self.flap_combo = None
            self.flap_val.grid_forget()

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.save).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.top.destroy).grid(row=0, column=1, padx=5)

        # Load existing values
        if existing_values:
            self.load_existing(existing_values)

    def load_existing(self, data):
        self.mach_entry.delete(0, tk.END)
        self.mach_entry.insert(0, data.get("Mach", ""))

        self.rho_entry.delete(0, tk.END)
        self.rho_entry.insert(0, data.get("Rho", ""))

        self.cdo_entry.delete(0, tk.END)
        self.cdo_entry.insert(0, data.get("Cdo", ""))

        self.aoa_mode.set(data.get("AOA Mode", "Angle"))
        self.aoa_val.delete(0, tk.END)
        self.aoa_val.insert(0, data.get("AOA Val", ""))

        if self.has_elevator and self.elevator_val.winfo_exists():
            self.elevator_mode.set(data.get("Elevator Mode", "Deflection"))
            self.elevator_val.delete(0, tk.END)
            self.elevator_val.insert(0, data.get("Elevator Val", ""))

        if self.has_flap and self.flap_val.winfo_exists():
            self.flap_mode.set(data.get("Flap Mode", "Deflection"))
            self.flap_val.delete(0, tk.END)
            self.flap_val.insert(0, data.get("Flap Val", ""))

    def save(self):
        values = {
            "Mach": self.mach_entry.get().strip(),
            "Rho": self.rho_entry.get().strip(),
            "Cdo": self.cdo_entry.get().strip(),
            "AOA Mode": self.aoa_mode.get(),
            "AOA Val": self.aoa_val.get().strip()
        }
        if self.has_elevator:
            values["Elevator Mode"] = self.elevator_mode.get()
            values["Elevator Val"] = self.elevator_val.get().strip()
        if self.has_flap:
            values["Flap Mode"] = self.flap_mode.get()
            values["Flap Val"] = self.flap_val.get().strip()

        from models import property_drafts
        property_drafts[self.name] = values
        self.top.destroy()
