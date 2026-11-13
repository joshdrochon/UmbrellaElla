> Generated from `pipeline/unreal/commands-and-packaging.md`, `.github/workflows/pipeline-checks.yml`, `.github/CODEOWNERS.example`, `tools/pipeline_check.py`, `tools/affected_tests.py`, `tools/module_check.py`, `tools/ue_run.py`, `tools/ue/common.ps1`, `tools/ue/common.sh`, `tools/ue/build.ps1`, `tools/ue/build.sh`, `tools/ue/validate.ps1`, `tools/ue/validate.sh`, `tools/export_package.py` at `b201a66` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Technical Development Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Own modules, build scripts, config, plugins and the repo guardrails that every other lane relies on.
- **Owner:** Technical Director (agent role plus the TD human).
- **Inputs:** Day-0 skeleton cards, `pipeline/unreal-rules.md`, engine logs.
- **Outputs:** Build and validate scripts, module boundaries, CI checks, this package's exporter.
- **Gates:** `pipeline_check.py` and the unit tests in CI; `module_check.py` once `Source/` exists; local compile logs in the PR.

## Built from

- Commands and packaging: `pipeline/unreal/commands-and-packaging.md`
- CI and repo settings: `.github/workflows/pipeline-checks.yml`, `.github/CODEOWNERS.example`
- Commands and checks: `tools/pipeline_check.py`, `tools/affected_tests.py`, `tools/module_check.py`, `tools/ue_run.py`, `tools/ue/common.ps1`, `tools/ue/common.sh`, `tools/ue/build.ps1`, `tools/ue/build.sh`, `tools/ue/validate.ps1`, `tools/ue/validate.sh`, `tools/export_package.py`

## Commands and packaging

### `pipeline/unreal/commands-and-packaging.md`

#### Commands, smoke, eval cameras, packaging (on demand; core: `pipeline/unreal-rules.md`)

Load when you build, test, package, smoke or capture eval shots.

##### Commands (wrapped by tools/ue/*; set UE_ROOT once per machine)
- Compile: `tools/ue/build.sh` (Mac) / `tools\ue\build.ps1` (Windows). Non-unity build: `pipeline/unreal/cpp-rules.md`, Modules item 4.
- Tests: `tools/ue/test.sh` / `test.ps1`, then `python3 tools/check_automation_report.py Saved/Automation/index.json`. The exit code of the editor alone proves nothing. [src: U12, U13]
  Epic's 5.8 docs spell it `Automation RunTest`; scripts use `RunTests`. Zero tests? Try the docs spelling. [src: U14]
- Package (Win64 only on Windows): `tools\ue\package.ps1 [-Shipping] [-Workbench]`. Fails on any `Error:` in the cook log.
  Default is the submission target, workbench compiled out (`workbench-check` must pass); `-Workbench` makes the tester package, never submitted (D-new-workbench-debug).
  Package scripts refuse a dirty git tree (`--allow-dirty` / `-AllowDirty` overrides), write `BUILD_INFO.txt` (commit, date, config) (plus `target=` and `workbench=`) into the package, and time out (`UE_TIMEOUT` seconds, default 7200).
- Smoke: run the packaged game with `-SmokeQuitAfter=15`; the log must contain one line per the contract in `tools/ue_run.py`: `SMOKE_OK map=<map> fps=<n> worst_ms=<n> commit=<sha> input=ok|none input_vz=<Z cm/s while IA_Attack is held, below 0> res=<W>x<H> win=windowed|fullscreen view=<W>x<H> aspect=<a> debugdraw=0|1 textpx=<n> load_ms=<n> workbench=0|1`. view= is the gameplay view inside the bars (16:9 within 0.01), debugdraw=1 means a debug draw is on (a default launch logs 0). `-SmokeShot=<png>` writes the whole-window screenshot the smoke checks with `art_check.py`, `screen_check.py` and `art_judge.py scene` (`pipeline/unreal-rules.md` Display). textpx = smallest UI text height in px on title, HUD, pause and lose at the current resolution. `-SmokeMap=<path>` loads that map instead of GameDefaultMap. (The switches are Day-0 card 0.6.) [VERIFY]
- `tools/ue/smoke.sh <exe>` / `smoke.ps1 -Exe <exe>` fails on a non-zero exit, a `SMOKE_OK` line that misses the contract in `tools/ue_run.py` (fps < 55 is one miss), any `SMOKE_BAD` pattern, any `Error:` line or `Failed to load` line (allowlist `tools/ue/smoke-allow.txt`, one decision row per line), or a new `Saved/Crashes` folder.
- A PR that changes a map smokes that map: `SMOKE_GAME_MAP=/Game/UmbrellaElla/Maps/<Map> SMOKE_MAP=<Map> tools/ue/smoke.sh <exe>` (`$env:` for `smoke.ps1`). `SMOKE_GAME_MAP` is the full path the game loads (`-SmokeMap=`); `SMOKE_MAP` is the short name the `SMOKE_OK map=` field must show. `check_pr.py` fails a pasted `SMOKE_OK` line whose map is not one the PR changes, so paste only changed-map smokes.
- The smoke runs on the Development package (D-new-smoke). Shipping writes no log. [src: U10]

##### Eval cameras (art captures from a packaged build)
- `-EvalCam=<CameraActor name>` (e.g. `-EvalCam=CAM_Eval_Arena`), Day-0 card 0.12, lane `Source/UmbrellaElla/Private/Smoke/**`.
  After the map and its sublevels load (wait up to 10 s), it sets the player's view target to that camera with no blend, waits 2 s,
  runs `HighResShot 1920x1080`, logs `EVALCAM_OK cam=<name> file=<path>` and quits with exit code 0. A name not in the map logs an `Error` naming it and exits 1.
- Dev-only: compiled inside `#if !UE_BUILD_SHIPPING`, so captures come from a Development package. Shipping ignores the switch.
- The Integrator places the `CAM_Eval_*` actors. The Art Director judges only captures made this way (`pipeline/roles/art-director.md`).

