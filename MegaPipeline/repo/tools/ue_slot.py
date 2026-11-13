#!/usr/bin/env python3
"""Engine slots: at most UE_SLOTS (default 2) Unreal runs at once on one machine, however many sessions run. Stdlib.

tools/ue_run.py `run` holds a slot for every engine command (UBT build, automation tests, UAT package, smoke), so
tools/ue/*.sh and *.ps1 take one with no change, and so does every parallel kickoff session or area worker.
A slot is a folder <dir>/slot<N> holding the owner's PID; a slot whose owner died is taken over. UE_SLOT_DIR sets
<dir> (default: <temp>/umbrellaella-ue-slots-py, one per machine), UE_SLOTS=0 turns slots off, and a command run
inside a slot (UE_SLOT_HELD set) never waits for a second one.

Usage: python3 tools/ue_slot.py run -- <command...>    run one command inside a slot (exit = its exit code)
       python3 tools/ue_slot.py status                 who holds each slot
"""
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
import time

POLL = float(os.environ.get("UE_SLOT_POLL", "5"))


def slots():
    try:
        return max(0, int(os.environ.get("UE_SLOTS", "2")))
    except ValueError:
        return 2


def slot_dir():
    return os.environ.get("UE_SLOT_DIR") or os.path.join(tempfile.gettempdir(), "umbrellaella-ue-slots-py")


def alive(pid):
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259   # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def owner(path):
    try:
        with open(os.path.join(path, "owner"), encoding="utf-8") as fh:
            return int(fh.read().split()[0])
    except (OSError, ValueError, IndexError):
        return -1


def try_take(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        if not alive(owner(path)) and time.time() - os.path.getmtime(path) > 2:
            shutil.rmtree(path, ignore_errors=True)   # its owner died: free it, take it on the next pass
        return False
    with open(os.path.join(path, "owner"), "w", encoding="utf-8") as fh:
        fh.write(f"{os.getpid()} {os.getcwd()}\n")
    return True


@contextlib.contextmanager
def slot(label="", say=lambda m: print(m, file=sys.stderr, flush=True)):
    """Hold one engine slot for the with-block (no-op when slots are off or one is already held)."""
    n = slots()
    if n == 0 or os.environ.get("UE_SLOT_HELD"):
        yield None
        return
    d = slot_dir()
    os.makedirs(d, exist_ok=True)
    told = False
    while True:
        for i in range(1, n + 1):
            path = os.path.join(d, f"slot{i}")
            if try_take(path):
                os.environ["UE_SLOT_HELD"] = path
                try:
                    yield path
                finally:
                    os.environ.pop("UE_SLOT_HELD", None)
                    shutil.rmtree(path, ignore_errors=True)
                return
        if not told:
            say(f"ue_slot: all {n} engine slots are busy (UE_SLOTS); waiting for one: {label}")
            told = True
        time.sleep(POLL)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["status"]:
        d = slot_dir()
        for i in range(1, slots() + 1):
            p = os.path.join(d, f"slot{i}")
            print(f"slot{i}: " + (f"pid {owner(p)} ({'alive' if alive(owner(p)) else 'dead'})" if os.path.isdir(p) else "free"))
        return 0
    if argv[:1] == ["run"]:
        cmd = argv[2:] if argv[1:2] == ["--"] else argv[1:]
        if not cmd:
            print("usage: ue_slot.py run -- <command...>", file=sys.stderr)
            return 2
        with slot(" ".join(cmd)):
            return subprocess.call(cmd)
    print(__doc__.strip().splitlines()[-2], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
