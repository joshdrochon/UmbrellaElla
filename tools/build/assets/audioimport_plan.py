"""Plan for audioimport_import.py: takes with a blind-critic pass on their bytes (or a person approval) that are not tracked placeholders. Run from the repo root."""
import sys,os,csv,json
sys.path.insert(0,"tools"); import audio_check as ac
rows=[r for r in csv.DictReader(open("pipeline/audio/sound-list.csv")) if r["tier"]!="cut"]
prov=ac.provenance_rows(ac.DEFAULT_PROV); ph=ac.placeholder_takes()
imp=[];skip={};missing=[]
for r in rows:
    sid=r["id"];d=f"Audio/Source/{sid}"
    fs=sorted(f for f in (os.listdir(d) if os.path.isdir(d) else []) if f.startswith(f"SW_{sid}_") and f.endswith(".wav"))
    if not fs: missing.append((sid,r["tier"])); continue
    rels=[f"{d}/{f}" for f in fs]
    rec=ac.critic_verdict(sid,rels)
    for rel in rels:
        origin=(prov.get(rel) or {}).get("origin") or ""
        if rel in ph: skip[rel]="placeholder"
        elif ac.APPROVED in origin: imp.append(rel)
        elif rec and rec.get("verdict")=="pass" and rec.get("style_pass"): imp.append(rel)
        else: skip[rel]="critic "+("fail" if rec else "no record")
os.makedirs("Saved", exist_ok=True); json.dump({"import": imp, "skip": skip, "missing": missing}, open("Saved/audioimport_plan.json", "w"), indent=1)
print(len(imp),len(skip),len(missing))
import collections;print(collections.Counter(skip.values()))
print([k for k,v in skip.items() if v!="placeholder"][:20])
print(missing)
