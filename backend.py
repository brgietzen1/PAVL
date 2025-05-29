from models import Aircraft, SimulationCase, GeometrySurface, MassProperty
import numpy as np

def write_avl_file(jobname: str, aircraft: Aircraft, sim_case: SimulationCase, geom, filepath: str):

    """
    Writes a .avl file formatted for AVL's LOAD command.

    Parameters:
        jobname (str): Identifier written in the comment header line.
        aircraft (Aircraft): Global aircraft model containing properties global to session.
        sim_case (SimulationCase): The selected simulation case.
        filepath (str): Path to write the .avl file (e.g., "results/jobname.avl").
    """
    
    lines = []
    lines.append(jobname)
    lines.append(f"{sim_case.Mach:.1f}                   !   Mach")
    lines.append("0     0     0.0       !   iYsym  iZsym  Zsym")
    lines.append("{:.4g} {:.4g} {:.4g}       !   Sref   Cref   Bref".format(aircraft.Sref, aircraft.Cref, aircraft.Bref))
    lines.append("0.00  0.0   0.0       !   Xref   Yref   Zref   moment reference location (arb.)")
    lines.append(f"{sim_case.Cdo:.5f}                 !   CDp")
    
    for surface in aircraft.geometry.values():
        lines.extend(write_surface(surface))
    
    with open(filepath, "w") as f:
        f.write("\n".join(lines))


def write_surface(surface: GeometrySurface) -> list[str]:
    """
    Returns a list of strings representing the AVL-formatted surface definition.

    Parameters:
        surface (GeometrySurface): A single surface object containing position and incidence angle.

    Returns:
        List[str]: Lines defining the surface block in .avl format.
    """
    lines = []
    lines.append("")
    lines.append("#")
    lines.append("#==============================================================")
    lines.append("#")

    lines.append("SURFACE")
    lines.append(surface.name)  
    lines.append("10  1.0  22  1.0   ! Nchord   Cspace   Nspan  Sspace")
    lines.append("#")
    # Symmetry plane
    lines.append("YDUPLICATE")
    lines.append("     0.00000")
    lines.append("")
    # Incidence angle (twist bias for the whole surface)
    lines.append("ANGLE")
    lines.append(f"     {surface.incidence:.4f}")

    # Optional scale factors (keep at 1.0 for now)
    lines.append("SCALE")
    lines.append("  1.0   1.0   1.0")

    # Position offset (x, y, z)
    lines.append("TRANSLATE")
    lines.append(f"    {surface.x:.5f}     {surface.y:.5f}     {surface.z:.5f}")

    total_span = compute_total_span(surface)
    attach_controls_to_sections(surface)
    #control_points = get_control_breakpoints(surface, total_span)
    lines.extend(write_section_block(surface, total_span))

    return lines




def compute_xle(section, chord_mode: str, sweep_mode: str, current_span: float) -> float:
    taper = float(section.get("Taper", 1))
    sweep_le = float(section.get("LE Sweep", 0))
    sweep_c4 = float(section.get("C/4 Sweep", 0))

    if chord_mode == "Taper+Root":
        root_c = float(section["Root C"])
        tip_c = taper * root_c
    elif chord_mode == "Taper+Tip":
        tip_c = float(section["Tip C"])
        root_c = tip_c / taper
    elif chord_mode == "Root+Tip":
        root_c = float(section["Root C"])
        tip_c = float(section["Tip C"])
    else:
        raise ValueError(f"Unsupported chord mode: {chord_mode}")

    if sweep_mode == "LE":
        x_le = current_span * np.tan(np.radians(sweep_le))
    elif sweep_mode == "C4":
        x_c4r = root_c / 4
        x_c4t = x_c4r + current_span * np.tan(np.radians(sweep_c4))
        x_le = x_c4t - tip_c / 4
    else:
        raise ValueError(f"Unsupported sweep mode: {sweep_mode}")

    return x_le

def compute_yle(section, chord_mode: str, sweep_mode: str, current_span: float) -> float:
    dihedral = float(section.get("Dihedral", 0))
    return current_span * np.cos(np.radians(dihedral))

def compute_zle(section, chord_mode: str, sweep_mode: str, current_span: float) -> float:
    dihedral = float(section.get("Dihedral", 0))
    return current_span * np.sin(np.radians(dihedral))

def compute_ainc(surface, current_span: float, total_span: float) -> float:
    twist = surface.twist 
    return (twist / total_span) * current_span if total_span > 0 else 0.0

