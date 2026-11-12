# Start here: run the pipeline

Build mode: run `tools/kickoff.sh` (or `.ps1`); it follows `docs/build/MODE`. `direct`: no cards, issues or PRs (section 4); use `HANDOFF.md`.

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


You were asked to merge a pull request and run the pipeline. This page is every step, in order.
It is written for Windows. Mac notes are at the end. Every command is typed in **PowerShell**, then press Enter.

Words on this page:
- **Repo**: the project folder, kept on GitHub. The test repo is `RickTheBuilder/PipelineTesting`.
- **PR (pull request)**: a set of changes waiting on GitHub. **Merge** = accept them into `main`.
- **main**: the shared version of the repo. **Pull** = copy the newest `main` from GitHub to your computer.
- **Agent**: the AI that writes the work (Codex or Claude Code). **Kickoff**: the one command that runs the agents.
- **Card**: one task, filed as a GitHub issue. **NEEDS HUMAN**: the pipeline is waiting for a person.

## Build modes
`tools/kickoff.sh` (Windows: `tools\kickoff.ps1`) follows `docs/build/MODE`:
- `direct`: no GitHub cards, PRs or reviews. Kickoff reads `HANDOFF.md`, resumes every unfinished area from its
  `area/<name>` branch with a Claude Code worker (brief: `docs/build/areas/<name>.md`), runs the local gates, merges
  each passing area into `main` and pushes. Use it to build fast, or to pick up the build where someone stopped.
- `cards`: the GitHub card flow (task cards, PRs, reviewers, CI). Use it when every change should be reviewed on GitHub.
No MODE file: kickoff asks once (Enter = `direct`) and saves the answer. Change it by editing the file, or pass
`--mode cards|direct` for one run. Both modes start every ready job whose files overlap no running job's (at most one
per CPU; `--parallel N` caps it); Unreal builds and tests share `UE_SLOTS` (default 2) engine slots. One area by hand:
`tools/area.sh <name>` (Windows: `tools\area.ps1 <name>`). Lead's handoff file shape: `docs/build/HANDOFF-template.md`.

## 1. One-time setup (skip any step you already did)

Open PowerShell: press the Windows key, type `PowerShell`, press Enter. Do not use "Command Prompt".
Do not use a terminal inside Codex, Claude Code or VS Code: kickoff refuses to run there.

1. Install the tools. Type each line and wait for it to finish:
   ```
   winget install Git.Git
   winget install Python.Python.3.12
   winget install GitHub.cli
   winget install OpenJS.NodeJS.LTS
   ```
   Close PowerShell and open a new one, so it finds the new programs. Then check:
   ```
   git --version
   py --version
   gh --version
   npm --version
   ```
   Each prints a version number. `py --version` must say 3.9 or higher. If `py` is "not recognized", try
   `python --version`, and type `python` wherever this page says `py`.
2. Set up Git once:
   ```
   git lfs install
   git config --global core.longpaths true
   ```
   You see `Git LFS initialized.` (LFS stores the big image files. Long paths stop Windows errors on deep folders.)
3. Let PowerShell run the repo's scripts (Windows blocks them by default):
   ```
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```
   Type `Y` and press Enter if it asks. Skip this and you get "running scripts is disabled on this system".
4. Log in to GitHub: type `gh auth login` and answer: `GitHub.com`, `HTTPS`, `Yes`, `Login with a web browser`.
   Copy the code it shows, press Enter, paste the code in the browser page. Check: `gh auth status` says
   `Logged in to github.com`. You also need write access to the repo: if you never got an invite, ask Rick.
5. Install and log in to your agent (one is enough):
   - Codex: `npm install -g @openai/codex`, then `codex login` (a browser opens; sign in with your ChatGPT account).
     Check: `codex login status` says `Logged in`.
   - Claude Code: `npm install -g @anthropic-ai/claude-code`, then `claude auth login`. Check: `claude auth status`.
