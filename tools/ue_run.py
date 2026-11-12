#!/usr/bin/env python3
"""Shared helper for tools/ue/*.sh and *.ps1, so the Mac and Windows scripts behave the same.
Stdlib only. macOS has no `timeout` command, and Windows PowerShell 5.1 has no clean one either.

Subcommands:
  run --timeout S --log FILE -- cmd ...   run cmd, copy its output to the console and FILE, kill it
                                          after S seconds (exit 124). Otherwise exit with cmd's code.
  alive --seconds S --log FILE -- cmd ... no-log smoke (Shipping, only if D-new-smoke picks it): pass when
      [--max-boot-s B]                    cmd is still running after S s, then closes on WM_CLOSE
                                          (SIGTERM on Mac) with exit code 0 [VERIFY on 5.8.4]. --max-boot-s: the
                                          first visible window shows within B s (prints boot_s=; Windows only)
  workbench-check                         the submission target Source/UmbrellaElla.Target.cs sets
                                          UMBRELLAELLA_WORKBENCH=0 (comments ignored) and nothing else under Source/
                                          or Plugins/ sets or #defines it (final-9 B H6, M4)
                                          (D-new-workbench-debug; package scripts run it unless -Workbench)
  clean-tree [--allow-dirty]              exit 1 if `git status --porcelain` shows any change
                                          (ignored files such as Saved/ and Packaged/ don't count)
  build-info --out DIR --config CFG       write DIR/BUILD_INFO.txt (commit, date, config, dirty, and with
      [--target T] [--workbench 0|1]      --target/--workbench the target and its UMBRELLAELLA_WORKBENCH value) and the
      [--commit SHA]                      (--commit: the commit the package script stamped at build start and passed
                                          to the compile as UMBRELLAELLA_BUILD_COMMIT; final-9 B H5) and the
                                          same file into each folder directly under DIR (the platform
                                          folder UAT archives, e.g. Packaged/Windows [VERIFY name on 5.8.4]);
                                          copy pipeline/submission/README.txt and LICENSE.txt next to each
                                          (submission_check.py zip needs both beside the exe)
  smoke-log LOG... --exit-code N          pass only if N == 0, a LOG has a SMOKE_OK line (contract below),
      [--expect-map M] [--expect-commit S]  map and commit match when given (the scripts pass the commit from
      [--min-fps F] [--max-frame-ms MS]     the package's BUILD_INFO.txt and $SMOKE_MAP), fps >= F (default 55),
      [--expect-res WxH] [--expect-win W]   worst_ms <= MS (default 33), input=ok (input=none only on a
      [--min-text-px N] [--no-input-check] [--no-gamepad-check]  --no-player-maps map), res=/win=/textpx=/section= match when asked,
      [--expect-section S] [--restart-cycles N]  N SMOKE_CYCLE lines with no drift when asked, and zero
      [--no-player-maps L_Title] [--allow F]     lines with any SMOKE_BAD or SMOKE_BAD_BROAD pattern below
                                          (--no-player-maps default: pipeline/qa/no-player-maps.txt, which map
                                          cards extend; GameDefaultMap is never exempt; final-9 A H2)
      [--max-load-ms MS] [--expect-workbench 0|1]  (a BROAD line matching an --allow regex does not count), and
                                          load_ms <= MS (default 10000) on SMOKE_OK and each SMOKE_CYCLE. 0 = off.
                                          --expect-workbench: SMOKE_OK workbench= must match; with 0, any
                                          WORKBENCH_MARKERS line fails (smoke scripts pass BUILD_INFO's workbench=)
      [--expect-aspect 16:9] [--aspect-tol T]  view=/aspect= on SMOKE_OK: the gameplay view inside the bars is 16:9
                                          within T (default 0.01), aspect= agrees with view=, and the view fits the
                                          window and fills it on one axis (pipeline/unreal-rules.md, Display)
      [--expect-debugdraw 0|1]            debugdraw= on SMOKE_OK (default 0: every debug draw is off by default)
      [--shot PNG]                        the SMOKE_SHOT screenshot the scripts asked for (-SmokeShot=): art_check.py,
                                          screen_check.py and, on a map with a player, art_judge.py scene (the key-art
                                          composition, pipeline/art/references.json; refs outside the repo under
                                          ART_REFS_ROOT) run on it and any FAIL fails the smoke. Art bootstrap
                                          (tied to repo state, ends by itself): until card 0.10b adds
                                          Content/UmbrellaElla/Art/Anchors/ both still run and print, but do not fail
  launch-record --zip ZIP --exe EXE LOG...  after a passing smoke of the unzipped gate zip (smoke.sh / smoke.ps1
                                          with SMOKE_ZIP=<zip>; EXE must be a file of ZIP, same name and sha256,
                                          final-10 B H2): append `LAUNCH <zip sha256> | ... exe=<member>
                                          exe_sha256=<h> ... | SMOKE_EFFECTIVE at=start ...` to
                                          the record. check_card.py --gate-record reads it for "re-downloaded and
                                          launched: yes" (platform=Windows) and the G4 bake tie (final-9 B H4, H5)
  crash-list DIR... --out FILE            write every */Saved/Crashes/* entry under the DIRs to FILE
  crash-check --before FILE DIR...        exit 1 if a crash folder exists now that was not in FILE; exit 2 if
                                          none of the DIRs exists (a wrong crash path is not a pass)
  state-list --out FILE / state-check --before FILE   hash Saved/SaveGames/** and Saved/Config/*/
                                          GameUserSettings.ini under --root; state-check exits 1 on any change
  maps                                    print GameDefaultMap, then each +MapsToCook map (Config/*.ini)
  daily --shell sh|ps1                    the daily build as one graph: clean-tree, build (non-unity), test, alone (each
                                          newly merged test-map test run alone), shuffle (merged tests again in a
                                          seeded random order), validate (DataValidation), package (cook warnings
                                          may not rise), smoke (every map;
                                          GameDefaultMap $SMOKE_REPEAT times), display (each resolution that fits
                                          the monitor), settings (boot with a garbage and an old
                                          GameUserSettings.ini), client-test, shipping-alive, workbench
                                          (the tester package into Packaged-Workbench; a failure fails the line).
                                          Stops at the first failure; prints and appends one record line.
                                          Day-1 bootstrap (final-8 A H7), tied to repo state so it ends by itself,
                                          like check_pr's SMOKE_BOOTSTRAP: until card 0.5 adds
                                          Source/UmbrellaElla/Private/Tests/Meta/, test runs with --bootstrap
                                          (placeholder only); until card 0.6's smoke hook exists, smoke is one
                                          alive run (SMOKE_MODE=alive) and display and settings do not run. Each
                                          is listed in Not checked; a gate record never accepts either
  merge-check --since REF [--require-client]  exit 1 if a first-parent commit in REF..HEAD has no DAILY record
                                          line with package=PASS, smoke=PASS and no FAIL step (dirty runs
                                          don't count); --require-client (from G2) also needs client-test=PASS
                                          on each commit whose own test map has the Flow row (TitleToPlayToSurvived)
                                          merged
  verify-tags [--root R]                  list every open VERIFY tag in tools/ue/* scripts and tools/*.py;
                                          exit 1 while any is left (card 0.6 is done at 0)
  stress-check [--commit REF]             exit 1 unless the record has a STRESS line for REF (default HEAD)
                                          with every hand-check field pass (format: tools/ue/daily-checklist.md)
  playthrough-check / shipping-check [--commit REF]   same for the PLAYTHROUGH line (each phase preset in
                                          pipeline/level/encounter.json, none for the one GDD 1.3 base phase; survived,
                                          die-restart, quit-play, quit-title, quit-pause all pass; --gate G1 needs
                                          survived, fail-retry, fail-bottom and quit-play, G2 adds both menu quits, the rest pass or n/a)
                                          and the SHIPPING line
                                          (boot_s <= 20, quit rc=0)
Exit 0 = ok, 1 = check failed, 2 = usage/input error, 124 = timeout.

Smoke hook contract (card 0.6 builds it; every switch and field is [VERIFY] until a real package prints it):
  switches  -SmokeQuitAfter=15  -SmokeMap=/Game/...  -SmokeSection=S5  -SmokeRestartCycles=5  -ResX/-ResY
  SMOKE_OK  map=<short name> fps=<1% low over the window> worst_ms=<worst frame ms> commit=<sha>
            input=ok|none input_vz=<Z cm/s while IA_Attack is held>
            gamepad=ok|none gp_vx=<X cm/s, left stick held right> gp_attack_vz=<Z cm/s, right trigger held>
            gp_shield_vz=<Z cm/s, left trigger held; none until the MVP 10 shield merges> res=<WxH of the live viewport> win=windowed|fullscreen textpx=<smallest visible
            UMG text height in px> load_ms=<ms from map load start to the first gameplay frame> [section=<S>]
            workbench=<UMBRELLAELLA_WORKBENCH as compiled, 0|1>
            view=<WxH of the gameplay view: the view target camera's constrained view rect inside the letterbox or
            pillarbox bars, measured from the live viewport, never computed from the camera's AspectRatio>
            aspect=<view W/H, 3 decimals> debugdraw=<1 if any debug draw is on: ue.Debug, a collision or hitbox draw,
            on-screen debug text; 0 in a default launch>
  SMOKE_SHOT at_s=<s> w=<W> h=<H>   with -SmokeShot=<png> the hook writes one screenshot of the whole window (bars
            and UI included) at a fixed moment, 5 s after the first gameplay frame, before the input check, and logs this
            line. smoke-log runs art_check.py and screen_check.py on that file (--shot). Card 0.6 builds it
            [VERIFY a full-window screenshot with UI and bars on 5.8.4]
  -SmokeNoAspectLock / -SmokeDebugDraw   non-Shipping proof switches (SMOKE_FORCE_NO_ASPECT=1 / SMOKE_FORCE_DEBUGDRAW=1):
            the first turns the view target camera's aspect constraint off, the second turns ue.Debug on; a smoke at
            2560x1080 must then FAIL on aspect, the second on debugdraw= and on the screenshot
  SMOKE_EFFECTIVE at=start|end [outcome=survived|fail|quit] commit=<UMBRELLAELLA_BUILD_COMMIT as compiled>
            workbench=<as compiled> platform=<Windows|Mac> manifest=<manifest_version the harness flag table was made
            from> <field>=<value> ...   in the LogUmbrellaElla category, at the start of its log line.
            at=start once at the first gameplay frame; at=end when the run ends: at the Survived or fail screen
            (each restart cycle's fail screen too), else at the -SmokeQuitAfter quit (outcome=quit). The same read
            both times, so a value written after startup shows (final-10 B H3). The hook reads tuning where gameplay
            reads it (pipeline/unreal/gameplay-code.md): `GetDefault<UUmbrellaTuning>()`, on every map, with or
            without a player (final-10 A H2, A M12, B H4). It needs no edit when a card marks a key (final-10 A H1):
              params  every reflected field of every struct UPROPERTY of UUmbrellaTuning (TFieldIterator over the
                      class, then over each struct), logged as `<Struct>.<Field>=<value>` with the struct name as
                      reflection gives it (no F prefix), e.g. UmbrellaFlightTuning.AscentSpeed=300. `bake_preset.py`
                      maps each one to its `// bake:` key from the marked line; an unmarked field is not checked
              flags   `<ID>.enabled=1|0` for each entry of the flag table, by UHarnessSubsystem::ForEachFlag on the
                      live harness subsystem (the seam card 0.3 makes and card 0.27 fills; the EFeatureId name with
                      `_` as `-`); manifest= is its ManifestVersion() (final-11 A H1)
            Values in manifest units (a `%` key is the percent). Never from the header text or BUILD_INFO. Keys
            or fields given twice fail. UPROPERTY meta tags are editor-only data, so the packaged hook cannot read
            a `BakeKey` meta: the field path is the identity [VERIFY WITH_METADATA is 0 in a 5.8.4 Development game].
            commit= and workbench= are compiled in: the package script stamps the commit at build start and every
            Target.cs passes it as UMBRELLAELLA_BUILD_COMMIT (pipeline/unreal-rules.md). `bake_preset.py
            effective` compares every line with pipeline/qa/baked.json and the manifest at the commit the game was
            built from; check_pr, the daily smoke and the G4 tie run it.
  title     with -SmokeQuitAfter the hook passes the title screen through the title's own Play path
            (the function the Play button calls, card 0.21) before the input check; it logs
            `SMOKE_TITLE skipped=<function>` (final-9 A H1). Before card 0.21 there is no title.
  WORKBENCH_ON debug=<0|1>   logged once at startup by a build with the workbench compiled in (card 0.27);
            a submission package never prints it, nor LogWorkbench or TestPresetLoaded lines.
  input=ok  the hook injected input through Enhanced Input and saw the result. GDD 1.3: with nothing held the
            umbrella is UP_OPEN and rises, so a rise proves nothing. The hook holds IA_Attack (the injected
            action, never a direct state set), and within 0.5 s the umbrella falls; it logs that Z velocity as
            input_vz=<cm/s>, which must be below 0, then releases ATTACK. It reads no gameplay state name, so MVP 2
            needs no hook edit (final-11 A H1)
            (final-8 dry run A H2). input=none is accepted only on a map with no player (--no-player-maps,
            default: the maps listed in pipeline/qa/no-player-maps.txt; never GameDefaultMap).
  gamepad=ok  card 0.6e: the hook feeds raw gamepad KEYS (Gamepad_LeftX=+1, Gamepad_RightTriggerAxis,
            Gamepad_LeftTriggerAxis) into the local player's input as a gamepad device, never the actions, so a
            missing controller mapping in the IMC or a wrong input mode fails (a controller that did not work in a
            packaged test build). Each held 0.5 s, then released: gp_vx above 0 (direct steering, the GDD default),
            gp_attack_vz and gp_shield_vz below 0. Required with input=ok on every map with a player
            (SMOKE_REQUIRE_GAMEPAD=0 / --no-gamepad-check only while the test-map QA-GP row is planned; past G1 it is
            a P1). [VERIFY on 5.8.4: UEnhancedPlayerInput::InputKey with FInputKeyParams for a gamepad device]
  SMOKE_CYCLE n=<i> actors=<count> health=<h> load_ms=<restart load ms>   one line after each scripted
            die -> restart cycle.
"""
import argparse
import datetime
import glob
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMOKE_BAD = ["Ensure condition failed", "Fatal error", "Accessed None", "Assertion failed",
             "=== Critical error", "Unhandled Exception", "LogOutputDevice: Error"]