##### Packaging gotchas
- Every map is listed in `MapsToCook` (the Integrator's map card adds its line); `GameDefaultMap` is set (TD, card 0.3). Assets loaded only by string path are not cooked; use `DirectoriesToAlwaysCook`. [src: U17, U18]
- Shipping strips `check`, logging and the console. The submission is the Windows Development package; Shipping is not required (D25). [src: U9, U10, U11]
- Win64 packages build only on Windows; Mac packages only on a Mac. The Windows packaging machine is named in the `docs/jam-brief.md` People table by Day-0 card 0.0 (a Day-1 blocker). [src: U26]
- `-prereqs` adds Epic's prerequisites installer (VC++ runtime); since 5.1 some clean PCs still miss it (fallback: app-local prerequisites). Test the zip on a machine or user profile that never had the editor. [src: U16]

## CI and repo settings

### `.github/workflows/pipeline-checks.yml`

```yaml
name: pipeline-checks
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
  issues:
    types: [opened, edited, labeled]
  push:
    branches: [main]
permissions:
  contents: read
  issues: read   # check_card.py reads the task card the PR closes
# CI profile (pipeline/agent-ops/README.md "CI profile"): a committed .pipeline-ci-full at the root turns on the long
# pipeline suites (the Linux unit tests, the windows job). The installer never ships it, so a game repo runs the fast
# game checks only; the pipeline source repo and the pipeline test repo keep it.
# Build mode: docs/build/MODE says `direct` (or there is no MODE file and HANDOFF.md exists) when the team builds
# directly: a build lead merges area/* branches into main after the local gate (tools/build/gate.sh) and pushes. Then
# the card-only work is skipped (card readiness, PR body, the LFS art pulls for the PR ship gate) and so are the checks
# the local gate judges against main instead of absolutely (ui_check ci, bake_preset, the audio WAV scans): an
# unfinished game fails them by design. The fast checks keep running, so a red main still means something broke.
# The Unreal build never runs on GitHub runners; the local gate builds and tests it.
jobs:
  profile:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      full: ${{ steps.marker.outputs.full }}
      direct: ${{ steps.mode.outputs.direct }}
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false
      - name: CI profile from the .pipeline-ci-full marker (full = the pipeline suites run too)
        id: marker
        run: |
          if [ -f .pipeline-ci-full ]; then full=true; else full=false; fi
          echo "CI profile: full=$full"
          echo "full=$full" >> "${GITHUB_OUTPUT:-/dev/null}"
      - name: Build mode from docs/build/MODE (direct = local build lead merges, no cards or PRs)
        id: mode
        run: |
          if [ -f docs/build/MODE ]; then mode=$(tr -d '[:space:]' < docs/build/MODE); elif [ -f HANDOFF.md ]; then mode=direct; else mode=cards; fi
          if [ "$mode" = direct ]; then direct=true; else direct=false; fi
          echo "build mode: $mode (direct=$direct)"
          echo "direct=$direct" >> "${GITHUB_OUTPUT:-/dev/null}"
  card:
    # Card readiness when a card is filed or edited, not only when its PR opens (AGENTS.md section 8).
    needs: profile
    if: github.event_name == 'issues' && contains(github.event.issue.labels.*.name, 'task') && needs.profile.outputs.direct != 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Task card is ready (Producer)
        run: python3 tools/check_card.py --event
  checks:
    # Runs even when the profile job fails (then the timeout is the fast one); the game checks below always run.
    needs: profile
    if: ${{ !cancelled() && github.event_name != 'issues' }}
    runs-on: ubuntu-latest
    timeout-minutes: ${{ needs.profile.outputs.full == 'true' && 180 || 20 }}   # full: the unit tests take about 100 min
    env:
      DIRECT: ${{ needs.profile.outputs.direct }}   # 'true': direct local build, the card-only steps below skip
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false   # pointers are enough for these checks; saves LFS bandwidth
          fetch-depth: 0   # check_pr rule gate reads the PR's commits (base..head) for kickoff's gate-commit trailer
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Repo guardrails and the cross-doc consistency gate (decision IDs, card IDs, paths, owners, Day-0 cycles)
        run: python3 tools/pipeline_check.py
      - name: List the LFS art the ship gate re-measures (references, team art, the GDD's images)
        if: env.DIRECT != 'true'
        id: lfsart
        run: |
          git lfs ls-files -l -I 'pipeline/art/reference/**,Assets/**,Mockups/**,docs/gdd/**' | sort > "$RUNNER_TEMP/lfs-art.txt"
          echo "key=$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest()[:16])' "$RUNNER_TEMP/lfs-art.txt")" >> "${GITHUB_OUTPUT:-/dev/null}"
      - name: Restore the LFS art cache (bandwidth is spent only when the art set changes)
        if: env.DIRECT != 'true'
        uses: actions/cache@v4
        with:
          path: .git/lfs/objects
          key: lfs-art-${{ runner.os }}-${{ steps.lfsart.outputs.key }}
          restore-keys: lfs-art-${{ runner.os }}-
      - name: Pull the art the ship gate re-measures (check_pr artship re-runs the art checks on every shipped image against these; the art calibration and ship-gate unit tests read them too)
        if: env.DIRECT != 'true'
        run: git lfs pull --include='pipeline/art/reference/**,Assets/**,Mockups/**,docs/gdd/**'
      - name: Pull the key art from LFS so the art calibration test runs (it skips on a pointer; full CI profile only)
        if: hashFiles('.pipeline-ci-full') != ''
        run: git lfs pull --include='pipeline/art/reference/*.png'
      - name: Pull the LFS files the unit tests copy (test fixtures and the pinned rules PDF; a pointer there fails the sandboxes' checkouts; full CI profile only)
        if: hashFiles('.pipeline-ci-full') != ''
        run: git lfs pull --include='tests/fixtures/**,docs/rules/*.pdf'
      - name: Feature manifest matches the current GDD snapshot (statuses, IDs, QA tests, presets, snapshot pins)
        env:
          BASE: ${{ github.event.pull_request.base.sha }}
        run: |
          if [ -n "$BASE" ]; then
            git cat-file -e "$BASE^{commit}" 2>/dev/null || git fetch --no-tags origin "$BASE"   # no --depth: a shallow mark would cut base..head
            # merged GDD snapshots never change: every pin on the base branch is still the same (dry run B H9)
            git show "$BASE:docs/feature-manifest.json" > "$RUNNER_TEMP/base-manifest.json"
            python3 tools/manifest_check.py --pins-from "$RUNNER_TEMP/base-manifest.json"
          else
            python3 tools/manifest_check.py
          fi
      - name: Pipeline unit tests (includes the module, card and art gate calibration suites; full CI profile only, about 100 min)
        if: hashFiles('.pipeline-ci-full') != ''
        run: python3 -m unittest discover -s tests -v
      - name: Module boundaries and C++ standard (Technical Director; skips while there is no Source/)
        run: python3 tools/module_check.py || [ $? -eq 2 ]
      - name: Pull only the Art PNGs this PR changed from LFS (D-new-ci-lfs), so sprite_check sees real images
        if: github.event_name == 'pull_request'
        env:
          BASE: ${{ github.event.pull_request.base.sha }}
        run: |
          git cat-file -e "$BASE^{commit}" 2>/dev/null || git fetch --no-tags origin "$BASE"   # no --depth: a shallow mark would cut base..head
          inc=$(git diff --name-only "$BASE" HEAD -- 'Art/**/*.png' | paste -sd, -)
          if [ -n "$inc" ]; then git lfs pull --include="$inc"; fi
      - name: Sprite sheets with a .sprite.json sidecar (skips LFS pointers and a missing Art/; the TD human adds --require-dir on card 0.10b)
        run: python3 tools/sprite_check.py --scan Art
      - name: Hitboxes fit the art (Gameplay Dev; required). Pulls every sprite named in pipeline/feel/hitboxes.json, so a stale shape or an art swap without a re-fit fails
        run: |
          inc=$(python3 tools/hitbox_check.py lfs-include)
          if [ -n "$inc" ]; then git lfs pull --include="$inc"; fi
          python3 tools/hitbox_check.py check --fail-lfs-pointer
      - name: Owl encounter data (Level Designer)
        run: python3 tools/encounter_check.py
      - name: UI inputs that exist yet (UI and UX; skips inputs not created)
        if: env.DIRECT != 'true'
        run: python3 tools/ui_check.py ci
      - name: Feel data limits (Game Designer)
        run: python3 tools/feel_check.py
      - name: Shipped defaults equal the baked preset; before the G4 bake, every C++ default follows the tuning rules
        if: env.DIRECT != 'true'
        run: |
          if [ -f pipeline/qa/baked.json ]; then python3 tools/bake_preset.py check; else python3 tools/bake_preset.py defaults; fi
      - name: Submission duties and the deadline guard stay wired (Producer; dry run B M2)
        run: python3 tools/submission_check.py wiring
      - name: No undeclared game commits before the jam start (direct build; tools/build/gate.sh runs it on every merge)
        if: env.DIRECT == 'true'
        run: python3 tools/submission_check.py prejam
      - name: Official Rules (docs/rules) - jam rules cite them, deadline = section 4, pre-jam assets (7(h)), English (7(i))
        run: |
          python3 tools/submission_check.py rules
          python3 tools/submission_check.py assets
          python3 tools/submission_check.py english
      - name: Editor MCP config is valid and off until the kickoff record (Agent Ops)
        run: python3 tools/editor_mcp.py check
      - name: No committed secrets (Agent Ops; the settings, agents, mcp and components rules join after card 0.17)
        run: python3 tools/secrets_check.py --rules secret,secretfile
      - name: Audio sound list and sound names in docs and data (Audio)
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch --no-tags --depth=1 origin "${{ github.event.pull_request.base.sha }}"
            # a P0 feature's sound never drops a tier against the base branch (dry run B H8)
            git show "${{ github.event.pull_request.base.sha }}:pipeline/audio/sound-list.csv" > "$RUNNER_TEMP/base-sounds.csv"
            python3 tools/audio_check.py --list --tiers-from "$RUNNER_TEMP/base-sounds.csv"
          else
            python3 tools/audio_check.py --list
          fi
          python3 tools/audio_check.py --docs AGENTS.md pipeline/*.md pipeline/*/*.md pipeline/level/encounter.json pipeline/feel/feel.json
          # every event, state, attack, feature, screen and menu action has a sound row with a style family
          python3 tools/audio_check.py --events
      - name: "Story text (Story role): bible, names, tone, deny list; the critic calibration set still fails where it should"
        run: |
          python3 tools/story_check.py
          python3 tools/story_check.py --calibrate
          if [ -f Content/UmbrellaElla/UI/ST_UI.csv ]; then python3 tools/story_check.py --scan Content/UmbrellaElla/UI/ST_UI.csv pipeline/submission/itch-page.md; else python3 tools/story_check.py --scan pipeline/submission/itch-page.md; fi
      - name: Audio source WAVs (skips LFS pointers and a missing Audio/Source; add --require-dir once card 0.15 or the first audio card merges)
        if: env.DIRECT != 'true'
        run: python3 tools/audio_check.py --scan Audio/Source
      - name: Audio quality bar, measured (pipeline/audio/style-target.md; skips LFS pointers and a missing Audio/Source)
        if: env.DIRECT != 'true'
        run: python3 tools/audio_style_check.py check Audio/Source
      - name: PR body has task, evidence header, package evidence where paths or the linked card need it, linked risks
        if: (github.event_name == 'pull_request') && env.DIRECT != 'true'
        env:
          BASE: ${{ github.event.pull_request.base.sha }}
          GH_TOKEN: ${{ github.token }}
        run: |
          git cat-file -e "$BASE^{commit}" 2>/dev/null || git fetch --no-tags origin "$BASE"   # no --depth: a shallow mark would cut base..head
          git diff --name-only "$BASE" HEAD > "$RUNNER_TEMP/changed.txt"
          n=$(python3 -c "import json,os,re; b=json.load(open(os.environ['GITHUB_EVENT_PATH']))['pull_request'].get('body') or ''; m=re.search(r'(?i)\b(?:Closes|Fixes|Resolves|Part of)\s+#(\d+)', b); print(m.group(1) if m else '')")
          # a lane_guard revert PR names the commit it reverts; check_pr compares the diff with its inverse (final-10 A H3)
          rv=$(python3 -c "import json,os,re; b=json.load(open(os.environ['GITHUB_EVENT_PATH']))['pull_request'].get('body') or ''; m=re.search(r'(?m)^[ \t]*Revert of: ([0-9a-f]{40})', b); print(m.group(1) if m else '')")
          if [ -n "$rv" ]; then git cat-file -e "$rv^{commit}" 2>/dev/null || git fetch --no-tags origin "$rv"; fi
          if [ -n "$n" ]; then
            # the card's own Done-when decides package evidence too, not only the PR's copy (dry run A H4)
            gh issue view "$n" --repo "$GITHUB_REPOSITORY" --json title,body > "$RUNNER_TEMP/card.json"
            python3 tools/check_pr.py --changed "$RUNNER_TEMP/changed.txt" --card "$RUNNER_TEMP/card.json" --base "$BASE"
          else
            python3 tools/check_pr.py --changed "$RUNNER_TEMP/changed.txt" --base "$BASE"
          fi
      - name: Linked task card is ready (Producer)
        if: (github.event_name == 'pull_request') && env.DIRECT != 'true'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          n=$(python3 -c "import json,os,re; b=json.load(open(os.environ['GITHUB_EVENT_PATH']))['pull_request'].get('body') or ''; m=re.search(r'(?i)\b(?:Closes|Fixes|Resolves|Part of)\s+#(\d+)', b); print(m.group(1) if m else '')")
          if [ -z "$n" ]; then echo "check_card: PR links no card; check_pr.py fails this PR for that"; exit 0; fi
          gh issue view "$n" --repo "$GITHUB_REPOSITORY" --json title,body | python3 tools/check_card.py --json-stdin
  windows:
    # Teammates run the pipeline on Windows (PowerShell, Codex or Claude Code). Same unit tests and repo gate as the
    # Linux job, plus one headless Blender render. Suites that drive the Mac tools/ue/*.sh scripts skip on Windows.
    # Full CI profile only (.pipeline-ci-full): Windows minutes count double on the game repo's plan.
    needs: profile
    if: github.event_name != 'issues' && needs.profile.outputs.full == 'true' && needs.profile.outputs.direct != 'true'
    runs-on: windows-latest
    timeout-minutes: 300   # the Linux suite takes about 100 min; Windows starts processes and git more slowly
    env:
      PYTHONUTF8: "1"   # as tools/kickoff.ps1, start_session.ps1 and agent.ps1 set it for every agent session
      BLENDER_VERSION: "5.2.1"   # the Mac runs 5.2.1; checksum from download.blender.org/release/Blender5.2/blender-5.2.1.sha256
      BLENDER_SHA256: "0e631dad7d0cad6d5d18abdd2e2550f6c0213215334eda00ddbd3d22b96ecb2c"
    defaults:
      run:
        shell: pwsh
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: false   # pointers are enough for most checks; the next step pulls what the tests copy
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: List the LFS art the unit tests read (references, team art, the GDD's images)
        id: lfsart
        run: |
          $list = Join-Path $env:RUNNER_TEMP "lfs-art.txt"
          git lfs ls-files -l -I 'pipeline/art/reference/**,Assets/**,Mockups/**,docs/gdd/**' | Sort-Object | Set-Content -Path $list -Encoding utf8
          $key = (Get-FileHash $list -Algorithm SHA256).Hash.ToLower().Substring(0, 16)
          "key=$key" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
      - name: Restore the LFS art cache (bandwidth is spent only when the art set changes)
        uses: actions/cache@v4
        with:
          path: .git/lfs/objects
          key: lfs-art-${{ runner.os }}-${{ steps.lfsart.outputs.key }}
          restore-keys: lfs-art-${{ runner.os }}-
      - name: Pull the LFS files the unit tests need (the art the calibration and ship-gate tests read, fixtures, the pinned rules PDF)
        run: git lfs pull --include='pipeline/art/reference/**,Assets/**,Mockups/**,docs/gdd/**,tests/fixtures/**,docs/rules/*.pdf'
      - name: Repo guardrails and the cross-doc consistency gate
        run: python tools/pipeline_check.py
      - name: Pipeline unit tests, fast modules (everything but the long sandbox suites)
        working-directory: tests
        run: |
          $slow = @('test_honest_jam', 'test_ue_scripts', 'test_kickoff', 'test_kickoff_simple', 'test_plan_checks')
          $fast = Get-ChildItem test_*.py | ForEach-Object { $_.BaseName } | Where-Object { $slow -notcontains $_ }
          python -m unittest @fast
      - name: Pipeline unit tests, the long sandbox suites (runs even when the fast ones fail)
        if: success() || failure()
        working-directory: tests
        run: python -m unittest test_honest_jam test_ue_scripts test_kickoff test_kickoff_simple test_plan_checks
      - name: Install Blender (official zip, version and checksum pinned)
        if: success() || failure()
        run: |
          $minor = ($env:BLENDER_VERSION -split '\.')[0..1] -join '.'
          $zip = Join-Path $env:RUNNER_TEMP "blender.zip"
          Invoke-WebRequest "https://download.blender.org/release/Blender$minor/blender-$env:BLENDER_VERSION-windows-x64.zip" -OutFile $zip
          $got = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
          if ($got -ne $env:BLENDER_SHA256) { Write-Error "blender zip sha256 $got, want $env:BLENDER_SHA256"; exit 1 }
          Expand-Archive $zip -DestinationPath $env:RUNNER_TEMP
          $exe = Join-Path $env:RUNNER_TEMP "blender-$env:BLENDER_VERSION-windows-x64\blender.exe"
          if (-not (Test-Path $exe)) { Write-Error "no $exe in the zip"; exit 1 }
          "BLENDER=$exe" | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8
      - name: Blender headless render smoke (Cycles on the CPU; the runner has no GPU)
        if: success() || failure()
        run: |
          $png = Join-Path $env:RUNNER_TEMP "blender-smoke.png"
          $expr = "import bpy; s = bpy.context.scene; s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; " +
                  "s.cycles.samples = 1; s.render.resolution_x = 32; s.render.resolution_y = 32; " +
                  "s.render.image_settings.file_format = 'PNG'; s.render.filepath = r'$png'; " +
                  "bpy.ops.render.render(write_still=True)"
          & $env:BLENDER -b --factory-startup --python-exit-code 1 --python-expr $expr
          if ($LASTEXITCODE -ne 0) { Write-Error "blender exited $LASTEXITCODE"; exit 1 }
          if (-not (Test-Path $png) -or (Get-Item $png).Length -eq 0) { Write-Error "no render at $png"; exit 1 }
          Write-Host "BLENDER_SMOKE_OK $png $((Get-Item $png).Length) bytes"
```

### `.github/CODEOWNERS.example`

```text
# Rename to CODEOWNERS once D26 names the human Technical Director, then turn on
# branch protection "Require review from Code Owners" for main.
# Agents cannot be code owners; these must be real GitHub accounts.
*.uproject                      @TD_GITHUB_HANDLE
/Source/*.Target.cs             @TD_GITHUB_HANDLE
/Source/**/*.Build.cs           @TD_GITHUB_HANDLE
/Source/UmbrellaElla/Public/Core/ @TD_GITHUB_HANDLE
# Component lanes (Public/Umbrella/, Public/Attack/, ...) are not listed: the Dev Lead reviews them, not the TD.
/Config/DefaultEngine.ini       @TD_GITHUB_HANDLE
/pipeline/                      @RickTheBuilder
/AGENTS.md                      @RickTheBuilder
/tools/                         @TD_GITHUB_HANDLE
/.github/                       @RickTheBuilder
/docs/decisions.md              @RickTheBuilder
```

## Commands and checks

### `tools/pipeline_check.py`

Usage text from the file:

```text
Repository guardrails for the jam pipeline. Stdlib only; runs locally and in CI.

Checks (each one exists because of a finding in docs/audit.md):
  leak        text from another project or another engine (Unity) in pipeline/docs/code
  forbidden   Unreal build output or IDE junk committed (Binaries/, Intermediate/, ...)
  lfs         binary assets (.uasset, .umap, .png, .wav, ...) not routed through Git LFS
  size        large non-LFS files
  budget      always-loaded agent context over its word budget
  roles       role cards missing a required section (owns / inputs / outputs / done / never)
  hygiene     in Source/ and Config/ (skipped while absent; pipeline/checklists/file-hygiene.md):
              a TODO without a card or decision id (`TODO(UE-12)`, `TODO(D-new-port-4)` are fine),
              `#pragma warning(disable` or PRAGMA_DISABLE_*_WARNINGS without a decision row on that line
              (AGENTS.md section 7), and any `ROLE:` line (pipeline text in shipped code)
  placeholder `_PH` asset names (D-new-port-8) in Source/, Config/ and Content/ paths. Reported as a note
              during the jam; a problem with --release (the submission build, G4)
  private     names of private projects, tools and personal paths (describe a practice on its own merits)
  consistency cross-doc references (so docs cannot drift apart): a decision ID (D<n>, D-new-..., GDD B DEC-nn) with no row in docs/decisions.md,
              a Day-0 card ID not in pipeline/day0-cards.md, a repo path that does not exist (and is not a planned
              output in a Day-0 lane; case must match exactly, as on the Linux CI runner), a decision owner that is not a People row, person or role in
              docs/jam-brief.md / AGENTS.md, a cycle in the Day-0 "After" column, and a Day-0 row a person owns or a
              person's step outside a true checkpoint (check_card.day0_owner_problems, pipeline/human-checkpoints.md)
  repomap     docs/repo-map.md (tools/repo_map.py): a pipeline folder the installer ships is missing from it, or its
              "Pipeline folders" section names a path that does not exist. Team folders never fail it; skipped while
              the map is absent
  package     MegaPipeline/ is stale, hand-edited, or a repo doc lands in no package file (pipeline repos only, not an
              installed game repo; tools/export_package.py --check;
              skipped while MegaPipeline/ is absent)
Also prints the total size of LFS-tracked files (from the pointers; nothing is downloaded).

Usage: python3 tools/pipeline_check.py [--root PATH] [--release]
Exit 0 = clean, 1 = violations found.
```

Run in CI by:

- `.github/workflows/main-red.yml`: Pipeline checks
- `.github/workflows/pipeline-checks.yml`: Repo guardrails and the cross-doc consistency gate (decision IDs, card IDs, paths, owners, Day-0 cycles)
- `.github/workflows/pipeline-checks.yml`: Repo guardrails and the cross-doc consistency gate

Tests: `tests/test_affected_tests.py`, `tests/test_agent_ops_hook.py`, `tests/test_export_package.py`, `tests/test_honest_jam.py`, `tests/test_lane_guard.py`, `tests/test_pipeline_check.py`, `tests/test_practice.py`, `tests/test_repo_map.py`

### `tools/affected_tests.py`

Usage text from the file:

```text
Pick the pipeline unit tests a change needs, inside a time budget. Stdlib only.

Card sessions (builder and reviewer) run this, never `unittest discover`: the full suite runs in the pipeline repos'
CI (.pipeline-ci-full). A selection aims at BUDGET seconds of test time (5 min, measured in tests/timings.json). The
budget picks tests; it never fails a run: a run over it prints one WARNING line and carries on.

How a changed path maps to test modules, nearest first:
  0  the test file itself; tests/test_<name>.py for tools/<name>.py; the docs tests (DOC_TESTS) for a doc
  1  a test that imports the changed tool or test helper, or names its path (`tools/kickoff.py`)
  2  a test that names a changed doc's path (`docs/decisions.md`), or a changed tool's file name (`kickoff.py`)
  3  a test that names only a doc's file name (`"decisions.md"`, often a sandbox copy list) or its folder
     (`pipeline/roles`), or imports a tool which imports the changed tool
Nearest first, then cheapest first, whole modules fill the budget. A module too slow to fit runs only its classes
that name the change, cheapest first, while they fit; the rest is listed as left for CI with its time.
Game files (Source/, Content/, Config/, ...) map to no Python test. A Source/ change maps to Unreal automation test
prefixes instead, printed as a `tools/ue/test.sh` line (never run here; the card's Unreal steps run it):
  Source/<Module>/{Public,Private}/<Area>/...   UmbrellaElla.<Area> (when a test has that name) plus the prefixes of
                                                every test file under Private/Tests/ that includes the changed header
  Source/<Module>/Private/Tests/<Area>/x.cpp    the prefixes of the test names in that file
  a test helper header (Tests/Shared/x.h)       the prefixes of the test files that include it
  *.Build.cs, *.Target.cs, a module's own file, or nothing found: the whole set, UmbrellaElla

Usage: python3 tools/affected_tests.py [FILE ...]          print the selection and the command (default files:
                                                            git diff origin/main...HEAD plus uncommitted changes)
       python3 tools/affected_tests.py --run [FILE ...]    run it, one unittest process per target, and print the time
       python3 tools/affected_tests.py --base REF          diff against REF instead of origin/main
       python3 tools/affected_tests.py --budget SECONDS    another budget (default 300)
       python3 tools/affected_tests.py --measure           time every module and class into tests/timings.json
                                                            (the full suite: pipeline repos only, never a card session)
       python3 tools/affected_tests.py --measure tests/test_x.py   time only that module (a new one) into the file
Exit 0 = nothing failed (time never fails), 1 = a selected test failed, 2 = usage error.
```

Tests: `tests/test__card_session_guard.py`, `tests/test_affected_tests.py`

### `tools/module_check.py`

Usage text from the file:

```text
Technical Director's module-boundary gate for Source/ (pipeline/unreal-rules.md,
"Modules are this project's assembly definitions" and "C++ correctness rules").

A module is any Source/**/<Name>/<Name>.Build.cs with Public/ (or Classes/) and Private/ next to it.

Rules (the tag is printed in front of each finding):
  a private-include   #include reaching into another module's Private/ (relative path or not)
  b missing-dep       a module includes a header of a module not in its Build.cs
                      PublicDependencyModuleNames / PrivateDependencyModuleNames
  c public-leak       a Public header exposes a type (include or name) of a module that is
                      only a Private dependency
  d missing-api       a UCLASS/USTRUCT in Public/ used by another module has no <MODULE>_API
                      macro (UCLASS(MinimalAPI) also counts)
  e generated-last    "X.generated.h" is not the last #include of its header, or X is not the header's name
  f raw-uobject       raw U*/A* pointer member in a UCLASS/USTRUCT body (should be TObjectPtr),
                      also inside TArray/TSet/TMap/TMultiMap/TSortedMap (TArray<AActor*>)
  g iwyu              Build.cs does not set IWYUSupport = IWYUSupport.Full

C++ standard rules (Epic coding standard + pipeline/unreal-rules.md; every .h/.cpp in a module):
  h pragma-once       a header has no "#pragma once"
  i null              NULL (use nullptr)
  j std               std:: (except std::initializer_list), #include <vector> and other STL headers,
                      try/catch/throw, dynamic_cast (use TArray/TMap, return codes, Cast<>)
  k logtemp           LogTemp (use LogUmbrellaElla)
  l using-namespace   "using namespace" anywhere; a using declaration (using X::Y;) at file scope
  m override          a header declares a known engine virtual (BeginPlay, EndPlay, Tick, TickComponent,
                      SetupPlayerInputComponent, NotifyHit, NotifyActorBeginOverlap, Falling, ... see
                      ENGINE_OVERRIDES) without override or final
  n bool-name         a bool variable, member or parameter whose name does not start with b + capital,
                      and a bitfield bool (uint8 Name : 1) whose name does not start with b + capital
  o bool-func         a header declares a bool function not starting with Is, Has, Can or Should
                      (override/final declarations are skipped; their name is the engine's)
  p braces            if / else / for / while whose body is not in { } (do-while's "while (...);" is fine)
  q switch-default    a switch with no "default:" at its top level
  r text-macro        any string literal in code not wrapped in TEXT() (OpenLevel(this, "L_Graybox"),
                      FString X = "...", asset paths, UE_LOG formats). Skipped: # lines (#include, #define
                      LOCTEXT_NAMESPACE), and literals inside the macros in TEXT_FREE_CALLS (UPROPERTY/UCLASS
                      specifiers and meta, LOCTEXT, NSLOCTEXT, static_assert, IMPLEMENT_*_MODULE,
                      IMPLEMENT_SIMPLE_AUTOMATION_TEST, UE_LOGFMT [VERIFY on 5.8.4], ...)
  s shipping-guard    TAutoConsoleVariable, FAutoConsoleCommand*, FAutoConsoleVariableRef,
                      RegisterConsoleVariable/Command or CheatManager outside "#if !UE_BUILD_SHIPPING"
                      (or the #else of "#if UE_BUILD_SHIPPING"); UFUNCTION(Exec) anywhere, because UHT
                      does not allow UFUNCTION inside such a block [VERIFY on 5.8.4]
  t indent-tabs       lines indented with spaces (Epic: tabs). One finding per file, with the count.
                      Spaces after leading tabs (alignment) are fine.
  u raw-input         IsInputKeyDown, WasInputKeyJustPressed, WasInputKeyJustReleased,
                      GetInputKeyTimeDown, GetAsyncKeyState (input goes through Enhanced Input actions)
  v looping-timer     a .cpp calls a looping SetTimer but has no ::EndPlay that calls ClearTimer or
                      ClearAllTimersForObject. Looping = the loop argument is there and is not "false"
                      (SetTimer(H, this, &F, Rate, Loop) or SetTimer(H, Delegate, Rate, Loop)), so a
                      loop flag held in a variable counts as looping

More of Epic's standard (every .h/.cpp in a module):
  w type-prefix       UCLASS deriving from an A* class starts with A, other UCLASS/UINTERFACE with U,
                      USTRUCT with F, enums with E, other classes/structs with F, T, I or S; class members,
                      member functions, locals and parameters are PascalCase (bools are rule n)
  x deferred-lambda   a lambda that captures by reference ([&], &Local), everything by copy ([=], which also
                      captures this implicitly) or raw [this] and runs later:
                      written directly inside SetTimer, SetTimerForNextTick, CreateLambda, BindLambda,
                      AddLambda, AsyncTask or Async, or stored first (auto Fn = [...]) and then passed to
                      one of them in the same function (use CreateWeakLambda(this, ...) or capture by value)
  y auto              "auto", except a lambda variable (auto Fn = [...]) and a range-based for
  z enum              a UENUM that is not "enum class EName : uint8"; any other enum (in a .h or .cpp) that is
                      not "enum class" (a plain or unnamed enum)
  A const-getter      a header member function named Get*/Is*/Has*/Can*/Should* without trailing const
                      (static, override and final are skipped)
  B const-return      a header member function returning "const T" by value
  C public-state      any data member in the public: section of a UCLASS, UPROPERTY or not; and a protected
                      data member of a UCLASS that is not tuning or an asset reference: protected is allowed
                      only for a UPROPERTY with EditDefaultsOnly, EditAnywhere or EditInstanceOnly, or a
                      member whose type is an F*Tuning struct. static and constexpr are fine, and so is a
                      UDeveloperSettings subclass (UUmbrellaTuning is read as GetDefault<UUmbrellaTuning>()->Attack.X)
  D uobject-ref       a U*/A* type passed by reference in a header (UObject& Thing); pass a pointer
  E macro-name        a #define not named UMBRELLAELLA_[A-Z0-9_]* (LOCTEXT_NAMESPACE is allowed)
  F delegate-unbind   a .cpp binds onto another object's delegate (Other->OnX.AddDynamic/AddUObject/...)
                      and no ::EndPlay (or NativeDestruct/Deinitialize/BeginDestroy) there removes OnX
  G magic-number      a number in a .cpp outside Private/Tests/ other than 0, 0.5, 1, 2, named or not:
                      const/constexpr locals and namespace-scope constants count too. Tuning goes in the
                      component's F<Comp>Tuning header; a true constant goes in a header as static constexpr
  H dead-zone         a *DeadZone* identifier (stick dead zones live in the IA_Move modifier)
  I forward-decl      a header includes a project header but uses its types only by pointer, reference,
                      TObjectPtr/TWeakObjectPtr/TSubclassOf/...; forward-declare instead
  J bool-param        a header member function of a UCLASS takes a bool by value (Move(bool bFast)): use an
                      enum or two functions. Skipped: Set<X>(bool) with one parameter, On<X> delegate
                      handlers (the delegate fixes the signature), static functions (plain rule functions
                      take state as input), override/final, and bool& / bool* out parameters
  K final             (with --rules K, or once pipeline/unreal/cpp-rules.md drops its [VERIFY] on final) a UCLASS
                      that is not final, not Abstract or Blueprintable, has no subclass in Source/ and is not
                      named in docs/asset-changes/*.json (where a Blueprint child would be listed). An actor
                      class (A prefix) inherits Blueprintable and is skipped unless it says NotBlueprintable
  L character-shell   SHELL_CLASS (AEllaCharacter) is wiring only: its .cpp may define only the constructor and
                      SetupPlayerInputComponent; the constructor never calls BindAction; and
                      SetupPlayerInputComponent calls only SHELL_INPUT_CALLS (Super, AddMappingContext,
                      ->BindInput, and the Cast/GetSubsystem lookups that reach the input subsystem)

  N determinism       gameplay code (not Private/Tests/ or Harness/) reads the wall clock (FPlatformTime::*,
                      FDateTime::Now/UtcNow) or an unseeded random (FMath::Rand*, FMath::FRand*, FMath::VRand*,
                      FMath::SRand, rand()): draws come from the seeded FRandomStream so one seed replays one
                      run (GDD QA-08)
  O mutable-static    a static variable that is not const or constexpr (static locals, static members,
                      namespace-scope statics, static delegates): PIE keeps the module loaded, so the value
                      leaks into the next run. Static functions and console variables (rule s) are skipped
  P container-getter  a header function returns a non-const reference or pointer to a TArray/TMap/TSet/...
                      (TArray<FBolt>& GetBolts()): return const& or a copy so only the owner writes it

Feature switches (GDD B section 4; pipeline/unreal-rules.md, "Feature flags"):
  M feature-flag      a gameplay file (not Private/Tests/, not a *FeatureFlags* file) names a gated feature ID (a
                      docs/feature-manifest.json record with a flag: UMB-02 or UMB_02, in code or comments) but never
                      calls IsFeatureEnabled(...<FLAG>...) for it. The manifest is read from --root, else this repo

Limits (regex, not a compiler):
  - Engine headers are mapped to modules only through ENGINE_HEADERS below. Other engine includes
    are trusted, so rule b/c only covers project modules plus that table.
  - Rule f looks at member declarations at the top brace level of a reflected class/struct body.
    It skips function declarations (anything with "(") and F*/I*/T* types. A non-UObject class
    named with a U or A prefix would be a false positive; a pointer hidden behind a typedef or
    macro is a false negative.
  - Rule c/d match type names by word. A same-named local identifier would count as a use.
  - #if/#ifdef blocks are not evaluated; every include counts. Only rule s reads #if lines.
  - Rules h-v see code with comments and string contents blanked, except rule r, which reads literals.
  - Rule m only knows the names in ENGINE_OVERRIDES. Other overrides are left to the reviewer.
    ReceiveHit is a BlueprintImplementableEvent with no C++ virtual, so it is not in the list.
  - Rule n misses bools declared through a typedef or macro. Bitfields are checked only as uint8/uint32 X : 1.
  - Rule v reads the loop argument by position; a timer cleared in another file is not seen. Delegate
    unbinding in EndPlay is left to rule F.
  - Rule r does not parse raw string literals R"(...)". A macro that needs a plain char literal and is not in
    TEXT_FREE_CALLS is a false positive: add it to the list with a test.
  - Rules w, A, B, C read class bodies at their top level only; a member declared through a macro is missed.
  - Rule x follows a stored lambda only by its variable name inside the same outermost { } block. A lambda
    passed through a helper function or a member variable is missed.
  - Rule w reads locals and parameters as "<Type> <name>" with a capitalised or built-in type; a lowercase
    type (a typedef) hides the name.
  - Rule y allows auto in every range-based for (a regex cannot tell a map from an array).
  - Rule D checks headers only; a .cpp-only function is missed.
  - Rule F skips own subobjects (X = CreateDefaultSubobject in the same .cpp, GetCapsuleComponent() and the
    like). A widget binding its own BindWidget button needs RemoveAll in NativeDestruct or is a false positive.
  - Rule I only follows project headers; an engine header that could be forward-declared is not seen.
  - Rule K is off while UHT support for final on a UCLASS is [VERIFY] in pipeline/unreal/cpp-rules.md (k_proven),
    unless asked for (--rules K). It turns on by itself when card 0.4a pastes the card 0.3 compile log of a final
    UCLASS there and removes that [VERIFY]: the measurement, not a gate patch, switches it.
  - Rule L knows the shell only by its class name, and reads calls by name ("Cast", "BindInput").
  - Rule C cannot tell tuning from state by meaning; it trusts the Edit* specifier and the F*Tuning name.
  - Rule J cannot tell a bool that picks a behavior from one that passes state; it flags every by-value bool
    outside the skipped forms.
  - Rule N reads names only; a clock or random reached through a helper or another module is missed, and
    TMap/TSet iteration order (also not repeatable) is left to the reviewer.
  - Rule O treats a static declaration whose first bracket is "(" as a function, so a static variable
    initialised with parentheses (static int32 X(0);) is missed.

Usage: python3 tools/module_check.py [--root PATH] [--rules LETTERS]   (e.g. --rules hijk; letters are case-sensitive;
       rule K runs when K is in --rules or once cpp-rules.md proves final on a UCLASS)
Exit 0 = clean, 1 = problems, 2 = no Source/ folder (nothing to check; CI treats it as a skip).
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Module boundaries and C++ standard (Technical Director; skips while there is no Source/)

Tests: `tests/test_final8_fixes.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_kickoff_unattended.py`, `tests/test_module_check.py`, `tests/test_pipeline_check.py`, `tests/test_score_review.py`

### `tools/ue_run.py`

Usage text from the file:

```text
Shared helper for tools/ue/*.sh and *.ps1, so the Mac and Windows scripts behave the same.
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
```

Tests: `tests/fixtures/kickoff/stub_daily.py`, `tests/test_check_pr.py`, `tests/test_day0_cards.py`, `tests/test_encounter_wiring.py`, `tests/test_final10_fixes.py`, `tests/test_final8_fixes.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_kickoff_windows_daily.py`, `tests/test_smoke_visual.py`, `tests/test_ue_scripts.py`

### `tools/ue/common.ps1`

Usage text from the file:

```text
Shared settings for the Windows scripts. Commands follow pipeline/unreal/commands-and-packaging.md; [VERIFY] on 5.8.4.
Timeouts, dirty-tree refusal, BUILD_INFO.txt and smoke-log checks live in tools/ue_run.py (same for .sh).
Continue: under Windows PowerShell 5.1, "Stop" turns any stderr line from UBT/UAT into a fatal error.
```

### `tools/ue/common.sh`

Usage text from the file:

```text
Shared settings for the Mac scripts. Commands follow pipeline/unreal/commands-and-packaging.md; [VERIFY] on 5.8.4.
Timeouts, dirty-tree refusal, BUILD_INFO.txt and smoke-log checks live in tools/ue_run.py (same for .ps1).
```

### `tools/ue/build.ps1`

Usage text from the file:

```text
Compile the editor target on Windows. -NonUnity runs the stricter non-merged build.
```

Tests: `tests/kickoff_sandbox.py`, `tests/test_agent_ops_hook.py`, `tests/test_area.py`, `tests/test_check_pr.py`, `tests/test_day0_cards.py`, `tests/test_final10_fixes.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_kickoff.py`, `tests/test_kickoff_unattended.py`, `tests/test_score_review.py`, `tests/test_ue_scripts.py`, `tests/test_ui_check.py`

### `tools/ue/build.sh`

Usage text from the file:

```text
Compile the editor target on Mac. Fails on compile errors; prints the warning count. NONUNITY=1 = strict build.
```

Tests: `tests/kickoff_sandbox.py`, `tests/test_affected_tests.py`, `tests/test_agent_ops_hook.py`, `tests/test_area.py`, `tests/test_check_card.py`, `tests/test_check_pr.py`, `tests/test_day0_cards.py`, `tests/test_final10_fixes.py`, `tests/test_final9_fixes.py`, `tests/test_honest_jam.py`, `tests/test_journal.py`, `tests/test_kickoff.py`, `tests/test_kickoff_unattended.py`, `tests/test_score_review.py`, `tests/test_ue_scripts.py`, `tests/test_ui_check.py`

### `tools/ue/validate.ps1`

Usage text from the file:

```text
Asset and data validation on Windows: runs the DataValidation commandlet on the project, fails on any error,
and prints `validate: errors=N warnings=M` for the daily record. [VERIFY -run=DataValidation and its
log lines on 5.8.4; the DataValidation plugin must be enabled, Technical Director's call]
```

Tests: `tests/test_bake_preset.py`, `tests/test_honest_jam.py`, `tests/test_ue_scripts.py`

### `tools/ue/validate.sh`

Usage text from the file:

```text
Asset and data validation on Mac: runs the DataValidation commandlet on the project, fails on any error,
and prints `validate: errors=N warnings=M` for the daily record. [VERIFY -run=DataValidation and its
log lines on 5.8.4; the DataValidation plugin must be enabled, Technical Director's call]
```

Tests: `tests/test_bake_preset.py`, `tests/test_honest_jam.py`, `tests/test_ue_scripts.py`

### `tools/export_package.py`

Usage text from the file:

```text
Build MegaPipeline/, the human-browsable package of the jam pipeline. Stdlib only.

The repo files stay the single source of truth. This script copies them into one folder people can read
and share: the agent instructions, one file per role card, one file per discipline, and the reference docs.
Every generated file starts with a stamp naming its sources and the commit the export ran on.
Agents never load MegaPipeline/; they keep loading AGENTS.md and pipeline/roles/ from the repo.

Every doc in the repo (.md .txt .json .csv .yml .yaml .example, outside tests/, eval cases and the game roots in
GAME_ROOTS) and every script (tools/, pipeline/) must land in exactly one package file. An unmapped file is an orphan: add it
to PIPELINES below.

Usage: python3 tools/export_package.py            write MegaPipeline/ (removes files it no longer makes)
       python3 tools/export_package.py --check    exit 1 if MegaPipeline/ is stale, hand-edited or a doc is unmapped
       python3 tools/export_package.py --zip      write dist/MegaPipeline-<shortsha>.zip from a fresh build
Same sources and commit give byte-identical output. --check ignores the commit in the stamp, so a package
built one commit earlier from the same sources still passes.
Exit 0 = ok, 1 = problems, 2 = usage error.
```

Tests: `tests/test_export_package.py`, `tests/test_final8_fixes.py`, `tests/test_honest_jam.py`, `tests/test_pipeline_check.py`
