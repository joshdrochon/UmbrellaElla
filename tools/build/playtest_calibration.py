"""Fixed calibration ranges for the CAM-04 motor transients, profile mill_lower_v1.

Recorded once from the played run of Nov 12 2026 (Broken Mill lower current, force 290, full health, trim 0, position
pinned in the band) and then frozen: a later run is judged against these numbers, never against its own. Change a range
only with a new measurement and a new profile name, written in the commit message.
Each entry: key -> (low, high) inclusive, seconds (accel, brake, reacq, decay) or units/s (steady).
"""
PROFILE = "mill_lower_v1"
TRANSIENT_RANGES = {
    "steady_vx": (285.0, 295.0),
    "steady_vz": (115.0, 125.0),
    "accel_t90": (0.45, 0.95),
    "brake_t10": (1.1, 2.1),
    "reacq_t90": (0.45, 0.95),
    "decay_open_t10": (1.1, 2.1),
    "decay_fall_t10": (0.1, 0.4),
}
