"""Area split of the GDD SH1.0 Rule IDs (docs/feature-manifest.json). Run to print coverage: python3 docs/build/areas.py"""
import json, os
def r(p, a, b, skip=()):
    return [f"{p}-{i:02d}" for i in range(a, b + 1) if i not in skip]
AREAS = {
    "move": {"g1": r("MOVE", 4, 7) + ["MOVE-11"] + r("MOVE", 13, 15) + r("MOVE", 18, 22) + ["CORE-04", "CORE-05", "UMB-05", "COM-05", "COM-06", "COM-10"],
             "later": ["MOVE-12", "MOVE-16"] + r("COM", 7, 9) + ["COM-11"]},
    "keeper": {"g1": r("OWL", 6, 35) + ["FLOW-09"], "later": []},
    "health": {"g1": ["SURV-05", "SURV-07"] + r("FLOW", 30, 33), "later": []},
    "flow": {"g1": ["FLOW-02", "FLOW-04", "FLOW-34", "FLOW-35", "ART-04"],
             "later": ["FLOW-03"] + r("FLOW", 36, 41) + ["FLOW-43", "FLOW-44", "FLOW-45"] + r("MOVE", 8, 10) + ["MOVE-17"]},
    "arena": {"g1": ["CAM-03", "WIND-03", "CORE-06", "ART-03"],
              "later": r("CAM", 4, 8) + r("HAZ", 24, 41) + r("BG", 2, 6) + r("ART", 5, 10) + r("ANIM", 2, 10) + r("VFX", 2, 11)
                       + r("FLOW", 24, 28) + ["FLOW-47"]},
    # Added 14:10 (Josh: 8 workers). Director's Cut areas.
    "enemies": {"g1": [], "later": r("COM", 12, 18) + r("HAZ", 2, 23) + ["FLOW-46"]},
    "progression": {"g1": [], "later": ["SURV-06"] + r("FLOW", 5, 23, skip=(9,)) + ["FLOW-29", "FLOW-42", "FLOW-48"]},
    "story": {"g1": [], "later": r("NAR", 2, 8) + ["FLOW-49"]},
}
if __name__ == "__main__":
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    ids = [f["feature_id"] for f in json.load(open(os.path.join(root, "docs/feature-manifest.json")))["features"]]
    got = [i for a in AREAS.values() for k in ("g1", "later") for i in a[k]]
    print("missing:", sorted(set(ids) - set(got)) or "none"); print("unknown:", sorted(set(got) - set(ids)) or "none")
    print("dupes:", sorted({i for i in got if got.count(i) > 1}) or "none")
    for n, a in AREAS.items(): print(f"{n}: G1 {len(a['g1'])}  later {len(a['later'])}")
