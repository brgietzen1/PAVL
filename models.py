# File: models.py

class GeometrySurface:
    def __init__(self, name):
        self.name = name
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.incidence = 0.0
        self.twist = 0.0
        self.naca_airfoil = ""

        self.sections = []  # List of dicts with fields like AR, Span, Taper, etc.
        self.control_surfaces = []  # List of dicts with type and positions

class MassProperty:
    def __init__(self, name, mass=0, x=0, y=0, z=0, Ixx=0, Iyy=0, Izz=0, Ixy=0, Ixz=0, Iyz=0):
        self.name = name
        self.mass = mass
        self.x = x
        self.y = y
        self.z = z
        self.Ixx = Ixx
        self.Iyy = Iyy
        self.Izz = Izz
        self.Ixy = Ixy
        self.Ixz = Ixz
        self.Iyz = Iyz

class SimulationCase:
    def __init__(self, name, Mach=0.0, rho=0.0, Cdo=0.0,
                 aoa_mode="Angle", aoa_val=0.0,
                 elevator_mode=None, elevator_val=None,
                 flap_mode=None, flap_val=None):
        self.name = name
        self.Mach = Mach
        self.rho = rho
        self.Cdo = Cdo

        self.aoa_mode = aoa_mode      # "Angle", "CL", or "Cm"
        self.aoa_val = aoa_val

        self.elevator_mode = elevator_mode  # "Deflection" or "Cm", or None
        self.elevator_val = elevator_val    # float or None

        self.flap_mode = flap_mode    # "Deflection", or None
        self.flap_val = flap_val      # float or None


class Aircraft:
    def __init__(self, units = "MKS", g=0, Sref=0, Cref=0, Bref=0):
        self.geometry = {}
        self.mass_properties = {}
        self.simulation_cases = {}
        self.units = units
        self.Sref = Sref
        self.Cref = Cref
        self.Bref = Bref
        self.session_jobs = set()

# Global aircraft instance
aircraft = Aircraft()

# Temporary storage for draft values from Input Properties window
property_drafts = {}

def validate_property_fields(fields):
    required_keys = ['Mass', 'X', 'Y', 'Z']
    for key in required_keys:
        if key not in fields or not fields[key].strip():
            return False, f"{key} is required."
        try:
            float(fields[key])
        except ValueError:
            return False, f"{key} must be a number."
    return True, ""