def compute_chord(section, chord_mode: str, sweep_mode: str, current_span: float, index) -> float:
    taper = float(section.get("Taper", 1))
    if chord_mode == "Taper+Root":
        root_c = float(section["Root C"])
        tip_c = taper * root_c
    elif chord_mode == "Taper+Tip":
        tip_c = float(section["Tip C"])
        root_c = tip_c / taper
    elif chord_mode == "Root+Tip":
        root_c = float(section["Root C"])
        tip_c = float(section["Tip C"])
    else:
        raise ValueError(f"Unsupported chord mode: {chord_mode}")
    return root_c if index == 0 else tip_c

def compute_total_span(surface):
    return sum(float(s["Span"]) for s in surface.sections)

def attach_controls_to_sections(surface: GeometrySurface):
    """
    Links each control surface definition to the appropriate section(s)
    based on Inboard/Outboard span locations.
    """
    total_span = compute_total_span(surface)
    for control in surface.control_surfaces:
        try:
            y_inboard = float(control["Inboard Loc"]) * total_span
            y_outboard = float(control["Outboard Loc"]) * total_span
        except ValueError:
            continue

        current_span = 0.0
        for section in surface.sections:
            span = float(section.get("Span", 0))
            next_span = current_span + span

            # Does this section fall within the control span range?
            if current_span <= y_outboard and next_span >= y_inboard:
                section.update(control)  # Copy all relevant fields
            current_span = next_span


def get_control_breakpoints_from_controls(surface: GeometrySurface, total_span: float) -> list[dict]:
    """
    Converts control surfaces into spanwise breakpoints for AVL.
    Pulls from surface.control_surfaces, not section data.
    """
    control_breakpoints = []

    for control in surface.control_surfaces:
        try:
            y_inboard = float(control["Inboard Loc"]) * total_span
            y_outboard = float(control["Outboard Loc"]) * total_span
            hinge_loc = float(control["Hinge Loc"])
        except (KeyError, ValueError):
            continue

        control_metadata = {
            "name": control["Control Name"],
            "hinge": hinge_loc,
            "type": control.get("Control Type", "Elevator"),
        }

        control_breakpoints.append({
            "span": y_inboard,
            "is_control": True,
            "position": "inboard",
            "control": control_metadata
        })
        control_breakpoints.append({
            "span": y_outboard,
            "is_control": True,
            "position": "outboard",
            "control": control_metadata
        })

    return control_breakpoints




def interpolate_geometry_at_span(surface: GeometrySurface, span_target: float, total_span: float) -> dict:
    """
    Interpolates Xle, Yle, Zle, chord, and ainc at a given spanwise location
    based on internal AVL-section representation derived from PAVL sections.
    """
    current_span = 0.0
    for section in surface.sections:
        local_span = float(section["Span"])
        span_start = current_span
        span_end = current_span + local_span

        if span_start <= span_target <= span_end:
            t = (span_target - span_start) / local_span

            chord_mode = section.get("ChordMode", "Taper+Root")
            sweep_mode = section.get("SweepMode", "LE")
            root_c, tip_c, _ = resolve_chord_lengths(section)
            chord = (1 - t) * root_c + t * tip_c

            xle_root = compute_xle(section, chord_mode, sweep_mode, span_start)
            xle_tip = compute_xle(section, chord_mode, sweep_mode, span_end)
            xle = (1 - t) * xle_root + t * xle_tip

            yle_root = compute_yle(section, chord_mode, sweep_mode, span_start)
            yle_tip = compute_yle(section, chord_mode, sweep_mode, span_end)
            yle = (1 - t) * yle_root + t * yle_tip

            zle_root = compute_zle(section, chord_mode, sweep_mode, span_start)
            zle_tip = compute_zle(section, chord_mode, sweep_mode, span_end)
            zle = (1 - t) * zle_root + t * zle_tip

            ainc_root = compute_ainc(surface, span_start, total_span)
            ainc_tip = compute_ainc(surface, span_end, total_span)
            ainc = (1 - t) * ainc_root + t * ainc_tip

            return {
                "span": span_target,
                "Xle": xle,
                "Yle": yle,
                "Zle": zle,
                "chord": chord,
                "ainc": ainc,
            }

        current_span = span_end

    raise ValueError(f"Could not interpolate geometry at span={span_target:.4f}")



