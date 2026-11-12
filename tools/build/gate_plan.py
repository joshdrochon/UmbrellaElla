#!/usr/bin/env python3
"""Which checks a merge needs (Josh, Nov 12: per-merge gates run only what relates to the change; the full Unreal and
Python suites run once before each packaged build). Prints shell assignments for tools/build/gate.sh.
Usage: gate_plan.py BASE [HEAD]"""
import subprocess, sys
base, head = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "HEAD")
files = subprocess.run(["git", "diff", "--name-only", base, head], capture_output=True, text=True).stdout.split()
# Source folder (Public/Private/<Dir> or Private/Tests/<Dir>) -> automation test prefix
PREFIX = {"Motor": "Move", "Umbrella": "Move", "Attack": "Move", "Input": "Move", "Move": "Move", "Shared": "Move",
          "Health": "Health", "Defense": "Health", "UI": "Health", "Projectile": "Projectile",
          "Owl": "Keeper", "Encounter": "Keeper", "Keeper": "Keeper", "Flow": "Flow", "Smoke": "Flow",
          "Arena": "Arena", "Field": "Field", "Feedback": "Feedback", "Level": "Level", "Hazard": "Level",
          "Enemy": "Enemy", "Trap": "Trap", "BrokenMill": "Trap", "Progression": "Progression",
          "Persistence": "Persistence", "Story": "Story", "DirectorsCut": "Story", "Settings": "Settings"}
SUB = {"UI/Menus": "Flow", "UI/Progression": "Progression", "UI/Story": "Story", "UI/Settings": "Settings"}
prefixes, full = set(), False
for f in files:
    if not f.startswith("Source/"):
        continue
    parts = f.split("/")
    if len(parts) < 5 or parts[1] != "UmbrellaElla":
        full = True; continue          # Build.cs, Target.cs, editor module
    d = parts[4] if parts[3] == "Tests" and len(parts) > 5 else parts[3]
    if parts[3] in ("Core", "Harness"):
        full = True; continue          # shared contracts: everything depends on them
    sub = "/".join(parts[3:5])
    p = SUB.get(sub) or PREFIX.get(d)
    if p:
        prefixes.add(p)
    else:
        full = True
any_ = lambda *pre: any(f.startswith(pre) for f in files)
ext = lambda *e: any(f.lower().endswith(e) for f in files)
src = any_("Source/")
print(f"SRC={int(src)}")
# The Flow world tests drive Start Game, defeat, retry and the win end to end, so every Source merge runs them too:
# areas talk through bus events, and a listener in one area can break another's path (story widgets broke Flow, Nov 12).
if prefixes:
    prefixes.add("Flow.World")
print(f"TESTS={'UmbrellaElla' if full else '+'.join('UmbrellaElla.' + p for p in sorted(prefixes))}")
print(f"MODULE={int(src)}")
print(f"MANIFEST={int(any_('docs/feature-manifest.json', 'docs/gdd/', 'Source/'))}")
print(f"FEEL={int(any_('pipeline/feel/', 'Source/UmbrellaElla/Public/Motor', 'Source/UmbrellaElla/Public/Umbrella', 'Source/UmbrellaElla/Public/Attack', 'Source/UmbrellaElla/Private/Motor', 'Source/UmbrellaElla/Private/Umbrella'))}")
print(f"ENCOUNTER={int(any_('pipeline/level/', 'Source/UmbrellaElla/Public/Owl', 'Source/UmbrellaElla/Private/Owl', 'Source/UmbrellaElla/Public/Encounter', 'Source/UmbrellaElla/Private/Encounter', 'Source/UmbrellaElla/Public/Enemy', 'Source/UmbrellaElla/Private/Enemy'))}")
print(f"UI={int(any_('Source/UmbrellaElla/Public/UI', 'Source/UmbrellaElla/Private/UI', 'Source/UmbrellaElla/Public/Flow', 'Source/UmbrellaElla/Private/Flow', 'Source/UmbrellaElla/Public/Settings', 'Source/UmbrellaElla/Private/Settings', 'Content/UmbrellaElla/UI', 'pipeline/ui/', 'Source/UmbrellaElla/Private/Core/UmbrellaGameMode'))}")
print(f"STORY={int(any_('pipeline/story/', 'Source/UmbrellaElla/Public/Story', 'Source/UmbrellaElla/Private/Story', 'Content/UmbrellaElla/UI/Story'))}")
print(f"ART={int(any_('Art/', 'Content/UmbrellaElla/Art', 'Content/UmbrellaElla/UI') and not all(f.startswith('Art/Source/') for f in files if f.startswith('Art/')))}")
print(f"AUDIO={int(any_('Audio/Source/'))}")
print(f"ASSETS={int(any_('Content/', 'Art/', 'Audio/', 'pipeline/art/provenance.csv'))}")