# Any Error: line in any Log category, and any failed asset load. A line here may be allowed by a regex in
# tools/ue/smoke-allow.txt, and each allow line must name a row in docs/decisions.md. SMOKE_BAD is never allowed.
SMOKE_BAD_BROAD = {"Error:": re.compile(r"\bError:"), "Failed to load": re.compile(r"Failed to load", re.I)}
ALLOW_FILE = os.path.join(ROOT, "tools", "ue", "smoke-allow.txt")
MIN_FPS = 55
MAX_FRAME_MS = 33
NO_PLAYER_MAPS = "L_Title"   # fallback when pipeline/qa/no-player-maps.txt is missing
NO_PLAYER_FILE = os.path.join("pipeline", "qa", "no-player-maps.txt")
MIN_TEXT_PX = 18
FALLBACK_RES = "1920x1080"   # the resolution a missing or garbage GameUserSettings.ini falls back to (team, 11 Nov)
MAX_LOAD_MS = 10000
# Daily display runs: WxH:windowed|fullscreen. Override with SMOKE_DISPLAY_MODES. [VERIFY -ResX/-ResY on 5.8.4]
# 1280x800 (16:10 laptop) and 2560x1080 (ultrawide) catch cut-off UI that 16:9 alone hides.
DISPLAY_MODES = ("1280x720:windowed,1920x1080:fullscreen,3840x2160:fullscreen,1280x800:windowed,"
                 "2560x1080:windowed")
TIMEOUT_RC = 124
# Lines only a build with the workbench compiled in can print (D-new-workbench-debug).
WORKBENCH_MARKERS = re.compile(r"\bWORKBENCH_ON\b|\bLogWorkbench\b|\bTestPresetLoaded\b")
WORKBENCH_DEFINE = "UMBRELLAELLA_WORKBENCH"
SUBMIT_TARGET = "UmbrellaElla"


# Seconds run() keeps reading after the command exits. The Mac editor forks UnrealTraceServer (TraceAuxiliary.cpp,
# `fork --sponsor=<pid>`), which keeps the inherited stdout open and only exits once its sponsor is reaped; reading to
# EOF before wait() deadlocked every editor run (card 0.3 dry run, UE 5.8.4 on macOS 15). RUN_DRAIN_S overrides.
DRAIN_S = 5.0


def run(cmd, timeout, log, env=None):
    os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
    drain = float(os.environ.get("RUN_DRAIN_S", DRAIN_S))
    with open(log, "ab") as fh:
        # Own process group, so a timeout also kills the children UBT/UAT start.
        extra = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, **extra)
        lock, closed = threading.Lock(), []

        def pump():
            # Reads until EOF; a daemon thread, so a pipe held open by a forked background server never blocks run().
            out = getattr(sys.stdout, "buffer", None)
            for chunk in iter(proc.stdout.readline, b""):
                with lock:
                    if closed:
                        return
                    if out is not None:
                        out.write(chunk)
                    else:
                        sys.stdout.write(chunk.decode("utf-8", "replace"))
                    sys.stdout.flush()
                    fh.write(chunk)

        reader = threading.Thread(target=pump, daemon=True)
        reader.start()

        def kill():
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    proc.kill()

        timed_out = False
        try:
            rc = proc.wait(timeout if timeout > 0 else None)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill()
            rc = proc.wait()
        # The command has exited and is reaped; read what is left, but stop once only a background process that
        # inherited the pipe still holds it open.
        reader.join(drain)
        with lock:
            closed.append(True)
            held = reader.is_alive()
            if held:
                msg = (f"note: output pipe still held open {drain:g}s after the command exited (a background "
                       "process it started, e.g. UnrealTraceServer); stopped reading\n")
                fh.write(msg.encode())
                print(msg, end="")
            if timed_out:
                msg = f"TIMEOUT: killed after {timeout}s: {' '.join(cmd)}\n"
                fh.write(msg.encode())
                print(msg, end="")
            fh.flush()
        if not held:
            proc.stdout.close()
        return TIMEOUT_RC if timed_out else rc


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def dirty_lines(root):
    p = git(root, "status", "--porcelain")
    if p.returncode != 0:
        raise OSError(p.stderr.strip() or "git status failed")
    return [ln for ln in p.stdout.splitlines() if ln.strip()]


def clean_tree(root, allow_dirty):
    lines = dirty_lines(root)
    if not lines:
        return 0
    if allow_dirty:
        print(f"WARNING: {len(lines)} uncommitted change(s); continuing because of --allow-dirty. BUILD_INFO says dirty=yes.")
        return 0
    print(f"FAIL: git tree has {len(lines)} uncommitted change(s). Commit or stash, or pass --allow-dirty:")
    for ln in lines[:20]:
        print("  " + ln)
    return 1


