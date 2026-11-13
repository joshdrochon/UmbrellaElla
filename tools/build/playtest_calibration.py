"""Fixed calibration ranges for the CAM-04 motor transients (Broken Mill lower current, force 290, full health, trim 0,
position pinned in the band). Profiles are versioned (GDD: "version the profile"); the checker uses PROFILE.
A range is frozen once recorded: a later run is judged against it, never against its own numbers. Change a range only
with a new measurement and a new profile name, written in the commit message.
Each entry: key -> (low, high) inclusive, seconds (accel, brake, reacq, decay) or units/s (steady).

mill_lower_v1  History. Recorded Nov 12 2026 on the pre-windfix motor (no restoring field, steady_vz +120). Superseded.
mill_lower_v2  Recorded once Nov 12 2026 from run-2026-11-12g.log (commit ac4403d2, windfix motor, restoring field centred
               on z 230). Measured: steady_vx 290.86, steady_vz -54.00, accel_t90 0.43, brake_t10 1.55, reacq_t90 0.42,
               decay_open_t10 1.57, decay_fall_t10 0.20. Ranges use the same margins v1 used around its measure
               (+-5 units/s, +-0.25 s on sub-second times, +-0.5 s on 1.5 s times, 0.1-0.4 s for the fall decay).
               Gate before recording: all 6 played rides left the right edge with exit root z 217.56-259.00, inside
               HAZ-06 lower eligibility z 210-330 and HAZ-08 required underpass root envelope z 185-285.
Frozen.
"""
PROFILES = {
    "mill_lower_v1": {
        "steady_vx": (285.0, 295.0),
        "steady_vz": (115.0, 125.0),
        "accel_t90": (0.45, 0.95),
        "brake_t10": (1.1, 2.1),
        "reacq_t90": (0.45, 0.95),
        "decay_open_t10": (1.1, 2.1),
        "decay_fall_t10": (0.1, 0.4),
    },
    "mill_lower_v2": {
        "steady_vx": (285.0, 295.0),
        "steady_vz": (-59.0, -49.0),
        "accel_t90": (0.18, 0.68),
        "brake_t10": (1.05, 2.05),
        "reacq_t90": (0.17, 0.67),
        "decay_open_t10": (1.07, 2.07),
        "decay_fall_t10": (0.1, 0.4),
    },
}
PROFILE = "mill_lower_v2"
TRANSIENT_RANGES = PROFILES[PROFILE]