def resolve_chord_lengths(section: dict) -> tuple[float, float, float]:
    """
    Resolves root and tip chord lengths from a section dictionary based on chord mode.

    Returns:
        root_c (float): Root chord length
        tip_c (float): Tip chord length
        taper (float): Taper ratio (tip_c / root_c)
    """
    mode = section.get("ChordMode", "Taper+Root")

    if mode == "Taper+Root":
        root_c = float(section["Root C"])
        taper = float(section["Taper"])
        tip_c = root_c * taper

    elif mode == "Taper+Tip":
        tip_c = float(section["Tip C"])
        taper = float(section["Taper"])
        root_c = tip_c / taper

    elif mode == "Root+Tip":
        root_c = float(section["Root C"])
        tip_c = float(section["Tip C"])
        taper = tip_c / root_c

    else:
        raise ValueError(f"Unsupported ChordMode: {mode}")

    return root_c, tip_c, taper

def assemble_augmented_sections(surface: GeometrySurface, total_span: float) -> list[dict]:
    """
    Combines interpolated control breakpoints with original user-defined sections,
    preserving AVL-compatible spanwise order.
    """
    sections_out = []
    current_span = 0.0
    original_sections = surface.sections

    
    control_points = get_control_breakpoints_from_controls(surface, total_span)
    interpolated_controls = []
    for control_bp in control_points:
        geom = interpolate_geometry_at_span(surface, control_bp["span"], total_span)
        geom.update({
            "is_control": True,
            "control": control_bp["control"]
        })
        interpolated_controls.append(geom)

    
    for i, section in enumerate(original_sections):
        span = float(section["Span"])
        current_span += span

        
        chord_mode = section.get("ChordMode", "Taper+Root")
        sweep_mode = section.get("SweepMode", "LE")
        root_c, tip_c, _ = resolve_chord_lengths(section)
        xle = compute_xle(section, chord_mode, sweep_mode, current_span)
        yle = compute_yle(section, chord_mode, sweep_mode, current_span)
        zle = compute_zle(section, chord_mode, sweep_mode, current_span)
        chord = tip_c
        ainc = compute_ainc(surface, current_span, total_span)

        sections_out.append({
            "span": current_span,
            "Xle": xle,
            "Yle": yle,
            "Zle": zle,
            "chord": chord,
            "ainc": ainc,
            "is_control": False
        })

    
    all_sections = sections_out + interpolated_controls
    all_sections.sort(key=lambda s: s["span"])

    return all_sections

def write_section_block(surface, total_span):
    section_lines = []
    seen_spans = set()

    def write_section_block_line(sec):
        section_lines.append("")
        section_lines.append("#--------------------------------------------------------------")
        section_lines.append("#    Xle         Yle         Zle         chord       ainc")
        section_lines.append("SECTION")
        section_lines.append(f"    {sec['Xle']:.5f}     {sec['Yle']:.5f}     {sec['Zle']:.5f}     {sec['chord']:.5f}     {sec['ainc']:.4f}")
        section_lines.append("NACA")
        section_lines.append(surface.naca_airfoil)
        return section_lines

    # === Interpolated control sections ===
    control_sections = []
    control_points = get_control_breakpoints_from_controls(surface, total_span)
    for control_bp in control_points:
        try:
            interp = interpolate_geometry_at_span(surface, control_bp["span"], total_span)
            interp.update({
                "is_control": True,
                "control": control_bp["control"]
            })
            control_sections.append(interp)
        except ValueError as e:
            print(f"[ERROR] Failed to interpolate control section: {e}")
            continue

    # === User-defined section tips ===
    current_span = 0.0
    tip_sections = []
    for i, section in enumerate(surface.sections):
        local_span = float(section["Span"])
        current_span += local_span

        chord_mode = section.get("ChordMode", "Taper+Root")
        sweep_mode = section.get("SweepMode", "LE")

        xle = compute_xle(section, chord_mode, sweep_mode, current_span)
        yle = compute_yle(section, chord_mode, sweep_mode, current_span)
        zle = compute_zle(section, chord_mode, sweep_mode, current_span)
        chord = compute_chord(section, chord_mode, sweep_mode, current_span, i + 1)
        ainc = compute_ainc(surface, current_span, total_span)

        tip_sections.append({
            "span": current_span,
            "Xle": xle,
            "Yle": yle,
            "Zle": zle,
            "chord": chord,
            "ainc": ainc,
            "is_control": False
        })

    # === Root section ===
    root = surface.sections[0]
    root_chord_mode = root.get("ChordMode", "Taper+Root")
    root_sweep_mode = root.get("SweepMode", "LE")
    root_c = compute_chord(root, root_chord_mode, root_sweep_mode, 0.0, 0)
    root_section = {
        "span": 0.0,
        "Xle": 0.0,
        "Yle": 0.0,
        "Zle": 0.0,
        "chord": root_c,
        "ainc": 0.0,
        "is_control": False
    }

    all_sections = [root_section] + tip_sections + control_sections
    all_sections.sort(key=lambda s: s["span"])

    for sec in all_sections:
        if sec["span"] in seen_spans:
            continue
        seen_spans.add(sec["span"])
        write_section_block_line(sec)

        if sec.get("is_control"):
            ctrl = sec["control"]
            print(f"Writing control surface: {ctrl['name']} at span {sec['span']:.2f}")
            xhinge = ctrl["hinge"]
            ctrl_type = ctrl["type"]
            hinge_vec = "0.0 0.0 1.0" if ctrl_type.lower() == "rudder" else "0.0 1.0 0.0"
            signdup = -1.0 if ctrl_type.lower() == "aileron" else 1.0
            section_lines.append("CONTROL")
            section_lines.append(f"    {ctrl['name']}     1.0     {xhinge:.3f}     {hinge_vec}     {signdup:.1f}")

    return section_lines






