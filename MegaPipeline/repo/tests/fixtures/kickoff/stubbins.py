"""Stub programs for the kickoff, connection and asset tests (no network, no credits, no real apps).

make(dir) writes one executable per tool into dir; each is a tiny Python program:
  claude, codex           --version and the login probes (`claude auth status`, `codex login status`)
  gh                      tests/fixtures/kickoff/fake_gh.py
  git-lfs                 `git lfs version`
  gimp-console, gimpcli   --version; `gimpcli clean IN OUT`: the corner colour becomes transparent
  aseprite                --version; `-b F1 F2 ... --sheet OUT --data JSON`: a horizontal strip
  blender                 --version; `-- --job JOB` writes each frame the job names (an ink blob with a gold bar that
                          moves per frame; STUB_BLENDER_ART=SHEET.png:WxH draws the frames from that sheet's cells instead),
                          the .blend and the BLENDER_RENDER line; `-- --out PNG` writes one PNG
  sox, obs-cmd, 7z, butler   version/info probes (butler status answers when BUTLER_TARGET is set)
  ffmpeg                  -version; a .wav to .wav step copies the audio; a video output is a JSON stand-in
                          {"duration", "width", "height", "audio"} (-t sets the duration)
  ffprobe                 reads that stand-in and prints ffprobe JSON
  gimp-mcp, aseprite-mcp, blender-mcp   answer one MCP initialize request on stdin
http_stub.py (next to this file) stands in for the vendor APIs.
"""
import os
import sys

FIX = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(FIX))), "tools")

PROGRAMS = {
    "claude": "a = sys.argv[1:]\nprint('2.1.0 (Claude Code)' if a == ['--version'] else 'Logged in (stub)')",
    "codex": "a = sys.argv[1:]\nprint('codex-cli 0.167.0' if a == ['--version'] else 'Logged in using ChatGPT')",
    "git-lfs": "print('git-lfs/3.8.0 (stub)')",
    "gimp-console": "print('GNU Image Manipulation Program version 3.0.4')",
    "blender": """a = sys.argv[1:]
if os.environ.get('BLENDER_STUB_LOG'):
    import json
    with open(os.environ['BLENDER_STUB_LOG'], 'a') as fh:
        fh.write(json.dumps(a) + chr(10))
if '--job' in a:
    sys.path.insert(0, TOOLS)
    import json, png
    j = json.load(open(a[a.index('--job') + 1]))
    w, h = j['frame_size']
    px, py = j['pivot_px']
    art = os.environ.get('STUB_BLENDER_ART')   # 'SHEET.png:WxH': frames drawn from a finished sheet's cells
    if art:
        src, cell = art.rsplit(':', 1)
        cw, ch = (int(v) for v in cell.split('x'))
        sw, sh, srows = png.read_png(src)
        cols = sw // cw
    for i, f in enumerate(j['frames']):
        rows = [[(0, 0, 0, 0)] * w for _ in range(h)]
        if art:   # cell i of the sheet's first row, nearest-neighbour scaled to the frame
            cx = (i % cols) * cw
            for y in range(h):
                r = srows[y * ch // h]
                rows[y] = [r[cx + x * cw // w] for x in range(w)]
        for y in range(h) if not art else ():
            for x in range(w):
                dx, dy = (x - px) / (w * 0.2), (y - py) / (h * 0.3)
                if dx * dx + dy * dy <= 1.0:
                    v = 18 + (x * 7 + y * 13 + i) % 9
                    rows[y][x] = (v, v - 2, v - 4, 255)
                elif abs(y - (py - h * 0.25 + i * 3)) < 3 and px < x < px + w * 0.3:
                    rows[y][x] = (233, 176, 74, 255)
        os.makedirs(os.path.dirname(f) or '.', exist_ok=True)
        png.write_png(f, w, h, rows)
    open(j['blend'], 'wb').write(b'BLENDER-stub')
    print('BLENDER_RENDER version=4.5.0 frames=%d blend=%s freestyle=on compositor=off engine=BLENDER_EEVEE_NEXT'
          % (len(j['frames']), j['blend']))
elif '--out' in a:
    sys.path.insert(0, TOOLS)
    import png
    png.write_png(a[a.index('--out') + 1], 8, 8, [[(20, 18, 16, 255)] * 8 for _ in range(8)])
else:
    print('Blender 4.5.0')""",
    "sox": "print('sox: SoX v14.4.2')",
    "obs-cmd": "print('obs-websocket 5.5 (stub)')",
    "7z": "print('7-Zip 24.08 (stub)')",
    "butler": ("a = sys.argv[1:]\nif a[:1] == ['status'] and not os.environ.get('BUTLER_TARGET'):\n    sys.exit(1)\n"
               "print('v15.24.0' if a == ['version'] else 'logged in')"),
    "gimpcli": """a = sys.argv[1:]
if a == ['--version']:
    print('gimpcli 1.0 (stub)'); sys.exit(0)
sys.path.insert(0, TOOLS)
import png
w, h, rows = png.read_png(a[1])
bg = rows[0][0][:3]
out = [[(0, 0, 0, 0) if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) <= 40 else (r, g, b, 255) for r, g, b, _ in row]
       for row in rows]
png.write_png(a[2], w, h, out)""",
    "aseprite": """a = sys.argv[1:]
if a == ['--version']:
    print('Aseprite 1.3.14'); sys.exit(0)
sys.path.insert(0, TOOLS)
import json, png
frames = [x for x in a[1:a.index('--sheet')]]
out = a[a.index('--sheet') + 1]
strips = [png.read_png(f) for f in frames]
w, h = strips[0][0], strips[0][1]
rows = [sum((s[2][y] for s in strips), []) for y in range(h)]
png.write_png(out, w * len(frames), h, rows)
json.dump({'frames': [{'filename': f} for f in frames]}, open(a[a.index('--data') + 1], 'w'))""",
    "ffmpeg": """import json, shutil
a = sys.argv[1:]
if a == ['-version']:
    print('ffmpeg version 8.1 (stub)'); sys.exit(0)
out = a[-1]
src = a[a.index('-i') + 1] if '-i' in a else None
if out.endswith('.wav'):
    shutil.copy(src, out)
else:
    dur = float(a[a.index('-t') + 1]) if '-t' in a else 50.0
    scaled = any('scale=1920:1080' in x for x in a)
    w, h = (1920, 1080) if scaled else (1280, 720)
    json.dump({'duration': dur, 'width': w, 'height': h, 'audio': True}, open(out, 'w'))""",
    "ffprobe": """import json
meta = json.load(open(sys.argv[-1]))
streams = [{'codec_type': 'video', 'width': meta['width'], 'height': meta['height']}]
if meta.get('audio'):
    streams.append({'codec_type': 'audio'})
print(json.dumps({'format': {'duration': str(meta['duration'])}, 'streams': streams}))""",
}
MCP = """line = sys.stdin.readline()
import json
req = json.loads(line)
print(json.dumps({'jsonrpc': '2.0', 'id': req['id'], 'result': {'serverInfo': {'name': os.path.basename(sys.argv[0])}}}))"""
for _n in ("gimp-mcp", "aseprite-mcp", "blender-mcp"):
    PROGRAMS[_n] = MCP


