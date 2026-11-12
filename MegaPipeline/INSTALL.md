# MegaPipeline: install at kickoff

**Told to merge a PR and run the pipeline? Read [`START_HERE.md`](START_HERE.md) instead.** This page is for
the person who installs or updates the pipeline by hand.

This folder holds the whole Umbrella Ella AI-agent pipeline. Nothing here is active yet:
Claude hooks, CI workflows and agent instructions only work from the repo root.

- `AI Roles/`, `Pipelines/`, `Reference/`, `Project Instructions.md`, `README_ProjectStructure.md`:
  the readable package (same layout as the inherited pipeline).
- `repo/`: the working pipeline exactly as it sits at the root when installed
  (`AGENTS.md`, `CLAUDE.md`, `.claude/`, `.github/`, `pipeline/`, `docs/`, `tools/`, `tests/`, `evals/`).

## Install (a human, after the team agrees)

```
bash MegaPipeline/install.sh           # dry run: lists files and conflicts
bash MegaPipeline/install.sh --apply   # copies every file that does not exist yet
```

The script never overwrites. Files that already exist at the root (today: `AGENTS.md`,
`README.md`, `.gitignore`, `.gitattributes`) are reported as CONFLICT for a human to merge.
## Update an older install

1. Get the new version: replace this repo's `MegaPipeline/` folder with the newest one (from GameJam2026 `main`,
   or the update PR someone opens for you, in which case just merge it, pull, and go to step 4).
2. Run the update:

```
bash MegaPipeline/install.sh --update           # dry run: one line per change, nothing written
bash MegaPipeline/install.sh --update --apply   # do it
```

Windows: `powershell -ExecutionPolicy Bypass -File MegaPipeline\install.ps1 --update` (add `--apply` to do it).
No need to delete anything first. Update replaces the pipeline's own files (listed in `MegaPipeline/manifest.json`)
and removes the ones the new version dropped. Every file it replaces or removes is copied first to
`Saved/pipeline-backup/<date-time>/`. It never touches `Source/`, `Content/`, `Config/`, the GDD, or your own files.
A pipeline file your team changed (for example the People table in `docs/jam-brief.md`) is kept; the new version is
saved under `new/` in the backup folder so you can merge it by hand. It ends with `updated from <old> to <new>`.
3. Commit and push everything the update changed, including `.pipeline-installed.json`.
4. Start the jam the usual way: `tools\kickoff.ps1` (Windows) or `tools/kickoff.sh`.

Maintainer: after changing `repo/`, run `python3 MegaPipeline/install.py --make-manifest` and commit the manifest.
Tests: `python3 -m unittest discover -s MegaPipeline/tests`.

Then, from a plain terminal (not inside an agent):

```
tools/kickoff.sh --check                 # what is connected and what still needs connecting
tools/kickoff.sh --agent codex           # or --agent claude; Windows: tools\kickoff.ps1
tools/kickoff.sh --agent codex --practice   # test repos only, before Nov 12
```

One command runs the jam and stops only at human checkpoints. Details: `pipeline/how-to-run-the-jam.md`.

`repo/.gitattributes` stores the key art, the official rules PDF and a few test fixtures in
Git LFS. Install git-lfs before cloning (`git lfs install`).