def build_info(root, out, config, now=None, target=None, workbench=None, commit=None):
    """commit: the commit stamped at build start (final-9 B H5). Without it, HEAD now."""
    commit = commit or git(root, "rev-parse", "HEAD").stdout.strip() or "unknown"
    dirty = "yes" if dirty_lines(root) else "no"
    when = (now or datetime.datetime.now(datetime.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = f"commit={commit}\ndate={when}\nconfig={config}\ndirty={dirty}\n"
    if target:
        text += f"target={target}\n"
    if workbench is not None:
        text += f"workbench={workbench}\n"
    if not os.path.isdir(out):
        raise OSError(f"package folder not found: {out}")
    targets = [out] + [os.path.join(out, d) for d in sorted(os.listdir(out)) if os.path.isdir(os.path.join(out, d))]
    extras = [os.path.join(root, "pipeline", "submission", n) for n in ("README.txt", "LICENSE.txt")]
    for e in extras:
        if not os.path.isfile(e):
            print(f"WARN: {os.path.relpath(e, root)} missing; the zip check will fail without it")
    for t in targets:
        with open(os.path.join(t, "BUILD_INFO.txt"), "w", encoding="utf-8") as fh:
            fh.write(text)
        for e in extras:
            if os.path.isfile(e):
                shutil.copyfile(e, os.path.join(t, os.path.basename(e)))
    print(f"BUILD_INFO.txt written to {len(targets)} folder(s): {text.strip().replace(chr(10), ' ')}")
    return text


WORKBENCH_DEFINED = re.compile(r"^\s*#\s*(?:(?:el)?if(?:n?def)\s+UMBRELLAELLA_WORKBENCH\b"
                               r"|(?:el)?if\b.*\bdefined\s*\(?\s*UMBRELLAELLA_WORKBENCH\b)")


WORKBENCH_ANY_IF = re.compile(r"^\s*#\s*(?:el)?if\b.*\bUMBRELLAELLA_WORKBENCH\b")
WORKBENCH_EXACT_IF = re.compile(r"^\s*#\s*(?:el)?if\s+!?\s*UMBRELLAELLA_WORKBENCH\s*(?://.*|/\*.*)?$")


def workbench_check(root):
    """Problems with the compile switch: the submission target sets UMBRELLAELLA_WORKBENCH=0, and it is set
    nowhere else but the Target.cs files (a Build.cs or #define would win over the target). [VERIFY on 5.8.4]"""
    src = os.path.join(root, "Source")
    target = os.path.join(src, SUBMIT_TARGET + ".Target.cs")
    out = []
    if not os.path.isfile(target):
        return [f"Source/{SUBMIT_TARGET}.Target.cs not found: the submission target must set {WORKBENCH_DEFINE}=0"]
    with open(target, encoding="utf-8", errors="replace") as fh:
        t = strip_comments(fh.read())
    vals = re.findall(WORKBENCH_DEFINE + r"\s*=\s*(\w+)", t)
    # final-9 B M4: only the literal define counts; a comment or a built string ("=" + (b ? "1" : "0")) is not =0
    lit = re.findall(r'ProjectDefinitions\.Add\(\s*"' + WORKBENCH_DEFINE + r'=0"\s*\)\s*;', t)
    if vals != ["0"] or len(lit) != 1 or t.count(WORKBENCH_DEFINE) != 1:
        out.append(f"Source/{SUBMIT_TARGET}.Target.cs sets {WORKBENCH_DEFINE}={','.join(vals) or '<nothing>'}; "
                   f"the submission target needs exactly one `ProjectDefinitions.Add(\"{WORKBENCH_DEFINE}=0\");` "
                   "and no other mention of it outside comments")
    # Final-10 A M10: the hook logs UMBRELLAELLA_BUILD_COMMIT, and every target compiles the hook (the editor target
    # for build.sh and test.sh, the -Workbench tester package), so once one Target.cs defines it, each one does.
    tcs = sorted(f for f in os.listdir(src) if f.endswith(".Target.cs"))
    with_commit = []
    for f in tcs:
        with open(os.path.join(src, f), encoding="utf-8", errors="replace") as fh:
            if re.search(r'ProjectDefinitions\.Add\(\s*"UMBRELLAELLA_BUILD_COMMIT=', strip_comments(fh.read())):
                with_commit.append(f)
    if with_commit:
        for f in tcs:
            if f not in with_commit:
                out.append(f"Source/{f} does not define UMBRELLAELLA_BUILD_COMMIT, but {with_commit[0]} does: every "
                           "target compiles the smoke hook, so each Target.cs passes the stamped commit (the line in "
                           "pipeline/unreal-rules.md, Smoke hook contract)")
    walk = [os.path.join(src, x) for x in ("",)] + [os.path.join(root, "Plugins")]   # final-9 B H6: plugins compile in
    for d, _, files in (w for base in walk for w in os.walk(base)):
        for f in files:
            p = os.path.join(d, f)
            if (f.endswith(".Target.cs") and os.path.dirname(p) == src) or \
                    not f.endswith((".cs", ".h", ".hpp", ".cpp", ".inl")):
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                body = strip_comments(fh.read())
            if re.search(r"#\s*define\s+" + WORKBENCH_DEFINE + r"\b|" + WORKBENCH_DEFINE + r"\s*=", body):
                out.append(f"{os.path.relpath(p, root)} sets {WORKBENCH_DEFINE}; only the Target.cs files may")
            # Dry run B H8: the submission target defines the macro as 0, so a defined() test is always true
            # and compiles the workbench into the submission. Code must test its value: #if UMBRELLAELLA_WORKBENCH
            for n, ln in enumerate(body.splitlines(), 1):
                if WORKBENCH_DEFINED.search(ln):
                    out.append(f"{os.path.relpath(p, root)}:{n} tests whether {WORKBENCH_DEFINE} is defined; it is "
                               f"always defined (=0 in the submission): write `#if {WORKBENCH_DEFINE}`")
                elif WORKBENCH_ANY_IF.search(ln) and not WORKBENCH_EXACT_IF.match(ln):
                    # dry run B M5: `#if UMBRELLAELLA_WORKBENCH || !UE_BUILD_SHIPPING` compiles it into the submission
                    out.append(f"{os.path.relpath(p, root)}:{n} guards on more than {WORKBENCH_DEFINE}; the guard is "
                               f"exactly `#if {WORKBENCH_DEFINE}` (nest any other condition inside it)")
    return out


def strip_comments(text):
    """C++/C# source without // and /* */ comments (string literals kept), so a commented-out define never counts."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            out.append("\n" * text.count("\n", i, n if j < 0 else j))
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def no_player_maps(root):
    """Maps with no player pawn, where input=none is accepted: the first cell of each row of
    pipeline/qa/no-player-maps.txt (`<map> | <card> | <why>`; the map card adds its row). Missing file: L_Title."""
    try:
        with open(os.path.join(root, NO_PLAYER_FILE), encoding="utf-8") as fh:
            rows = [ln.split("|", 1)[0].strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    except OSError:
        return NO_PLAYER_MAPS
    return ",".join(r for r in rows if r)


EFFECTIVE_LINE = re.compile(r"\bSMOKE_EFFECTIVE\b(?P<rest>[^\n]*)")
# Final-10 B M1: in a game log only the hook's own line counts: at the start of a line, after the [time][frame]
# prefixes, in the game's log category. A SMOKE_EFFECTIVE inside another line (LogInit echoing the command line) never does.
EFFECTIVE_LOG_LINE = re.compile(r"^(?:\[[^\]\n]*\])*[ \t]*LogUmbrellaElla:[ \t]*(?:(?:Display|Log|Warning):[ \t]*)?"
                                r"SMOKE_EFFECTIVE\b(?P<rest>[^\n]*)", re.M)
EFFECTIVE_FIELD = re.compile(r"(?:^|\s)([\w.-]+)=(\S+)")


def parse_effective(text):
    """The first SMOKE_EFFECTIVE line in text as {field: value} (at, commit, workbench, platform, manifest and one
    value per baked key, as `<KEY>=v` or as the reflected `<Struct>.<Field>=v`), or None. A field given twice is
    listed under `_dup` (final-10 B M2: the last one never silently wins)."""
    m = EFFECTIVE_LINE.search(text or "")
    if not m:
        return None
    return effective_fields(m.group("rest"))


def effective_fields(rest):
    out, dup = {}, []
    for k, v in EFFECTIVE_FIELD.findall(rest):
        if k in out and k not in dup:
            dup.append(k)
        out[k] = v
    if dup:
        out["_dup"] = ",".join(dup)
    return out


def effective_lines(logs_text):
    """Final-10 B H3, B M1: the hook's SMOKE_EFFECTIVE lines, one log at a time: [(raw line, fields)] from the first
    log (the game log first) that has any. The hook logs `at=start` once at the first gameplay frame and `at=end`
    when the run ends (the Survived or fail screen, else the -SmokeQuitAfter quit)."""
    for text in logs_text:
        hits = [(m.group(0).strip(), effective_fields(m.group("rest"))) for m in EFFECTIVE_LOG_LINE.finditer(text or "")]
        if hits:
            return hits
    return []


def effective_line_problems(hits):
    """Exactly one at=start line and at least one at=end line (final-10 B H3, B M1)."""
    starts = [h for h in hits if h[1].get("at") == "start"]
    ends = [h for h in hits if h[1].get("at") == "end"]
    out = []
    if len(starts) != 1:
        out.append(f"the game log has {len(starts)} `SMOKE_EFFECTIVE at=start` line(s); the hook logs exactly one, at "
                   "the first gameplay frame (tools/ue_run.py contract)")
    if not ends:
        out.append("the game log has no `SMOKE_EFFECTIVE at=end` line: the hook reads the values again when the run "
                   "ends (the Survived or fail screen, else the -SmokeQuitAfter quit), so a write after startup shows")
    for raw, f in hits:
        if f.get("at") not in ("start", "end"):
            out.append(f"'{raw[:80]}' has no at=start|end")
    return out


def read_logs(logs):
    out = []
    for log in logs:
        with open(log, encoding="utf-8", errors="replace") as fh:
            out.append(fh.read())
    return out


def file_sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def zip_member_for(zip_path, exe):
    """Final-10 B H2: the member of the zip that is byte for byte the smoked exe (same file name), or None."""
    import hashlib
    import zipfile
    want, name = file_sha256(exe), os.path.basename(exe).lower()
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if os.path.basename(info.filename).lower() != name:
                continue
            h = hashlib.sha256()
            with z.open(info) as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            if h.hexdigest() == want:
                return info.filename, want
    return None, want


def launch_record(root, zip_path, logs, record, exe=None):
    """Append the LAUNCH line for a passing smoke of the unzipped gate zip (final-9 B H4, H5). Final-10 B H1, H2: the
    line is written only here, and every field is derived from files: the zip's sha256, the zip member that is
    byte for byte the smoked exe (a smoke of any other exe with SMOKE_ZIP set fails), and the game log's own
    SMOKE_EFFECTIVE start line. check_card.py --gate-record re-hashes the zip and that member."""
    texts = read_logs(logs)
    hits = effective_lines(list(reversed(texts)))
    joined = "\n".join(texts)
    probs = effective_line_problems(hits)
    if not hits or not SMOKE_LINE.search(joined) or probs:
        print("FAIL: launch-record: the logs have no SMOKE_OK and SMOKE_EFFECTIVE at=start / at=end lines; run it after "
              "a passing smoke" + ("".join("\n  " + p for p in probs) if hits else ""))
        return 1
    if not exe or not os.path.isfile(exe):
        print("FAIL: launch-record: --exe <the smoked exe> is required: the record names the zip member it ran")
        return 1
    member, exe_sha = zip_member_for(zip_path, exe)
    if member is None:
        print(f"FAIL: launch-record: {exe} is not a file of {os.path.basename(zip_path)} (no member with its name and "
              "sha256): unzip SMOKE_ZIP and smoke the exe from that folder (final-10 B H2)")
        return 1
    digest = file_sha256(zip_path)
    raw, eff = next(h for h in hits if h[1].get("at") == "start")
    rest = raw[raw.index("SMOKE_EFFECTIVE") + len("SMOKE_EFFECTIVE"):]
    line = (f"LAUNCH {digest} | zip={os.path.basename(zip_path)} exe={member} exe_sha256={exe_sha} "
            f"commit={eff.get('commit', 'unknown')} platform={eff.get('platform', 'unknown')} "
            f"workbench={eff.get('workbench', 'unknown')} host={platform.node()}/{platform.system()} | "
            f"SMOKE_EFFECTIVE{rest.rstrip()}")
    os.makedirs(os.path.dirname(os.path.abspath(record)), exist_ok=True)
    with open(record, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)
    return 0


def smoke_counts(text, allow=()):
    lines = text.splitlines()
    counts = {p: sum(1 for ln in lines if p in ln) for p in SMOKE_BAD}
    for label, rx in SMOKE_BAD_BROAD.items():
        counts[label] = sum(1 for ln in lines if rx.search(ln) and not any(a.search(ln) for a in allow))
    return counts


def load_allow(path, decisions):
    """Regexes from the allow file. Each line is `<decision id> | <regex>`; the id must be a row in decisions."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except FileNotFoundError:
        return []
    rows = [(i, ln.strip()) for i, ln in enumerate(lines, 1) if ln.strip() and not ln.strip().startswith("#")]
    if not rows:
        return []
    try:
        with open(decisions, encoding="utf-8") as fh:
            known = set(re.findall(r"^\|\s*(D[\w-]+)\s*\|", fh.read(), re.M))
    except OSError:
        known = set()
    out = []
    for i, ln in rows:
        did, sep, rx = (x.strip() for x in ln.partition("|"))
        if not sep or not rx or not re.fullmatch(r"D[\w-]+", did):
            raise ValueError(f"{path}:{i}: write `<decision id> | <regex>`, got: {ln}")
        if did not in known:
            raise ValueError(f"{path}:{i}: {did} is not a row in {decisions}; an allowed log line needs a decision")
        try:
            out.append(re.compile(rx))
        except re.error as e:
            raise ValueError(f"{path}:{i}: bad regex: {e}")
    return out


SMOKE_LINE = re.compile(r"\bSMOKE_OK\b(?P<rest>[^\n]*)")
FIELDS = re.compile(r"\b(map|fps|worst_ms|commit|input|input_vz|gamepad|gp_vx|gp_attack_vz|gp_shield_vz|res|win|"
                    r"textpx|load_ms|section|workbench|view|aspect|debugdraw)=(\S+)")
SHOT_LINE = re.compile(r"\bSMOKE_SHOT\b")
ASPECT = "16:9"
ASPECT_TOL = 0.01
# Art bootstrap: before card 0.10b imports the anchors there is no game art, so the smoke screenshot's art and screen
# checks print but do not fail (the daily lists it in Not checked; from G2 a gate does not accept it)
ART_ANCHORS = os.path.join("Content", "UmbrellaElla", "Art", "Anchors")


def art_bootstrap(root):
    return not os.path.isdir(os.path.join(root or ROOT, ART_ANCHORS))


def aspect_problems(fields, want=ASPECT, tol=ASPECT_TOL):
    """The gameplay view on a SMOKE_OK line is 16:9 (GDD 1.3 §7: fixed 16:9 gameplay camera). A missing view= or
    aspect= fails: no measurement is not a pass."""
    view = fields.get("view", "")
    m = re.fullmatch(r"(\d+)x(\d+)", view.lower())
    asp = num(fields.get("aspect"))
    if not m or asp is None or not int(m.group(2)):
        return [f"SMOKE_OK has no view=WxH aspect=N (got view={view or '<none>'} aspect={fields.get('aspect', '<none>')}): "
                "the hook logs the gameplay view inside the bars"]
    vw, vh = int(m.group(1)), int(m.group(2))
    real = vw / vh
    a, _, b = want.partition(":")
    target = float(a) / float(b) if b else float(a)
    out = []
    if abs(asp - real) > 0.002:
        out.append(f"SMOKE_OK aspect={asp:g} disagrees with view={view} ({real:.3f}): log the measured view")
    if abs(real - target) > tol:
        out.append(f"gameplay view {view} is {real:.3f}:1, not {want} ({target:.3f} +/- {tol:g}): lock the view target "
                   "camera to 16:9 (Constrain Aspect Ratio, pipeline/unreal-rules.md Display)")
    r = re.fullmatch(r"(\d+)x(\d+)", fields.get("res", "").lower())
    if r:
        rw, rh = int(r.group(1)), int(r.group(2))
        if vw > rw + 1 or vh > rh + 1:
            out.append(f"SMOKE_OK view={view} is bigger than the window res={fields['res']}")
        elif abs(vw - rw) > 2 and abs(vh - rh) > 2:
            out.append(f"SMOKE_OK view={view} fills neither axis of res={fields['res']}: bars on all four sides")
    return out


def shot_checks(shot, root=None, scene=True, env=None):
    """art_check.py, screen_check.py and (scene=True: a gameplay map) art_judge.py scene on the smoke screenshot.
    Returns (printed lines, failures). References outside the repo are found under ART_REFS_ROOT (os.pathsep list)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import art_check
    import art_judge
    import screen_check
    root = root or ROOT
    if not shot or not os.path.isfile(shot):
        why = f"no smoke screenshot at {shot}" if shot else "no --shot screenshot (the scripts pass -SmokeShot=)"
        return [f"smoke-art: {why}"], [why]
    style_path = os.path.join(root, "pipeline", "art", "style.json")
    lines, fails = [], []
    try:
        res = screen_check.check(shot, screen_check.thresholds(style_path))
        res["image"] = os.path.basename(shot)   # a pasted line carries no machine path
        screen = ["smoke-art: " + ln for ln in screen_check.report(res)]
        if not res["pass"]:
            fails.append("screen_check: " + ", ".join(sorted({p["kind"] for p in res["problems"]})))
        view = shot
        if res["bars"] != "none" and res["box"][2] and res["box"][3]:
            view = screen_check.crop_view(shot, res, os.path.splitext(shot)[0] + "-view.png")
    except (OSError, ValueError) as e:
        screen = [f"smoke-art: screen_check: FAIL cannot read {shot}: {e}"]
        fails.append(f"screen_check: {e}")
        view = shot
    try:
        with open(style_path, encoding="utf-8") as fh:
            style = json.load(fh)
        af = art_check.evaluate(art_check.measure(view, style), style) + art_check.provisional_failure(
            style, os.path.join(root, "pipeline", "art", "reference", "target-keyart.png"))
    except (OSError, ValueError, KeyError) as e:
        af = [f"cannot check: {e}"]
    lines.append(f"smoke-art: art_check: {'PASS' if not af else 'FAIL'} shot={os.path.basename(shot)}"
                 + (" (" + "; ".join(af[:3]) + ")" if af else ""))
    fails = [f"art_check: {x}" for x in af] + fails
    lines += screen
    if scene:
        roots = list(dict.fromkeys([root, ROOT] + [r for r in (env if env is not None else os.environ).get(
            "ART_REFS_ROOT", "").split(os.pathsep) if r]))
        try:
            refs = art_judge.load_refs(os.path.join(root, "pipeline", "art", "references.json"))
            m, probs, score, _ = art_judge.scene(view, refs, roots)
            rh = art_judge.refs_hash(os.path.join(root, "pipeline", "art", "references.json"))
            lines.append(f"smoke-art: art_judge: {'PASS' if not probs else 'FAIL'} scene score={score} refs={rh} "
                         f"shot={os.path.basename(shot)}")
            lines += [f"smoke-art:   - {k}: {msg}" for k, msg in probs]
            lines += [f"smoke-art: FIX: {k}: {art_judge.FIX[k]}" for k in dict.fromkeys(k for k, _ in probs)]
            if probs:
                fails.append("art_judge: " + ", ".join(dict.fromkeys(k for k, _ in probs)))
        except (OSError, ValueError, KeyError) as e:
            lines.append(f"smoke-art: art_judge: FAIL cannot judge: {e}")
            fails.append(f"art_judge: {e}")
    return lines, fails
CYCLE = re.compile(r"\bSMOKE_CYCLE\s+n=(\d+)\s+actors=(\d+)\s+health=(\S+)(?:\s+load_ms=(\S+))?")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def shield_merged(root):
    """The test-map Shield row (DEF-01, the MVP 10 card) is merged: from then on the gamepad smoke needs gp_shield_vz."""
    if root is None:
        return False
    try:
        with open(os.path.join(root, "pipeline", "qa", "test-map.md"), encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return True
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) > 2 and cells[0] == "Shield" and "DEF-01" in cells[1]:
            return cells[-1] != "planned"
    return True


def gamepad_problems(fields, shield_due=True):
    """Card 0.6e: raw gamepad input reached movement, attack and (once the MVP 10 shield merged) shield in the
    packaged build. Before that gp_shield_vz may read none."""
    out = []
    if fields.get("gamepad", "<none>").lower() != "ok":
        return [f"SMOKE_OK gamepad={fields.get('gamepad', '<none>')}: the hook must feed raw gamepad keys and log "
                "gamepad=ok with gp_vx, gp_attack_vz and gp_shield_vz (card 0.6e; SMOKE_REQUIRE_GAMEPAD=0 only while "
                "the QA-GP row is planned)"]
    for k, sign, what in (("gp_vx", 1, "left stick right moves Ella right"),
                          ("gp_attack_vz", -1, "right trigger holds ATTACK, so she falls"),
                          ("gp_shield_vz", -1, "left trigger holds SHIELD, so she falls")):
        v = num(fields.get(k))
        if k == "gp_shield_vz" and not shield_due and fields.get(k, "none").lower() == "none":
            continue
        if v is None or v * sign <= 0:
            out.append(f"SMOKE_OK {k}={fields.get(k, '<none>')}: {what} ({'above' if sign > 0 else 'below'} 0)")
    return out


def smoke_log(logs, exit_code, expect_map=None, expect_commit=None, min_fps=MIN_FPS, expect_res=None,
              expect_win=None, min_text_px=0, max_frame_ms=MAX_FRAME_MS, require_input=True,
              no_player_maps=NO_PLAYER_MAPS, expect_section=None, restart_cycles=0, allow=(),
              max_load_ms=MAX_LOAD_MS, expect_workbench=None, root=None, require_gamepad=True, expect_aspect=None,
              aspect_tol=ASPECT_TOL, expect_debugdraw=None, shot=None, art_checks=True):
    text = ""
    for log in logs:
        with open(log, encoding="utf-8", errors="replace") as fh:
            text += fh.read() + "\n"
    counts = smoke_counts(text, allow)
    m = SMOKE_LINE.search(text)
    ok_line = m is not None
    fields = dict(FIELDS.findall(m.group("rest"))) if m else {}
    no_player = {short_map(x.strip()) for x in (no_player_maps or "").split(",") if x.strip()}
    if root is not None:
        dm = maps(root)[0]
        no_player.discard(short_map(dm) if dm else None)   # final-9 A H2: the map the game boots always has Ella
    on_no_player_map = short_map(fields.get("map", "")) in no_player
    print(f"smoke: exit={exit_code} SMOKE_OK={'yes' if ok_line else 'no'} "
          + " ".join(f"{k}={fields[k]}" for k in ("fps", "worst_ms", "input", "res", "win", "view", "aspect",
                                                  "debugdraw", "textpx", "load_ms", "section")
                     if k in fields) + " "
          + " ".join(f"'{k}'={v}" for k, v in counts.items()))
    if m:
        # The game's own log line, as printed, on a line of its own: the PR pastes it from this output (final-7 A H2)
        start = text.rfind("\n", 0, m.start()) + 1
        end = text.find("\n", m.start())
        print(text[start:end if end >= 0 else len(text)].rstrip("\r"))
    fails = []
    if exit_code != 0:
        fails.append(f"exit code {exit_code}")
    if not ok_line:
        fails.append("no SMOKE_OK line")
    else:
        for k in ("map", "commit"):
            if k not in fields:
                fails.append(f"SMOKE_OK line has no {k}= (format: SMOKE_OK map=<name> fps=<n> commit=<sha>)")
        got_map = fields.get("map", "").rsplit("/", 1)[-1].split(".")[0]
        if expect_map and "map" in fields and got_map != expect_map.rsplit("/", 1)[-1].split(".")[0]:
            fails.append(f"SMOKE_OK map={fields['map']}, expected {expect_map}")
        got_c = fields.get("commit", "").lower()
        if expect_commit and got_c and not (expect_commit.lower().startswith(got_c) or got_c.startswith(expect_commit.lower())):
            fails.append(f"SMOKE_OK commit={got_c}, but the package was built from {expect_commit}")
        if min_fps:
            fps = num(fields.get("fps"))
            if fps is None:
                fails.append(f"SMOKE_OK line has no numeric fps= (needed for --min-fps {min_fps:g})")
            elif fps < min_fps:
                fails.append(f"fps {fps:g} is below the minimum {min_fps:g}")
        if expect_res and fields.get("res", "").lower() != expect_res.lower():
            fails.append(f"SMOKE_OK res={fields.get('res', '<none>')}, expected {expect_res}")
        if expect_win and fields.get("win", "").lower() != expect_win.lower():
            fails.append(f"SMOKE_OK win={fields.get('win', '<none>')}, expected {expect_win}")
        if min_text_px:
            px = num(fields.get("textpx"))
            if px is None:
                fails.append("SMOKE_OK line has no numeric textpx= (smallest UI text height in px)")
            elif px < min_text_px:
                fails.append(f"smallest UI text is {px:g} px, minimum is {min_text_px:g} px")
        if max_frame_ms:
            worst = num(fields.get("worst_ms"))
            if worst is None:
                fails.append(f"SMOKE_OK line has no numeric worst_ms= (needed for --max-frame-ms {max_frame_ms:g})")
            elif worst > max_frame_ms:
                fails.append(f"worst frame {worst:g} ms is over the limit {max_frame_ms:g} ms")
        if require_input:
            got = fields.get("input", "<none>").lower()
            if not (got == "ok" or (got == "none" and on_no_player_map)):
                fails.append(f"SMOKE_OK input={got}; the hook must inject input and log input=ok "
                             f"(input=none only on {', '.join(sorted(no_player)) or 'no map'})")
            elif got == "ok" and not on_no_player_map:
                vz = num(fields.get("input_vz"))
                if vz is None or vz >= 0:
                    # final-8 A H2: GDD 1.3 UP_OPEN (no input held) rises, so only descent under held ATTACK
                    # proves the Enhanced Input binding works
                    fails.append(f"SMOKE_OK input_vz={fields.get('input_vz', '<none>')}: input=ok needs the Z "
                                 "velocity measured while the hook held IA_Attack, below 0 (GDD 1.3: with nothing held "
                                 "the umbrella rises)")
                if require_gamepad:
                    fails += gamepad_problems(fields, shield_merged(root))
        if expect_section and fields.get("section", "").lower() != expect_section.lower():
            fails.append(f"SMOKE_OK section={fields.get('section', '<none>')}, expected {expect_section}")
        if max_load_ms:
            fails += load_problems("SMOKE_OK", fields.get("load_ms"), max_load_ms)
        if expect_aspect:
            fails += aspect_problems(fields, expect_aspect, aspect_tol)
        if expect_debugdraw is not None and fields.get("debugdraw") != str(expect_debugdraw):
            fails.append(f"SMOKE_OK debugdraw={fields.get('debugdraw', '<none>')}, expected {expect_debugdraw}: a default "
                         "launch has every debug draw off (hitbox and collision draws, debug text; ue.Debug 0)")
        if art_checks:
            lines, art_fails = shot_checks(shot, root, scene=not on_no_player_map)
            if not SHOT_LINE.search(text):
                art_fails.append("no SMOKE_SHOT line: the hook did not take the -SmokeShot= screenshot")
                lines.append("smoke-art: no SMOKE_SHOT line in the log")
            for ln in lines:
                print(ln)
            if art_bootstrap(root):
                print(f"smoke-art: bootstrap: not blocking until {ART_ANCHORS.replace(os.sep, '/')}/ exists (card 0.10b)")
            else:
                fails += art_fails
        if restart_cycles and not on_no_player_map:
            cycles = CYCLE.findall(text)
            fails += cycle_problems(cycles, restart_cycles)
            if max_load_ms:
                for c in cycles:
                    fails += load_problems(f"SMOKE_CYCLE n={c[0]}", c[3] or None, max_load_ms)
    if expect_workbench is not None:
        if ok_line and fields.get("workbench") != str(expect_workbench):
            fails.append(f"SMOKE_OK workbench={fields.get('workbench', '<none>')}, BUILD_INFO says {expect_workbench}")
        if str(expect_workbench) == "0":
            wb = [ln.strip() for ln in text.splitlines() if WORKBENCH_MARKERS.search(ln)]
            if wb:
                fails.append(f"{len(wb)} workbench line(s) in a workbench=0 package, e.g. '{wb[0][:80]}'")
    fails += [f"{v} '{k}' line(s)" for k, v in counts.items() if v]
    if fails:
        print("FAIL: " + "; ".join(fails))
        return 1
    print("PASS")
    return 0


def load_problems(where, value, limit):
    """load_ms must be a number <= limit. A missing number fails: no measurement is not a pass."""
    ms = num(value)
    if ms is None:
        return [f"{where} has no numeric load_ms= (needed for --max-load-ms {limit:g})"]
    if ms > limit:
        return [f"{where} load took {ms:g} ms, over the limit {limit:g} ms"]
    return []


def cycle_problems(cycles, want):
    """SMOKE_CYCLE lines: at least `want` cycles, and the same actor count and health after each one."""
    if len({c[0] for c in cycles}) < want:
        return [f"{len(cycles)} SMOKE_CYCLE line(s), expected {want} die -> restart cycles"]
    out = []
    for i, label in ((1, "actor count"), (2, "health")):
        vals = [c[i] for c in cycles]
        if len(set(vals)) > 1:
            out.append(f"{label} drifted across restart cycles: {' '.join(vals)}")
    return out


def crash_list(dirs):
    found = set()
    for d in dirs:
        if d and os.path.isdir(d):
            for p in glob.glob(os.path.join(glob.escape(d), "**", "Saved", "Crashes", "*"), recursive=True):
                found.add(os.path.normpath(p))
            for p in glob.glob(os.path.join(glob.escape(d), "Crashes", "*")):   # d is itself a Saved folder
                found.add(os.path.normpath(p))
    return found


def crash_check(before_file, dirs):
    """Exit 1 on a new crash folder. Exit 2 when none of the watched roots exists: a wrong path is not a pass."""
    present = [d for d in dirs if d and os.path.isdir(d)]
    for d in dirs:
        if d and d not in present:
            print(f"crash root missing: {d}")
    if not present:
        print("FAIL: none of the watched crash roots exists, so a crash could not be seen. Fix the path "
              "(SMOKE_CRASH_DIRS) before trusting this smoke.")
        return 2
    try:
        with open(before_file, encoding="utf-8") as fh:
            before = {ln.strip() for ln in fh if ln.strip()}
    except OSError:
        before = set()
    new = sorted(crash_list(dirs) - before)
    print(f"crash folders: {len(new)} new")
    for n in new:
        print("  new crash folder: " + n)
    if new:
        print("FAIL: new Saved/Crashes folder")
        return 1
    return 0


def close_process(proc):
    """Ask the game to close the way a user would: WM_CLOSE on Windows, SIGTERM elsewhere. [VERIFY on 5.8.4]"""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def each(hwnd, _):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == proc.pid:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)   # WM_CLOSE
            return True
        user32.EnumWindows(proto(each), 0)
    else:
        proc.send_signal(signal.SIGTERM)


def window_up(proc):
    """True once proc shows a visible top-level window (Windows only), None where it can't be seen.
    [VERIFY on 5.8.4 that the first visible window is the title screen, not a splash]"""
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    seen = []

    def each(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == proc.pid and user32.IsWindowVisible(hwnd):
            seen.append(hwnd)
        return True
    user32.EnumWindows(proto(each), 0)
    return bool(seen)


def alive(cmd, seconds, close_timeout, log, max_boot_s=0):
    """Pass when cmd is still running after `seconds`, then exits with code 0 within close_timeout once closed.
    With max_boot_s, the first visible window must also show within that many seconds (prints boot_s=)."""
    os.makedirs(os.path.dirname(os.path.abspath(log)), exist_ok=True)
    with open(log, "ab") as fh:
        start = time.monotonic()
        proc = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
        boot, why = None, ""
        while True:
            t = time.monotonic() - start
            if proc.poll() is not None:
                print(f"FAIL: exited after {t:.1f}s with code {proc.returncode}, before {seconds}s")
                return 1
            if max_boot_s and boot is None:
                up = window_up(proc)
                if up:
                    boot = t
                elif up is None or t > max_boot_s:
                    why = "can't see windows on this OS" if up is None else f"no window within {max_boot_s:g} s"
                    break
            if t >= seconds and (not max_boot_s or boot is not None):
                break
            time.sleep(0.2)
        if why or (boot is not None and boot > max_boot_s):
            print("boot_s=unknown" if boot is None else f"boot_s={boot:.1f}")
            print(f"FAIL: boot time not measured ({why})" if why
                  else f"FAIL: first window after {boot:.1f} s, limit {max_boot_s:g} s")
            close_process(proc)
            try:
                proc.wait(close_timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            return 1
        if boot is not None:
            print(f"boot_s={boot:.1f}")
        print(f"alive at {seconds}s; closing")
        close_process(proc)
        try:
            rc = proc.wait(close_timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print(f"FAIL: did not close within {close_timeout}s")
            return TIMEOUT_RC
    if rc != 0:
        print(f"FAIL: closed with exit code {rc}")
        return 1
    print("PASS (alive, closed with exit code 0)")
    return 0


def ini_values(path, key):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    for ln in text.splitlines():
        m = re.match(r"\s*[+]?" + key + r"\s*=\s*(.+)", ln)
        if m:
            v = m.group(1).strip()
            fp = re.search(r'FilePath\s*=\s*"([^"]+)"', v)
            out.append(fp.group(1) if fp else v.strip('"'))
    return out


def short_map(m):
    return m.rsplit("/", 1)[-1].split(".")[0]


def maps(root):
    """(GameDefaultMap or None, every map to smoke). Reads Config/DefaultEngine.ini and DefaultGame.ini. [VERIFY keys]"""
    default = (ini_values(os.path.join(root, "Config", "DefaultEngine.ini"), "GameDefaultMap") or [None])[0]
    seen, out = set(), []
    for m in ([default] if default else []) + ini_values(os.path.join(root, "Config", "DefaultGame.ini"), "MapsToCook"):
        if short_map(m) not in seen:
            seen.add(short_map(m))
            out.append(m)
    return default, out


def desktop_res(env):
    """(w, h) of the main monitor, or None when it can't be read. SMOKE_DESKTOP_RES=WxH overrides. [VERIFY]"""
    m = re.fullmatch(r"(\d+)x(\d+)", env.get("SMOKE_DESKTOP_RES", "").strip().lower())
    if m:
        return int(m.group(1)), int(m.group(2))
    try:
        if os.name == "nt":
            import ctypes
            u = ctypes.windll.user32
            u.SetProcessDPIAware()   # otherwise a scaled desktop reports a smaller size
            return u.GetSystemMetrics(0), u.GetSystemMetrics(1)
        if platform.system() == "Darwin":
            out = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True,
                                 timeout=30).stdout
            sizes = [(int(w), int(h)) for w, h in re.findall(r"Resolution:\s*(\d+)\s*x\s*(\d+)", out)]
            return max(sizes) if sizes else None
    except Exception:   # any failure means "unknown": run every mode rather than skip one
        return None
    return None


CLIENT_TEST = "UmbrellaElla.Flow.TitleToPlayToSurvived"


def good_daily(line, require_client=False):
    """A DAILY line counts when package and smoke passed and no step that ran failed."""
    steps = dict(re.findall(r"\b([a-z-]+)=(PASS|FAIL|NOT RUN|not run)", line.split(" | Not checked:")[0]))
    if steps.get("package") != "PASS" or steps.get("smoke") != "PASS" or "FAIL" in steps.values():
        return False
    return not require_client or steps.get("client-test") == "PASS"


def merge_missing(root, since, lines, require_client=False, until="HEAD"):
    """(first-parent commits in since..until, the ones with no clean DAILY line that good_daily() accepts)."""
    p = git(root, "rev-list", "--first-parent", f"{since}..{until}")
    if p.returncode != 0:
        raise OSError(p.stderr.strip() or f"git rev-list {since}..{until} failed")
    lines = [ln for ln in lines if ln.startswith("DAILY ")]
    shas = p.stdout.split()
    good = [ln.split()[1] for ln in lines if good_daily(ln)]
    good_client = [ln.split()[1] for ln in lines if good_daily(ln, True)]

    def client_due(sha):
        """--require-client counts only for commits whose own test map has the packaged flow test merged: a commit
        merged before the title screen existed cannot pass client-test (final-8 A H7)."""
        t = git(root, "show", f"{sha}:pipeline/qa/test-map.md")
        if t.returncode != 0:
            return True
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import check_automation_report as car
        return CLIENT_TEST in car.test_map_requirements(t.stdout)[0]

    def ok(sha):
        pool = good_client if require_client and client_due(sha) else good
        return any(g and "+" not in g and sha.startswith(g) for g in pool)
    return shas, [s for s in shas if not ok(s)]


def merge_check(root, since, record, require_client=False):
    """Each first-parent commit in since..HEAD needs a clean DAILY line that good_daily() accepts."""
    try:
        with open(record, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        lines = []
    shas, missing = merge_missing(root, since, lines, require_client)
    print(f"merge-check: {len(shas) - len(missing)}/{len(shas)} commit(s) since {since} have a passing DAILY line"
          + (" (client-test=PASS required)" if require_client else ""))
    for s in missing:
        print("  no passing DAILY line: " + s[:12])
    return 1 if missing else 0


# Built in two parts so this file does not count its own tag.
VERIFY_TAG = re.compile(r"\[" + "VERIFY" + r"[^\]]*\]")


def verify_tags(root):
    """Every open VERIFY tag in the engine-facing scripts: (path, line number, text)."""
    files = sorted(glob.glob(os.path.join(root, "tools", "ue", "*.sh")) + glob.glob(os.path.join(root, "tools", "ue", "*.ps1"))
                   + [os.path.join(root, "tools", f) for f in ("ue_run.py", "check_automation_report.py")])
    out = []
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                for i, ln in enumerate(fh, 1):
                    if VERIFY_TAG.search(ln):
                        out.append((os.path.relpath(f, root), i, ln.strip()))
        except OSError:
            continue
    return out


STRESS_FIELDS = ["pause-restart", "pause-quit", "hold-alt-tab", "two-runs", "audio-switch", "gamepad"]
AUDIO_RESUME_S = 2.0


def stress_problems(line):
    """Problems with one STRESS line. Blank or missing fields fail; gamepad may be `not merged`."""
    got = fields_of(line)
    out = []
    for f in STRESS_FIELDS:
        v = got.get(f, "")
        if not v:
            out.append(f"{f}: blank (a blank field is not a pass)")
        elif f == "gamepad" and v == "not merged":
            continue
        elif not v.startswith("pass"):
            out.append(f"{f}: {v}")
        elif f == "audio-switch":
            m = re.search(r"\(\s*([\d.]+)\s*s", v)
            if not m:
                out.append("audio-switch: no '(N s)' seconds to resume")
            elif float(m.group(1)) > AUDIO_RESUME_S:
                out.append(f"audio-switch: {m.group(1)} s to resume, limit {AUDIO_RESUME_S:g} s")
    return out


PLAYTHROUGH_PHASES = ["intro", "contest", "desperation"]
PLAYTHROUGH_FIELDS = PLAYTHROUGH_PHASES + ["survived", "fail-retry", "fail-bottom", "quit-play", "quit-title", "quit-pause"]
# What exists at each gate (GDD 1.3 section 12A; pipeline/roles/producer.md Gates). G1 (Nov 12, first playable) is
# health/death, timer and restart: the bottom exit, health fail and retry (MVP 4-5) and the 90 s survive (MVP 6).
# The player screens (title, pause) are the Nov 13 target, so both quits are due from G2 (final-7 dry run A H1).
# The optional phase presets (GDD 1.3 section 8) are due from G3. A field not due yet may read n/a. No --gate = all.
# quit-play is due from G1: the G1 build goes to testers (itch Draft), and the first test build had no way out but
# Alt+F4. From play, an in-game quit (a key or a button) closes the game with exit code 0.
PLAYTHROUGH_G1 = ["survived", "fail-retry", "fail-bottom", "quit-play"]
PLAYTHROUGH_G2 = PLAYTHROUGH_G1 + ["quit-title", "quit-pause"]
PLAYTHROUGH_DUE = {"G1": PLAYTHROUGH_G1,
                   "G2": PLAYTHROUGH_G2,
                   "G3": PLAYTHROUGH_FIELDS, "G4": PLAYTHROUGH_FIELDS}
SHIPPING_BOOT_S = 20.0


def playthrough_fields(root=None):
    """GDD 1.3 §8: phases are optional presets. The phase fields are due only when pipeline/level/encounter.json
    uses the intro/contest/desperation presets; with the one base phase, `survived` covers the run.
    No readable encounter file = all three (the strict case)."""
    try:
        with open(os.path.join(root or ROOT, "pipeline", "level", "encounter.json"), encoding="utf-8") as fh:
            ids = [ph.get("id") for ph in json.load(fh).get("phases", [])]
    except (OSError, ValueError, AttributeError):
        return PLAYTHROUGH_FIELDS
    return [f for f in PLAYTHROUGH_FIELDS if f not in PLAYTHROUGH_PHASES or f in ids]


def fields_of(line):
    got = {}
    for p in [p.strip() for p in line.split("|")][1:]:
        name, _, value = p.partition(" ")
        if "=" in name and not value:
            name, _, value = name.partition("=")
        got[name] = value.strip().lower()
    return got


def playthrough_problems(line, gate=None, root=None):
    """Problems with one PLAYTHROUGH line: every phase in order, survived, a health fail and retry, a bottom-exit
    fail (GDD §2), and both quits must pass. With a gate, only the fields due at it must pass; the rest may be n/a."""
    got = fields_of(line)
    out = []
    fields = playthrough_fields(root)
    due = [f for f in (PLAYTHROUGH_DUE[gate] if gate else PLAYTHROUGH_FIELDS) if f in fields]
    for f in fields:
        v = got.get(f, "")
        if f not in due:
            if v not in ("pass", "n/a"):
                out.append(f"{f}: {v or 'blank'} (not due at {gate}: write pass or n/a)")
        elif not v:
            out.append(f"{f}: blank (a blank field is not a pass)")
        elif v != "pass":
            out.append(f"{f}: {v}")
    return out


def shipping_problems(line):
    """Problems with one SHIPPING line: boot_s <= 20 and quit rc=0."""
    got = fields_of(line)
    out = []
    boot = num(got.get("boot_s"))
    if boot is None:
        out.append("boot_s: no number (seconds from launch to the title screen)")
    elif boot > SHIPPING_BOOT_S:
        out.append(f"boot_s: {boot:g} s, limit {SHIPPING_BOOT_S:g} s")
    if got.get("quit", "").replace(" ", "") != "rc=0":
        out.append(f"quit: {got.get('quit') or 'blank'} (needs rc=0)")
    return out


HAND_LINES = {"STRESS": (stress_problems, "every hand check passed"),
              "PLAYTHROUGH": (playthrough_problems, "every due field (phase presets, survived, fail-retry, fail-bottom, quit-play, both quits) passed"),
              "SHIPPING": (shipping_problems, f"boot <= {SHIPPING_BOOT_S:g} s and quit rc=0")}


def hand_check(root, commit, record, kind, gate=None):
    """exit 1 unless the record's last `<kind> <sha>` line for commit has no problems."""
    p = git(root, "rev-parse", commit)
    if p.returncode != 0:
        raise OSError(p.stderr.strip() or f"git rev-parse {commit} failed")
    sha = p.stdout.strip()
    try:
        with open(record, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.startswith(kind + " ")]
    except OSError:
        lines = []
    mine = [ln for ln in lines if len(ln.split()) > 1 and len(ln.split()[1]) >= 7 and sha.startswith(ln.split()[1])]
    if not mine:
        print(f"FAIL: no {kind} line for {sha[:12]} in {record}")
        return 1
    problems, ok = HAND_LINES[kind]
    if kind == "PLAYTHROUGH":
        probs = problems(mine[-1], gate, root)
    else:
        probs = problems(mine[-1], gate) if gate else problems(mine[-1])
    if probs:
        print(f"FAIL: {kind} {sha[:12]}: " + "; ".join(probs))
        return 1
    if gate:
        fields = playthrough_fields(root) if kind == "PLAYTHROUGH" else PLAYTHROUGH_DUE[gate]
        # only the fields this encounter has (one GDD 1.3 base phase: no intro/contest/desperation; dry run A M12)
        ok = f"{gate}: " + ", ".join(f for f in PLAYTHROUGH_DUE[gate] if f in fields) + " passed"
    print(f"PASS: {kind} {sha[:12]}: {ok}")
    return 0


def stress_check(root, commit, record):
    return hand_check(root, commit, record, "STRESS")


STATE_GLOBS = [os.path.join("Saved", "SaveGames", "**", "*"),
               os.path.join("Saved", "Config", "*", "GameUserSettings.ini")]


def user_state(root):
    """{relative path: sha256} of save slots and GameUserSettings.ini under root, the files a test may not change."""
    import hashlib
    out = {}
    for g in STATE_GLOBS:
        for p in glob.glob(os.path.join(glob.escape(root), g), recursive=True):
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, root)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def state_check(root, before_file):
    """exit 1 if a save slot or GameUserSettings.ini was added, changed or removed since state-list."""
    try:
        with open(before_file, encoding="utf-8") as fh:
            before = dict(ln.rstrip("\n").split(" ", 1)[::-1] for ln in fh if ln.strip())
    except OSError as e:
        raise OSError(f"no state snapshot {before_file}: {e}")
    now = user_state(root)
    changed = sorted(p for p in set(before) | set(now) if before.get(p) != now.get(p))
    print(f"user state: {len(changed)} changed file(s)")
    for p in changed:
        what = "added" if p not in before else "removed" if p not in now else "changed"
        print(f"  {what}: {p}")
    if changed:
        print("FAIL: tests changed save or settings files (write under Saved/UmbrellaEllaTests and delete them)")
        return 1
    return 0


def decision_ids(root):
    try:
        with open(os.path.join(root, "docs", "decisions.md"), encoding="utf-8") as fh:
            return set(re.findall(r"^\|\s*(D[\w-]+)\s*\|", fh.read(), re.M))
    except OSError:
        return set()


def crash_dirs(exe, shell, env):
    """The folders the smoke scripts watch for new crash folders, for a step run from Python."""
    info = os.path.dirname(exe)
    for _ in range(5):
        if os.path.isfile(os.path.join(info, "BUILD_INFO.txt")):
            break
        info = os.path.dirname(info)
    if not os.path.isfile(os.path.join(info, "BUILD_INFO.txt")):
        info = os.path.dirname(exe)
    if shell == "sh":   # [VERIFY crash folders on 5.8.4], same as smoke.sh and smoke.ps1
        dirs = [info, os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Epic", "UmbrellaElla", "Saved")]
        extra = env.get("SMOKE_CRASH_DIRS", "").split(":")
    else:
        dirs = [info, os.path.join(env.get("LOCALAPPDATA", ""), "UmbrellaElla", "Saved")]
        extra = env.get("SMOKE_CRASH_DIRS", "").split(";")
    return dirs + [d for d in extra if d]


def settings_ini(shell, env):
    """The packaged game's GameUserSettings.ini. SETTINGS_INI overrides. [VERIFY packaged settings path on 5.8.4]"""
    if env.get("SETTINGS_INI"):
        return env["SETTINGS_INI"]
    if shell == "sh":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Epic", "UmbrellaElla",
                            "Saved", "Config", "Mac", "GameUserSettings.ini")
    return os.path.join(env.get("LOCALAPPDATA", ""), "UmbrellaElla", "Saved", "Config", "Windows",
                        "GameUserSettings.ini")


def host_note(env, node):
    """Not checked entry when the fps limits were not measured on the reference low-spec host (REF_HOST)."""
    ref = env.get("REF_HOST", "").strip()
    if not ref:
        return "reference host (REF_HOST not set; fps limits count only on the low-spec host)"
    if ref.lower() != node.lower():
        return f"fps on reference host {ref} (ran on {node})"
    return None


# Every entry `daily` writes under `Not checked`, one regex each (final-8 A C1, B H1). check_card.py --gate-record
# keys its rule on these names and on what each gate requires (tools/ue/daily-checklist.md, Switches by gate), not on
# keywords; an entry that is not one of these was not written by daily and fails the record.
NOT_CHECKED = {
    "alone": r"alone \(ALONE_NEW=0\)",
    "shuffle": r"shuffle \((?:SHUFFLE_TESTS=0|fewer than 2 merged test-map tests)\)",
    "input": r"input \(SMOKE_REQUIRE_INPUT=0\)",
    "gamepad": r"gamepad \(SMOKE_REQUIRE_GAMEPAD=0\)",
    "restart-cycles": r"restart cycles \(SMOKE_RESTART_CYCLES not set\)",
    "map-list": r"map list \(no GameDefaultMap or MapsToCook in Config/\*\.ini\)",
    "display-mode": r"display \d+x\d+ \w+ \(monitor \d+x\d+\)",
    "fallback-res": r"fallback res \d+x\d+ \(monitor \d+x\d+\)",
    "settings": r"settings \(SETTINGS_SMOKE=0\)",
    "settings-old-ini": r"settings old-ini \(SETTINGS_OLD_INI not set to the last gate zip's ini\)",
    "client-test": r"client-test \(CLIENT_TESTS=1 not set\)",
    "shipping-alive": r"shipping-alive \(SHIPPING_EXE not set; Shipping smoke only if D-new-smoke picks it\)",
    "verify-tags": r"real-engine pipeline \(\d+ VERIFY tag\(s\) left; ue_run\.py verify-tags\)",
    "ref-host": r"reference host \(REF_HOST not set; fps limits count only on the low-spec host\)"
                r"|fps on reference host \S+ \(ran on \S+\)",
    "bootstrap-tests": r"gameplay tests \(bootstrap: placeholder test only before card 0\.5\)",
    "bootstrap-smoke": r"smoke contract \(bootstrap: no smoke hook before card 0\.6; alive run only\)",
    "art-bootstrap": r"art checks \(no anchor art before card 0\.10b; shot results not blocking\)",
    "workbench": r"workbench package \(no Source/UmbrellaEllaWorkbench\.Target\.cs yet\)",
}


def not_checked_entries(text):
    """Split a DAILY line's `Not checked:` text into entries (commas inside parentheses stay in one entry)."""
    out, depth, cur = [], 0, ""
    for ch in (text or "").strip():
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [] if out == ["none"] else out


def not_checked_kind(entry):
    """The NOT_CHECKED name of one entry, or None when daily never writes it."""
    for name, rx in NOT_CHECKED.items():
        if re.fullmatch(rx, entry.strip()):
            return name
    return None


RECORD = os.path.join("Saved", "Logs", "pipeline", "daily-records.txt")
TEST_LINE = re.compile(r"\b(PASS|FAIL)\s+tests=(\d+) failed=(\d+)")
STEPS = ["clean-tree", "build", "test", "alone", "shuffle", "validate", "package", "smoke", "display", "settings",
         "client-test", "shipping-alive", "workbench"]
WORKBENCH_TARGET = os.path.join("Source", "UmbrellaEllaWorkbench.Target.cs")
GARBAGE_INI = "\x00\xff[[[ not an ini\n=broken=\n[/Script/Engine.GameUserSettings\nFullscreenMode=banana\n"
ALONE_FILE = os.path.join("Saved", "Logs", "pipeline", "alone-passed.txt")
COOK_WARN = re.compile(r"\bcook warnings: (\d+)")
VALIDATE_LINE = re.compile(r"\bvalidate: errors=(\d+) warnings=(\d+)")


def last_baseline(record):
    try:
        with open(record, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return 0
    for ln in reversed(lines):
        m = re.search(r"\btest=PASS\((\d+)/(\d+)/(\d+)\)", ln)
        if m:
            return int(m.group(3))
    return 0


def ancestry_baseline(root, record):
    """Final-9 A H3: the test-count baseline is the record of the nearest commit in HEAD's own history (HEAD itself
    included), not the last line on this machine, so a daily on an older commit (backfill) or on another branch
    never inherits a later count. The tests that commit's test map required (merged rows) and HEAD's no longer
    names lower it: a revert of a card takes its rows back to planned, so the revert's daily is green. A test that
    vanishes while its row stays merged still fails (check_automation_report --test-map)."""
    try:
        with open(record, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return 0
    p = git(root, "rev-list", "HEAD")
    if p.returncode != 0:
        return last_baseline(record)
    ancestors = p.stdout.split()   # nearest first: HEAD, its parent, ...
    daily = []   # (sha, count) per DAILY test=PASS line, newest last
    for ln in lines:
        m = re.search(r"\btest=PASS\((\d+)/(\d+)/(\d+)\)", ln)
        if m and ln.startswith("DAILY "):
            daily.append((ln.split()[1].split("+")[0], int(m.group(3))))
    # Final-10 B H5: the nearest ancestor commit that has a line wins (its newest line), whatever order the lines
    # were written in: a backfill line for an older commit never replaces the count of a nearer one.
    for hit in ancestors:
        counts = [c for sha, c in daily if len(sha) >= 7 and hit.startswith(sha)]
        if not counts:
            continue
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import check_automation_report as car
        then = git(root, "show", f"{hit}:pipeline/qa/test-map.md")
        try:
            with open(os.path.join(root, "pipeline", "qa", "test-map.md"), encoding="utf-8") as fh:
                now = set(car.test_map_requirements(fh.read())[0])
        except OSError:
            now = set()
        gone = set(car.test_map_requirements(then.stdout)[0]) - now if then.returncode == 0 else set()
        return max(0, counts[-1] - len(gone))
    return 0


def last_cook_warnings(record):
    """Cook warning count of the last DAILY line whose package step passed, or None."""
    try:
        with open(record, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    for ln in reversed(lines):
        m = re.search(r"\bpackage=PASS\(warn (\d+)", ln)
        if m:
            return int(m.group(1))
    return None


SMOKE_HOOK_DIR = "Source/UmbrellaElla/Private/Smoke"   # card 0.6
TESTS_META_DIR = "Source/UmbrellaElla/Private/Tests/Meta"   # card 0.5


def smoke_hook_exists(root, changed=()):
    """Card 0.6's smoke hook is in the tree (or a change adds it). Fail-closed (dry run B M8): any Source/ file that
    writes SMOKE_OK counts too, so moving or renaming the folder never reopens a bootstrap."""
    if any(p.strip().lstrip("./").startswith(SMOKE_HOOK_DIR + "/") for p in (changed or [])):
        return True
    if os.path.isdir(os.path.join(root, SMOKE_HOOK_DIR)):
        return True
    for d, _, files in os.walk(os.path.join(root, "Source")):
        for f in files:
            if f.endswith((".cpp", ".h")):
                try:
                    with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                        if "SMOKE_OK" in fh.read():
                            return True
                except OSError:
                    continue
    return False


def tests_bootstrap(root):
    """Before card 0.5 (no Tests/Meta/ folder) only card 0.3's placeholder test exists. check_automation_report
    --bootstrap itself fails once any other UmbrellaElla test runs, so the waiver ends by itself (final-8 A H7)."""
    return not os.path.isdir(os.path.join(root, TESTS_META_DIR))


def daily(root, shell, allow_dirty=False, env=None):
    env = dict(os.environ if env is None else env)
    logdir = os.path.join(root, "Saved", "Logs", "pipeline")
    os.makedirs(logdir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    record = os.path.join(root, RECORD)
    test_map = os.path.join(root, "pipeline", "qa", "test-map.md")
    result, not_checked = {}, []
    rule_s = env.get("RULE_MAX_SECONDS", "1.0")

    def script(name, args, step, extra=None):
        path = os.path.join(root, "tools", "ue", f"{name}.{shell}")
        cmd = (["bash", path] if shell == "sh" else
               ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path]) + args
        e = dict(env, **(extra or {}))
        log = os.path.join(logdir, f"daily-{stamp}-{step}.log")
        print(f"== daily: {step}: {' '.join(cmd[-len(args) - 1:])} {' '.join(f'{k}={v}' for k, v in (extra or {}).items())}", flush=True)
        rc = run(cmd, 0, log, env=e)
        with open(log, encoding="utf-8", errors="replace") as fh:
            return rc, fh.read()

    exe = env.get("SMOKE_EXE") or os.path.join(root, "Packaged", *(
        ["Mac", "UmbrellaElla.app", "Contents", "MacOS", "UmbrellaElla"] if shell == "sh"
        else ["Windows", "UmbrellaElla.exe"]))   # [VERIFY the packaged path on 5.8.4]
    smoke_args = [exe] if shell == "sh" else ["-Exe", exe]
    default_map, map_list = maps(root)

    def step_clean():
        return clean_tree(root, allow_dirty), ""

    def step_build():
        # Non-unity (-DisableUnity -NoPCH -NoSharedPCH), so a missing include fails the daily build.
        if shell == "sh":
            return script("build", [], "build", {"NONUNITY": "1"})[0], ""
        return script("build", ["-NonUnity"], "build")[0], ""

    boot_tests, boot_smoke = tests_bootstrap(root), not smoke_hook_exists(root)
    if not boot_smoke and art_bootstrap(root):
        not_checked.append("art checks (no anchor art before card 0.10b; shot results not blocking)")

    def step_test():
        base = ancestry_baseline(root, record)
        if boot_tests:
            # Day-1 bootstrap (final-8 A H7), scoped like check_pr's SMOKE_BOOTSTRAP: from the card 0.3 merge until
            # card 0.5 adds Tests/Meta/, the placeholder test is the only test, so the run uses --bootstrap.
            not_checked.append("gameplay tests (bootstrap: placeholder test only before card 0.5)")
            rc, out = script("test", ["--bootstrap"] if shell == "sh" else ["-Bootstrap"], "test")
            m = None
            for m in TEST_LINE.finditer(out):
                pass
            if m:
                total, failed = int(m.group(2)), int(m.group(3))
                return rc, f"({total - failed}/{failed}/{total}, bootstrap)"
            return (rc or 1), "(no report)"
        if shell == "sh":
            rc, out = script("test", ["--test-map", test_map, "--max-rule-seconds", rule_s], "test", {"BASELINE": str(base)})
        else:
            rc, out = script("test", ["-Baseline", str(base), "-TestMap", test_map, "-MaxRuleSeconds", rule_s], "test")
        m = None
        for m in TEST_LINE.finditer(out):
            pass
        if m:
            total, failed = int(m.group(2)), int(m.group(3))
            return rc, f"({total - failed}/{failed}/{total})"
        return (rc or 1), "(no report)"

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_automation_report as car

    def step_alone():
        """Each merged test-map test that has not yet passed alone on this machine runs alone once."""
        if env.get("ALONE_NEW", "1") == "0":
            not_checked.append("alone (ALONE_NEW=0)")
            return None, ""
        try:
            with open(test_map, encoding="utf-8") as fh:
                names, problems = car.test_map_requirements(fh.read())
        except OSError:
            names, problems = [], ["no test map"]
        if problems:
            print("alone: test map problems: " + "; ".join(problems))
            return 1, "(test map)"
        done_file = os.path.join(root, ALONE_FILE)
        try:
            with open(done_file, encoding="utf-8") as fh:
                done = {ln.strip() for ln in fh if ln.strip()}
        except OSError:
            done = set()
        new = [n for n in names if n not in done]
        for n in new:
            args = (["--require", n, "--max-rule-seconds", "0"] if shell == "sh"
                    else ["-Filter", n, "-Require", n, "-MaxRuleSeconds", "0"])
            rc = script("test", args, "alone-" + n, {"TEST_FILTER": n})[0]
            if rc:
                return rc, f"({n})"
            with open(done_file, "a", encoding="utf-8") as fh:
                fh.write(n + "\n")
        return 0, f"({len(new)} new)"

    def step_shuffle():
        """The merged test-map tests again, in a shuffled order with a logged seed. Any failure fails."""
        if env.get("SHUFFLE_TESTS", "1") == "0":
            not_checked.append("shuffle (SHUFFLE_TESTS=0)")
            return None, ""
        try:
            with open(test_map, encoding="utf-8") as fh:
                names = car.test_map_requirements(fh.read())[0]
        except OSError:
            names = []
        if len(names) < 2:
            not_checked.append("shuffle (fewer than 2 merged test-map tests)")
            return None, ""
        import random
        seed = env.get("SHUFFLE_SEED") or str(random.randrange(10 ** 6))
        order = list(names)
        random.Random(seed).shuffle(order)
        print(f"shuffle: seed={seed} order={' '.join(order)}")
        filt = "+".join(order)   # RunTests with a + list, run in this order [VERIFY on 5.8.4]
        args = (["--test-map", test_map, "--max-rule-seconds", "0"] if shell == "sh"
                else ["-Filter", filt, "-TestMap", test_map, "-MaxRuleSeconds", "0"])
        rc = script("test", args, "shuffle", {"TEST_FILTER": filt})[0]
        return rc, f"(seed {seed}, {len(order)} tests)"

    def step_validate():
        rc, out = script("validate", [], "validate")
        m = None
        for m in VALIDATE_LINE.finditer(out):
            pass
        if not m:
            return (rc or 1), "(no validate line)"
        return rc, f"(err {m.group(1)}, warn {m.group(2)})"

    def step_package():
        args = (["--allow-dirty"] if shell == "sh" else ["-AllowDirty"]) if allow_dirty else []
        before = last_cook_warnings(record)
        rc, out = script("package", args, "package")
        found = COOK_WARN.findall(out)
        if rc:
            return rc, ""
        if not found:
            print("FAIL: package log has no 'cook warnings: N' line")
            return 1, "(no warning count)"
        warn = int(found[-1])
        if before is not None and warn > before:
            why = env.get("COOK_WARN_DECISION", "")
            if why and why in decision_ids(root):
                return 0, f"(warn {warn}, up from {before} by {why})"
            print(f"FAIL: cook warnings rose from {before} to {warn}. Fix them, or set COOK_WARN_DECISION=<id> "
                  "to a row in docs/decisions.md that accepts them.")
            return 1, f"(warn {warn}, up from {before})"
        return 0, f"(warn {warn})"

    cycles = env.get("SMOKE_RESTART_CYCLES", "0")
    if env.get("SMOKE_REQUIRE_INPUT", "1") == "0":
        not_checked.append("input (SMOKE_REQUIRE_INPUT=0)")
    if env.get("SMOKE_REQUIRE_GAMEPAD", "1") == "0":
        not_checked.append("gamepad (SMOKE_REQUIRE_GAMEPAD=0)")
    if cycles in ("", "0"):
        not_checked.append("restart cycles (SMOKE_RESTART_CYCLES not set)")

    try:
        repeat = max(1, int(env.get("SMOKE_REPEAT", "1")))
    except ValueError:
        repeat = 1

    def step_smoke():
        """Every map once; the first (GameDefaultMap) SMOKE_REPEAT times. Any crash in any repeat fails."""
        if boot_smoke:
            # Day-1 bootstrap (final-8 A H7): before card 0.6 there is no hook to print SMOKE_OK or quit, so the
            # package is only run alive (still running at 15 s, closes with exit 0, no new crash folder). Display
            # and settings need SMOKE_OK and do not run. A gate record never accepts this line (no map count).
            not_checked.append("smoke contract (bootstrap: no smoke hook before card 0.6; alive run only)")
            rc = script("smoke", smoke_args + ([] if shell == "sh" else ["-Alive"]), "smoke-alive",
                        {"SMOKE_MODE": "alive"})[0]
            return rc, "(bootstrap alive)"
        if not map_list:
            not_checked.append("map list (no GameDefaultMap or MapsToCook in Config/*.ini)")
            for i in range(1, repeat + 1):
                rc = script("smoke", smoke_args, f"smoke-r{i}", {"SMOKE_RESTART_CYCLES": cycles})[0]
                if rc:
                    return rc, f"(no map list, repeat {i - 1}/{repeat})"
        for n, m in enumerate(map_list):
            extra = {"SMOKE_MAP": short_map(m), "SMOKE_RESTART_CYCLES": cycles}
            if m != default_map:
                extra["SMOKE_GAME_MAP"] = m   # needs the -SmokeMap switch (card 0.6) [VERIFY]
            for i in range(1, (repeat if n == 0 else 1) + 1):
                rc = script("smoke", smoke_args, f"smoke-{short_map(m)}" + (f"-r{i}" if n == 0 and repeat > 1 else ""),
                            extra)[0]
                if rc:
                    return rc, f"({short_map(m)}" + (f", repeat {i - 1}/{repeat})" if n == 0 and repeat > 1 else ")")
        # No section smoke: the game is one arena (D-new-cut5).
        maps_note = f"{len(map_list)} map(s)" if map_list else "no map list"
        if repeat > 1:
            maps_note += f", repeat {repeat}/{repeat}"
        return 0, f"({maps_note})"

    def step_display():
        if boot_smoke:
            return None, ""
        modes = [x for x in env.get("SMOKE_DISPLAY_MODES", DISPLAY_MODES).split(",") if x.strip()]
        desk = desktop_res(env)
        ran = 0
        for mode in modes:
            res, _, win = mode.strip().partition(":")
            win = win or "windowed"
            size = [int(v) for v in re.findall(r"\d+", res)][:2]
            if desk and len(size) == 2 and (size[0] > desk[0] or size[1] > desk[1]):
                not_checked.append(f"display {res} {win} (monitor {desk[0]}x{desk[1]})")
                continue
            ran += 1
            rc = script("smoke", smoke_args, f"display-{res}-{win}", {"SMOKE_RES": res, "SMOKE_WINDOW": win})[0]
            if rc:
                return rc, f"({res} {win})"
        if not ran:
            return 1, "(no mode fits the monitor)"
        return 0, f"({ran} mode(s))"

    def step_settings():
        """GameDefaultMap smoke with a garbage GameUserSettings.ini, then with SETTINGS_OLD_INI (the ini from the
        last gate zip). Each must reach SMOKE_OK. The real ini is put back after."""
        if boot_smoke:
            return None, ""
        if env.get("SETTINGS_SMOKE", "1") == "0":
            not_checked.append("settings (SETTINGS_SMOKE=0)")
            return None, ""
        ini = settings_ini(shell, env)
        variants = [("garbage", GARBAGE_INI)]
        old = env.get("SETTINGS_OLD_INI", "")
        if old and os.path.isfile(old):
            with open(old, encoding="utf-8", errors="replace") as fh:
                variants.append(("old", fh.read()))
        else:
            not_checked.append("settings old-ini (SETTINGS_OLD_INI not set to the last gate zip's ini)")
        saved = None
        if os.path.isfile(ini):
            with open(ini, "rb") as fh:
                saved = fh.read()
        extra = {"SMOKE_MAP": short_map(default_map)} if default_map else {}
        desk = desktop_res(env)
        if not desk or (desk[0] >= 1920 and desk[1] >= 1080):
            extra["SMOKE_EXPECT_RES"] = FALLBACK_RES   # a garbage or old ini falls back to 1920x1080
        else:
            not_checked.append(f"fallback res {FALLBACK_RES} (monitor {desk[0]}x{desk[1]})")
        try:
            for name, text in variants:
                os.makedirs(os.path.dirname(os.path.abspath(ini)), exist_ok=True)
                with open(ini, "w", encoding="utf-8") as fh:
                    fh.write(text)
                rc = script("smoke", smoke_args, f"settings-{name}", extra)[0]
                if rc:
                    return rc, f"({name} ini)"
        finally:
            if saved is None:
                try:
                    os.remove(ini)
                except OSError:
                    pass
            else:
                with open(ini, "wb") as fh:
                    fh.write(saved)
        return 0, f"({'+'.join(n for n, _ in variants)} ini)"

    def step_client():
        if env.get("CLIENT_TESTS", "0") != "1":
            not_checked.append("client-test (CLIENT_TESTS=1 not set)")
            return None, ""
        report = os.path.join(root, "Saved", "AutomationClient")
        shutil.rmtree(report, ignore_errors=True)
        log = os.path.join(logdir, f"daily-{stamp}-client-test.log")
        game_log = os.path.join(logdir, f"daily-{stamp}-client-test-game.log")
        dirs = crash_dirs(exe, shell, env)
        before = crash_list(dirs)
        snap = os.path.join(logdir, f"daily-{stamp}-client-test-crashes-before.txt")
        with open(snap, "w", encoding="utf-8") as fh:
            fh.write("".join(p + "\n" for p in sorted(before)))
        print("== daily: client-test", flush=True)
        rc = run([exe, "-ExecCmds=Automation RunTests UmbrellaElla.Flow;Quit", f"-ReportExportPath={report}",
                  "-log", f"-abslog={game_log}", "-unattended"],
                 int(env.get("CLIENT_TIMEOUT", "600")), log, env=env)   # [VERIFY on 5.8.4]
        if rc == TIMEOUT_RC:
            return rc, "(timeout)"
        text = ""
        for f in (log, game_log):
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    text += fh.read() + "\n"
            except OSError:
                pass
        fails = []
        if rc != 0:
            fails.append(f"exit code {rc}")
        if not os.path.isfile(game_log):
            fails.append(f"no -abslog file at {game_log}")
        try:
            allow = load_allow(os.path.join(root, "tools", "ue", "smoke-allow.txt"),
                               os.path.join(root, "docs", "decisions.md"))
        except ValueError as e:
            print(f"FAIL: {e}")
            return 2, "(allow file)"
        counts = smoke_counts(text, allow)
        fails += [f"{v} '{k}' line(s)" for k, v in counts.items() if v]
        # Packaged flow tests are world tests: no 1 s rule-test limit here.
        car_rc = car.main([os.path.join(report, "index.json"), "--require", CLIENT_TEST,
                           "--max-rule-seconds", "0"])
        if car_rc:
            fails.append("automation report")
        cr = crash_check(snap, dirs)
        if cr:
            fails.append("new crash folder")
        if fails:
            print("FAIL: client-test: " + "; ".join(fails))
            return 1, ""
        return 0, ""

    def step_shipping():
        ship = env.get("SHIPPING_EXE")
        if not ship:
            if env.get("SHIPPING_REQUIRED", "0") == "1":
                print("FAIL: SHIPPING_REQUIRED=1 (from Day 3) but SHIPPING_EXE is not set")
                return 1, "(SHIPPING_EXE not set)"
            not_checked.append("shipping-alive (SHIPPING_EXE not set; Shipping smoke only if D-new-smoke picks it)")
            return None, ""
        args = [ship] if shell == "sh" else ["-Exe", ship, "-Alive"]
        rc, out = script("smoke", args, "shipping-alive",
                         {"SMOKE_MODE": "alive", "SMOKE_MAX_BOOT_S": env.get("SMOKE_MAX_BOOT_S", "20")})
        m = re.findall(r"\bboot_s=(\S+)", out)
        return rc, f"(boot_s={m[-1]})" if m else ""

    def step_workbench():
        """After the Development package and its smoke pass: the tester package (package -Workbench / WORKBENCH=1)
        into Packaged-Workbench, so testers get a build of the same commit. Not run before its Target.cs exists."""
        if not os.path.isfile(os.path.join(root, WORKBENCH_TARGET)):
            not_checked.append(f"workbench package (no {WORKBENCH_TARGET.replace(os.sep, '/')} yet)")
            return None, ""
        args = ["--workbench"] if shell == "sh" else ["-Workbench"]
        if allow_dirty:
            args.append("--allow-dirty" if shell == "sh" else "-AllowDirty")
        rc, out = script("package", args, "workbench", {"WORKBENCH": "1"})
        if rc:
            return rc, ""
        if not re.search(r"^package exit: 0 .*target=UmbrellaEllaWorkbench", out, re.M):
            print("FAIL: workbench package log has no `package exit: 0 ... target=UmbrellaEllaWorkbench` line")
            return 1, "(no package line)"
        found = COOK_WARN.findall(out)
        return 0, f"(warn {found[-1]})" if found else ""

    tags = verify_tags(root)
    if tags:
        not_checked.insert(0, f"real-engine pipeline ({len(tags)} VERIFY tag(s) left; ue_run.py verify-tags)")
    host = host_note(env, platform.node())
    if host:
        not_checked.append(host)
    fns = dict(zip(STEPS, [step_clean, step_build, step_test, step_alone, step_shuffle, step_validate, step_package,
                           step_smoke, step_display, step_settings, step_client, step_shipping, step_workbench]))
    first_rc = 0
    for name in STEPS:
        if first_rc:
            result[name] = "not run"
            continue
        rc, note = fns[name]()
        if rc is None:
            result[name] = "NOT RUN"
            continue
        result[name] = ("PASS" if rc == 0 else "FAIL") + note
        if rc:
            first_rc = rc
    commit = git(root, "rev-parse", "--short", "HEAD").stdout.strip() or "unknown"
    try:
        if dirty_lines(root):
            commit += "+dirty"   # merge-check never counts a dirty run
    except OSError:
        pass
    line = (f"DAILY {commit} | {platform.node()}/{platform.system()} {platform.release()} | Development | "
            + " ".join(f"{k}={v}" for k, v in result.items())
            + f" | Not checked: {', '.join(not_checked) or 'none'}")
    with open(record, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)
    return first_rc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--timeout", type=int, required=True)
    r.add_argument("--log", required=True)
    r.add_argument("command", nargs=argparse.REMAINDER)
    al = sub.add_parser("alive")
    al.add_argument("--seconds", type=float, default=15)
    al.add_argument("--close-timeout", type=float, default=30)
    al.add_argument("--max-boot-s", type=float, default=0, help="first window within S s (Windows; prints boot_s=)")
    al.add_argument("--log", required=True)
    al.add_argument("command", nargs=argparse.REMAINDER)
    c = sub.add_parser("clean-tree")
    c.add_argument("--allow-dirty", action="store_true")
    b = sub.add_parser("build-info")
    b.add_argument("--out", required=True)
    b.add_argument("--config", required=True)
    b.add_argument("--target")
    b.add_argument("--workbench", choices=["0", "1"])
    b.add_argument("--commit", help="the commit the package script stamped at build start (final-9 B H5)")
    sub.add_parser("workbench-check")
    lr = sub.add_parser("launch-record")
    lr.add_argument("log", nargs="+")
    lr.add_argument("--zip", required=True)
    lr.add_argument("--exe", help="the smoked exe: it must be a file of the zip (final-10 B H2)")
    lr.add_argument("--record")
    s = sub.add_parser("smoke-log")
    s.add_argument("log", nargs="+")
    s.add_argument("--exit-code", type=int, required=True)
    s.add_argument("--expect-map")
    s.add_argument("--expect-commit")
    s.add_argument("--min-fps", type=float, default=MIN_FPS)
    s.add_argument("--expect-res")
    s.add_argument("--expect-win")
    s.add_argument("--min-text-px", type=float, default=0)
    s.add_argument("--max-frame-ms", type=float, default=MAX_FRAME_MS)
    s.add_argument("--no-input-check", action="store_true")
    s.add_argument("--no-gamepad-check", action="store_true")
    s.add_argument("--no-player-maps", default=None, help="default: pipeline/qa/no-player-maps.txt")
    s.add_argument("--expect-section")
    s.add_argument("--restart-cycles", type=int, default=0)
    s.add_argument("--allow", default=ALLOW_FILE)
    s.add_argument("--max-load-ms", type=float, default=MAX_LOAD_MS)
    s.add_argument("--expect-workbench", choices=["0", "1"])
    s.add_argument("--expect-aspect", default=ASPECT, help="W:H of the gameplay view (default 16:9); off = not checked")
    s.add_argument("--aspect-tol", type=float, default=ASPECT_TOL)
    s.add_argument("--expect-debugdraw", default="0", choices=["0", "1", "off"])
    s.add_argument("--shot", help="the -SmokeShot= screenshot: art_check.py and screen_check.py run on it")
    mc = sub.add_parser("merge-check")
    mc.add_argument("--since", required=True)
    mc.add_argument("--record")
    mc.add_argument("--require-client", action="store_true", help="from G2: client-test=PASS too")
    sub.add_parser("verify-tags")
    st = sub.add_parser("stress-check")
    st.add_argument("--commit", default="HEAD")
    st.add_argument("--record")
    for kind in ("playthrough", "shipping"):
        h = sub.add_parser(kind + "-check")
        h.add_argument("--commit", default="HEAD")
        h.add_argument("--record")
        if kind == "playthrough":
            h.add_argument("--gate", choices=sorted(PLAYTHROUGH_DUE), help="check only the fields due at this gate")
    sl = sub.add_parser("state-list")
    sl.add_argument("--out", required=True)
    sc = sub.add_parser("state-check")
    sc.add_argument("--before", required=True)
    cl = sub.add_parser("crash-list")
    cl.add_argument("dirs", nargs="*")
    cl.add_argument("--out", required=True)
    cc = sub.add_parser("crash-check")
    cc.add_argument("dirs", nargs="*")
    cc.add_argument("--before", required=True)
    sub.add_parser("maps")
    d = sub.add_parser("daily")
    d.add_argument("--shell", choices=["sh", "ps1"], required=True)
    d.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd in ("run", "alive"):
            cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
            if not cmd:
                print(f"ue_run {a.cmd}: no command given", file=sys.stderr)
                return 2
            if a.cmd == "alive":
                return alive(cmd, a.seconds, a.close_timeout, a.log, a.max_boot_s)
            return run(cmd, a.timeout, a.log)
        if a.cmd == "clean-tree":
            return clean_tree(a.root, a.allow_dirty)
        if a.cmd == "build-info":
            build_info(a.root, a.out, a.config, target=a.target, workbench=a.workbench, commit=a.commit)
            return 0
        if a.cmd == "workbench-check":
            probs = workbench_check(a.root)
            for p in probs:
                print("FAIL: " + p)
            print(f"workbench-check: {'FAIL' if probs else 'PASS'} " + (f"{len(probs)} problem(s)" if probs else
                  f"{SUBMIT_TARGET}.Target.cs sets {WORKBENCH_DEFINE}=0"))
            return 1 if probs else 0
        if a.cmd == "launch-record":
            return launch_record(a.root, a.zip, a.log, a.record or os.path.join(a.root, RECORD), a.exe)
        if a.cmd == "crash-list":
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write("".join(p + "\n" for p in sorted(crash_list(a.dirs))))
            return 0
        if a.cmd == "crash-check":
            return crash_check(a.before, a.dirs)
        if a.cmd == "maps":
            for m in maps(a.root)[1]:
                print(m)
            return 0
        if a.cmd == "daily":
            return daily(a.root, a.shell, a.allow_dirty)
        if a.cmd == "merge-check":
            return merge_check(a.root, a.since, a.record or os.path.join(a.root, RECORD), a.require_client)
        if a.cmd == "verify-tags":
            tags = verify_tags(a.root)
            for f, i, ln in tags:
                print(f"{f}:{i}: {ln}")
            print(f"verify-tags: {len(tags)} open tag(s)" + ("" if tags else "; real-engine pipeline is verified"))
            return 1 if tags else 0
        if a.cmd in ("stress-check", "playthrough-check", "shipping-check"):
            return hand_check(a.root, a.commit, a.record or os.path.join(a.root, RECORD), a.cmd.split("-")[0].upper(),
                              getattr(a, "gate", None))
        if a.cmd == "state-list":
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write("".join(f"{h} {p}\n" for p, h in sorted(user_state(a.root).items())))
            return 0
        if a.cmd == "state-check":
            return state_check(a.root, a.before)
        allow = load_allow(a.allow, os.path.join(a.root, "docs", "decisions.md"))
        return smoke_log(a.log, a.exit_code, a.expect_map, a.expect_commit, a.min_fps, a.expect_res,
                         a.expect_win, a.min_text_px, a.max_frame_ms, not a.no_input_check,
                         no_player_maps(a.root) if a.no_player_maps is None else a.no_player_maps,
                         a.expect_section, a.restart_cycles, allow, a.max_load_ms, a.expect_workbench, root=a.root,
                         require_gamepad=not a.no_gamepad_check,
                         expect_aspect=None if a.expect_aspect == "off" else a.expect_aspect, aspect_tol=a.aspect_tol,
                         expect_debugdraw=None if a.expect_debugdraw == "off" else a.expect_debugdraw, shot=a.shot)
    except (OSError, ValueError) as e:
        print(f"ue_run: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
