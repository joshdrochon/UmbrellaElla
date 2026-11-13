#!/usr/bin/env python3
"""API keys for the asset tools, read only from the environment or the OS keychain. Never from a file in the repo,
never printed. Stdlib only.

Keys (pipeline/agent-ops/asset-tools.json `keys`): ELEVENLABS_API_KEY (ElevenLabs Sound Effects / Music),
STABILITY_API_KEY (Stable Audio); image model keys (D-new-art-image-model, tools/assetgen.py image): GEMINI_API_KEY
(default provider), OPENAI_API_KEY (optional). Blender art needs no key. Lookup order:
  1. the environment variable of that name;
  2. macOS Keychain: `security find-generic-password -s umbrella-ella -a <NAME> -w`
     (set once: `security add-generic-password -s umbrella-ella -a ELEVENLABS_API_KEY -w`);
  3. Windows Credential Manager / Linux Secret Service through the `keyring` package when it is installed
     (set once: `python -m keyring set umbrella-ella ELEVENLABS_API_KEY`).
KEYS_NO_KEYCHAIN=1 skips 2 and 3 (tests). Agent sessions never get the keys: tools/kickoff.py strips them from every
session's environment and runs the API steps itself (tools/assetgen.py fulfil).

  python3 tools/keys.py status      one line per key: `present (env|keychain)` or `missing -> <how to set it>`
"""
import os
import platform
import subprocess
import sys

SERVICE = "umbrella-ella"
KEYS = {
    "ELEVENLABS_API_KEY": "ElevenLabs Sound Effects / Music",
    "STABILITY_API_KEY": "Stability AI (Stable Audio)",
}
# Image model keys (D-new-art-image-model). Kept apart from KEYS so tools/connections.py --live (which pings every
# KEYS entry) is not handed a key it has no ping for (docs/build/requests/imagegen.md); status and scrub cover both.
IMAGE_KEYS = {
    "GEMINI_API_KEY": "Gemini API image generation (default image provider)",
    "OPENAI_API_KEY": "OpenAI Images (optional image provider)",
    "OPENROUTER_API_KEY": "OpenRouter (second provider for the same Google image models, own spend cap)",
}


def _keychain(name):
    if os.environ.get("KEYS_NO_KEYCHAIN") == "1":
        return None
    if platform.system() == "Darwin":
        try:
            r = subprocess.run(["security", "find-generic-password", "-s", SERVICE, "-a", name, "-w"],
                               capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        import keyring  # optional; Windows Credential Manager, Linux Secret Service
        return keyring.get_password(SERVICE, name) or None
    except Exception:
        return None


def clean(v):
    """A key as pasted: surrounding whitespace (CR, newline) and one pair of matching quotes removed."""
    v = (v or "").strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1].strip()
    return v


def lookup(name):
    """(value, where) with where 'env' | 'keychain', or (None, None). The value is never printed."""
    v = clean(os.environ.get(name))
    if v:
        return v, "env"
    v = clean(_keychain(name))
    return (v, "keychain") if v else (None, None)


def get(name):
    return lookup(name)[0]


def how_to_set(name):
    return (f"set {name} once: export {name}=... (PowerShell: setx {name} ...), or the keychain: "
            f"security add-generic-password -s {SERVICE} -a {name} -w (Windows: python -m keyring set {SERVICE} {name})")


def status_lines():
    out = []
    for name, what in {**KEYS, **IMAGE_KEYS}.items():
        _, where = lookup(name)
        out.append(f"{name} ({what}): " + (f"present ({where})" if where else "missing -> " + how_to_set(name)))
    return out


# Never handed to a session either: the image keys, and any other vendor key a machine may hold
SCRUB_ALSO = tuple(IMAGE_KEYS)


def scrub(env):
    """A copy of env without any key (agent sessions never hold them)."""
    return {k: v for k, v in env.items() if k not in KEYS and k not in SCRUB_ALSO}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] != ["status"]:
        print(__doc__)
        return 2
    for ln in status_lines():
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