WINDOWS = os.name == "nt"


def exe(d, name):
    """The path a stub `name` in `d` runs from: `name` here, `name.cmd` on Windows (it cannot run a #! file)."""
    return os.path.join(d, name + (".cmd" if WINDOWS else ""))


def script(path, body, python=sys.executable):
    """Write a runnable Python stub at `path`; returns the path to run (path.cmd beside path.py on Windows)."""
    if not WINDOWS:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"#!{python}\n{body}\n")
        os.chmod(path, 0o755)
        return path
    with open(path + ".py", "w", encoding="utf-8") as fh:
        fh.write(body + "\n")
    return wrapper(path, python, path + ".py")


def wrapper(path, *argv):
    """POSIX: a sh script that execs argv. Windows: path.cmd that runs argv with the caller's arguments."""
    if WINDOWS:
        with open(path + ".cmd", "w", encoding="utf-8", newline="\r\n") as fh:
            fh.write("@" + " ".join(f'"{a}"' for a in argv) + " %*\n")
        return path + ".cmd"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\nexec " + " ".join(f'"{a}"' for a in argv) + ' "$@"\n')
    os.chmod(path, 0o755)
    return path


def make(d, skip=()):
    os.makedirs(d, exist_ok=True)
    for name, body in PROGRAMS.items():
        if name in skip:
            continue
        script(os.path.join(d, name), f"import os, sys\nTOOLS = {TOOLS!r}\n{body}")
    if "gh" not in skip:
        wrapper(os.path.join(d, "gh"), sys.executable, os.path.join(FIX, "fake_gh.py"))
    return d


def add_git(d):
    """A PATH value that finds the stubs in `d` and the host's real git, nothing else from the host on Mac and
    Linux (a link in d). Windows: git's own folder joins the PATH (a linked git.exe cannot find its install), and
    the Windows system folders every Windows PATH has (System32, Windows PowerShell), so the PowerShell probe runs."""
    import shutil
    git = shutil.which("git")
    if WINDOWS:
        sysroot = os.environ.get("SystemRoot", r"C:\Windows")
        system = [os.path.join(sysroot, "System32"), os.path.join(sysroot, "System32", "WindowsPowerShell", "v1.0")]
        return os.pathsep.join([d, os.path.dirname(git)] + system)
    os.symlink(git, os.path.join(d, "git"))
    return d


def system_path(d, hide=()):
    """A folder of links to the host's /usr/bin and /bin programs minus `hide`, for a PATH that must not find a
    program. Linux runners install git-lfs, 7z and gh in /usr/bin, so "/usr/bin:/bin" alone does not hide them.
    Windows has no /usr/bin: the host PATH minus every folder that holds a hidden program (any PATHEXT)."""
    if WINDOWS:
        exts = [""] + [e.lower() for e in os.environ.get("PATHEXT", ".EXE;.CMD;.BAT").split(";") if e]
        keep = [p for p in os.environ.get("PATH", "").split(os.pathsep)
                if p and not any(os.path.isfile(os.path.join(p, n + e)) for n in hide for e in exts)]
        return os.pathsep.join(keep)
    os.makedirs(d, exist_ok=True)
    for src in ("/usr/bin", "/bin"):
        if not os.path.isdir(src):
            continue
        for name in os.listdir(src):
            dst = os.path.join(d, name)
            if name in hide or os.path.lexists(dst):
                continue
            full = os.path.join(src, name)
            if os.path.isfile(full) and os.access(full, os.X_OK):
                os.symlink(full, dst)
    return d


def tool_env(d):
    """The assetgen env overrides that point every tool at its stub."""
    return {"GIMPCLI": exe(d, "gimpcli"), "GIMP": exe(d, "gimp-console"), "ASEPRITE": exe(d, "aseprite"),
            "BLENDER": exe(d, "blender"), "FFMPEG": exe(d, "ffmpeg"), "SOX": exe(d, "sox"), "OBS_CMD": exe(d, "obs-cmd"),
            "SEVENZIP": exe(d, "7z"), "BUTLER": exe(d, "butler")}