def write_mass_file(jobname: str, aircraft: Aircraft, sim_case: SimulationCase, filepath: str):
    """
    Create a formatted .mass file matching AVL specification and layout.

    Parameters:
        jobname (str): Identifier written in the comment header line.
        aircraft (Aircraft): Global aircraft model containing mass properties and unit system.
        sim_case (SimulationCase): The selected simulation case providing rho.
        filepath (str): Path to write the .mass file (e.g., "results/jobname.mass").
    """

    # Unit handling
    units = aircraft.units.upper()
    if units == "MKS":
        Lunit_str, Munit_str, Tunit_str = "m", "kg", "s"
        g = 9.81
    elif units == "FPS":
        Lunit_str, Munit_str, Tunit_str = "ft", "slug", "s"
        g = 32.17
    else:
        raise ValueError(f"Unknown unit system: {units}")

    # Header lines
    lines = []
    lines.append("#1")
    lines.append(f"# {jobname}")
    lines.append(f"Lunit = 1.0     {Lunit_str}")
    lines.append(f"Munit = 1.0     {Munit_str}")
    lines.append(f"Tunit = 1.0     {Tunit_str}")
    lines.append(f"g     = {g:<8.2f}")
    lines.append(f"rho   = {sim_case.rho:<8.5f}")
    lines.append("")

    # Format and add each mass property component
    for name, prop in aircraft.mass_properties.items():
        mass_line = (
            f"{prop.mass:<10.6f} {prop.x:<10.6f} {prop.y:<10.6f} {prop.z:<10.6f} "
            f"{prop.Ixx:<10.6f} {prop.Iyy:<10.6f} {prop.Izz:<10.6f} "
            f"{prop.Ixy:<10.6f} {prop.Ixz:<10.6f} {prop.Iyz:<10.6f} ! {name}"
        )
        lines.append(mass_line)

    # Write to file
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_run_file(jobname: str, sim_case, filepath: str):
    """
    Writes a .run file formatted for AVL's CASE command.

    Parameters:
        jobname (str): The name used for the CASE field.
        sim_case (SimulationCase): The input conditions for the simulation.
        filepath (str): The full path to write the .run file.
    """
    lines = []
    lines.append("")
    lines.append("---------------------------------------------")
    lines.append(f" Run case  1:  {jobname}")
    lines.append("")

    # AoA / CL / Cm pitchmom
    if sim_case.aoa_mode == "Angle":
        lines.append(f" alpha        ->  alpha       =   {sim_case.aoa_val:<8.4f}")
    elif sim_case.aoa_mode == "CL":
        lines.append(f" alpha        ->  CL          =   {sim_case.aoa_val:<8.4f}")
    elif sim_case.aoa_mode == "Cm":
        lines.append(f" alpha        ->  Cm pitchmom =   {sim_case.aoa_val:<8.4f}")

    lines.append(f" beta         ->  beta        =   0.00000")
    lines.append(f" pb/2V        ->  pb/2V       =   0.00000")
    lines.append(f" qc/2V        ->  qc/2V       =   0.00000")
    lines.append(f" rb/2V        ->  rb/2V       =   0.00000")

    # Flap
    if sim_case.flap_mode == "Deflection":
        lines.append(f" flap         ->  flap        =   {sim_case.flap_val:<8.4f}")


    # Elevator
    if sim_case.elevator_mode == "Deflection":
        lines.append(f" elevator     ->  elevator    =   {sim_case.elevator_val:<8.4f}")
    elif sim_case.elevator_mode == "Cm":
        lines.append(f" elevator     ->  Cm pitchmom =   {sim_case.elevator_val:<8.4f}")


    lines.append("")

    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")