6. Art is made in Blender: install it from blender.org (no key). Without it art is a labelled placeholder that never
   ships. Audio API keys (optional for a test run; without them sound uses placeholders): if you were given keys,
   type each one like this (your key inside the quotes), then close and reopen PowerShell:
   ```
   setx ELEVENLABS_API_KEY "paste-the-key-here"
   setx STABILITY_API_KEY "paste-the-key-here"
   ```
   Never paste a key into a file in the repo.

## 2. Get the repo on your computer (first time only)
```
mkdir $HOME\dev
cd $HOME\dev
gh repo clone RickTheBuilder/PipelineTesting
cd PipelineTesting
```
Use this folder, not one inside OneDrive. GitHub Desktop users: File > Clone repository, pick
`RickTheBuilder/PipelineTesting`. Its folder is then `$HOME\Documents\GitHub\PipelineTesting`.

## 3. Merge the PR on GitHub
1. Open the PR link you were sent (or the repo's **Pull requests** tab, then the PR named "Update MegaPipeline").
2. Scroll to the bottom. Click the green **Merge pull request**, then **Confirm merge**.
3. Done when the page shows a purple **Merged** label.
   If it says "This branch has conflicts", stop and tell Josh. Do not try to fix it.
   A red X next to the checks: merge only if the PR description says the red checks are expected. If not, tell Josh.

## 4. Pull the merged version to your computer
In PowerShell, inside the repo folder (`cd $HOME\dev\PipelineTesting`):
```
git checkout main
git pull
```
You see a list of changed files, or `Already up to date.` Check the version: `type pipeline\VERSION` prints `1.1.0`.
GitHub Desktop instead: set **Current branch** to `main`, click **Fetch origin**, then **Pull origin**.
If `git pull` says "Your local changes would be overwritten", type `git stash`, then `git pull` again.

## 5. Check the connections
```
tools\kickoff.ps1 --check --agent codex
```
(Use `--agent claude` if you use Claude Code.) The first line is `kickoff: pipeline 1.1.0+<code> | GDD ...`.
Then one line per tool: `CONNECTED`, `SKIPPED` or `NOT CONNECTED <name> -> <what to do>`.
- Only lines that end in `(required)` stop you. Do what each says after `->`, then run the check again.
- `NOT CONNECTED git hooks ... (required)` is normal the first time. Type `py tools\install_git_hooks.py`; it prints
  two `installed` lines.
- Many other `NOT CONNECTED` lines (Unreal, GIMP, Aseprite, sox, OBS, butler, API keys) are fine for a test run.
- When a line says `python3`, type `py` instead.

## 6. Run it
Before the jam starts (Nov 12, 00:00 New York time) a test repo needs practice mode, so the first run is:
```
tools\kickoff.ps1 --practice --agent codex
```
It prints `PRACTICE mode on: ...` (it commits and pushes one small file, `.pipeline-practice`, to `main`),
then starts the run (part 7).
The first night, bound the run: add `--max-cards 5`. It stops once 5 cards are merged or blocked (cards already
running finish first) and ends with `KICKOFF bounded: 5 card(s) done this run (merged X, blocked Y); run again to
continue`. Running it again picks up where it stopped.
To reach the first playable (G1) on a Mac, use `tools/kickoff.sh --split --until G1` instead: it builds only the cards
G1 needs and ends with `KICKOFF G1 reached: DAILY ...` once the Mac Development package launches in its smoke.
`--max-cards` alone cannot do this: it counts cards, it does not pick which ones.
If a teammate already did this, `git pull` brought that file and the flag does nothing. After that, just type:
```
tools\kickoff.ps1 --agent codex
```
On the team repo before the start (no `--practice`), it runs only the pre-jam cards: agent setup, the rules check and
the test workbench on plain boxes. It prints `PRE-JAM mode` and says the rest waits for the start.

## 7. What happens while it runs
Leave the window open and do not type in it. You do not need to do anything until it stops. You will see lines like:
```
RUN #1: pipeline 1.1.0+abc1234 | GDD 1.3 (...) | agent codex | prompt none (...)
PRODUCER session exit=0: 12 card(s) filed or refreshed
CHECK_CARD 0 problem(s) after 1 Producer cycle(s)
START build UE-0.1 #7 role=<role>
PR #8 opened for UE-0.1 (ue-0.1-...)
REVIEW UE-0.1 PR #8: approve
MERGED UE-0.1 PR #8 at 1a2b3c4d5e6f: 2 CI check(s) green, reviewer approved, check_pr 0 problems
```
What that means: one agent (the Producer) turns the plan into cards (GitHub issues). Then kickoff gives each ready
card to a fresh agent session, which does the work and commits. Kickoff pushes it and opens a PR. A second
agent reviews the PR and posts `approve` or `changes`. When the PR is approved, its CI checks are green and
`check_pr` passes, kickoff merges it and closes the card. It runs 2 cards at a time.
- Long quiet stretches are normal. One agent session can take 5 to 30 minutes or more.
- To watch it work: open the repo's **Issues** and **Pull requests** tabs on GitHub, or open the newest
  `session.log` under `.pipeline\outbox\` in the repo folder.
- It never closes a gate or submits the game. Those always wait for a person. `WAITING on CI` means a PR is
  approved and kickoff is waiting for its checks before it merges.
- Agents and kickoff do all the build work, gate patches and repo settings included. You do two things: the itch
  upload and setting your API keys. A card that runs on the Windows packaging machine waits until kickoff runs
  there (`tools\kickoff.ps1` on that machine). Card 0.0 fills the People and Team hours rows for you from the repo's GitHub
  collaborators (`default (agent)`); edit your row if it is wrong. A `merge PR #N: ...` ask means
  kickoff could not merge it (the ask says why): fix that, then run it again.

It ends with: `KICKOFF idle: <n> session(s) this run, <m> new needs-human ask(s). Answer the needs-human queue, then
run tools\kickoff.ps1 again`. That means everything left is waiting on a person.

## 8. Answer a NEEDS HUMAN ask
A line `NEEDS HUMAN #7: <who> <what> <link>` means issue #7 on GitHub now has the `needs-human` label and a comment
saying what is needed. In the test repo, you are the human: answer them yourself.
1. Open the issue on GitHub. Do what it asks (it says why kickoff stopped: a card blocked after its retries, a merge
   it could not make, an upload).
2. Write a comment on the issue saying what you did.
3. Remove the `needs-human` label (right side of the issue page, **Labels**, untick it).
4. Run `tools\kickoff.ps1 --agent codex` again. It picks up where it stopped.
To list every open ask: `gh issue list --label needs-human`.
To keep kickoff running and checking for your answers every 10 minutes: add `--watch 10`.

## 9. Stop it
Press **Ctrl+C**. You see `kickoff: stopped by Ctrl+C. Run tools\kickoff.ps1 again to pick up where it stopped.`
That is safe. The next run continues from GitHub and its record. A session cut off midway runs again.

## 10. Record your prompt for A/B testing
Your prompt is your own instruction to the agents (for example "make the dash feel snappier"). Kickoff adds it to every
agent session and saves it in the run record, so you can compare two runs.
- Short prompt: `tools\kickoff.ps1 --agent codex --prompt "make the dash feel snappier"`
- Long prompt: type `notepad $HOME\Documents\my-prompt.txt`, write it, save, close. Then:
  `tools\kickoff.ps1 --agent codex --prompt-file $HOME\Documents\my-prompt.txt`
  Keep the file outside the repo folder so no agent commits it.
- The `RUN #<n>` line shows the run number and a code for your prompt. Write the run number down.
- After you play the build, record how it went: `py tools\journal.py run-outcome --run 3 --outcome pass`
  (the outcome is `pass`, `fail`, `partial` or `stopped`).
- Compare two runs: `py tools\journal.py compare 2 3`. Runs are saved on your computer only
  (`.pipeline\journal.db`), so compare runs you made on the same computer.

## 11. Test a different GDD version
The GDD (game design document) is the design the agents build from. The team's official one is the file named in
`docs\gdd\CURRENT`. To test another revision, give its number (like `1.4`) or the path of its `.md` file.
1. Check it first. This only reads files, it never changes anything:
   ```
   py tools\gdd_select.py "1.4" --check
   ```
   Keep the quotes around the number: without them PowerShell turns `1.10` into `1.1`.
   `1.4` finds `docs\gdd\GDD-1.4.md`, or else the `.md` file under `scratch\gdd\` whose `Revision` row says `1.4`.
   A path works too: `py tools\gdd_select.py scratch\gdd\v1.4\GameDesignDocument-v1.4.md --check`.
   - `OK, GDD 1.4 ... passes every import check.` and a `pipeline ... | GDD 1.4 (...)` line: go to step 2.
   - One `FIX <file>: <what to do>` line per problem, then `cannot be imported yet`: each line names the file to change
     and what to add. Send the lines to Josh. Never edit the GDD file itself; statuses and approved numbers are Richard's.
2. Run the pipeline on it:
   ```
   tools\kickoff.ps1 --agent codex --gdd "1.4"
   ```
   It checks the GDD again and stops if it fails. The `RUN #<n>` line and the run record show the GDD revision and the
   pipeline version, so `py tools\journal.py runs` lists which GDD each run used.
   This is for this run only: `docs\gdd\CURRENT` stays as it is. Add `--set-current` only when the team decides to
   switch to that revision (it then also changes `docs\gdd\CURRENT`; the file must be `docs\gdd\GDD-<rev>.md`).

## 12. Next time there is an update
Someone opens a PR named "Update MegaPipeline to <version>". Do parts 3, 4 and 6 again: merge it, pull, run.
The first line kickoff prints shows the new version. No PR? `MegaPipeline/INSTALL.md`, "Update an older install".

## 12. Play a different boss fight (practice builds only)
The owl fight is data in `pipeline/level/encounter.json`. GDD 1.3 is the default. To see the other fights:
```
py tools\encounter_check.py --presets --gdd 1.3
```
Ricky's fight is `OWL-FIGHT-RICKY`. It is a proposal for Richard to decide, so it loads only in a practice or
workbench build: set `UmbrellaElla.Encounter.Preset=OWL-FIGHT-RICKY` there. The normal build always plays GDD 1.3.

## When something goes wrong
Every problem prints one line starting with `kickoff:` that says what to type next. The common ones:
- `running scripts is disabled on this system`: do part 1, step 3.
- `this window is inside an agent session`: open a new PowerShell from the Start menu and run it there.
- `before the jam start ... PRE-JAM mode runs only the pre-jam cards`: normal on the team repo before Nov 12. In a test repo add `--practice` (part 6).
- `practice mode starts on the main branch`: type `git checkout main`, then run it again.
- `the pipeline is not fully installed`: type `git pull origin main`, then run it again.
- `RETRY UE-... builder: <reason>; it runs again now`: a session crashed, timed out or did nothing; kickoff runs it
  once more by itself. Nothing to do.
- `BLOCKED UE-...: 2 builder sessions failed in a row: <reason>`: the card now has a NEEDS HUMAN ask with the reason;
  open that card's `session.log` and send it to Josh.
- `kickoff: journal not written (...)`: the run goes on without its local record; send the line to Josh.
- `KICKOFF FAILED: ...`: something with no card to ask on failed twice (the Producer session); send the line to Josh.
- `kickoff: stopped by an unexpected error`: type `tools\kickoff.ps1 --check` and send the output to Josh.

## Mac
Same steps with these changes: install with `brew install git git-lfs python gh node`; skip part 1, step 3; type
`tools/kickoff.sh` instead of `tools\kickoff.ps1`, `python3` instead of `py`, and `/` instead of `\` in paths.
Blender.app in /Applications is found by itself. Audio keys: `export ELEVENLABS_API_KEY="..."` in `~/.zshrc`, or `python3 tools/keys.py status` for the keychain way.
