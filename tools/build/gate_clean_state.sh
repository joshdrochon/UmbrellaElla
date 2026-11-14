#!/usr/bin/env bash
# Sourced by gate.sh (and its self-test). Josh, Nov 13 19:4x: the gate must never fail good work over its own leftovers.
# clean_state <worktree>: before (and after) every gate step that launches the game (Unreal tests, the visual_qa capture,
# critics that play), wipe the game's persistent player state in the gate worktree and reset settings to the main
# checkout's copy, so no step can leave state for the next (Nov 13 19:31-19:42: a progress save written by a visual_qa
# capture made Flow.World.LevelUpShowsAndResumes open the purchase screen and failed three good merges, the owl among them).
clean_state() {
  local w="${1:?worktree}" root="${GATE_STATE_ROOT:-$ROOT}"
  rm -rf "$w/Saved/SaveGames" "$w/Saved/Story"
  mkdir -p "$w/Saved/Config/MacEditor"
  if [ -n "$root" ] && [ -f "$root/Saved/Config/MacEditor/GameUserSettings.ini" ]; then
    cp -f "$root/Saved/Config/MacEditor/GameUserSettings.ini" "$w/Saved/Config/MacEditor/GameUserSettings.ini"
  fi
  rm -f "$w/Saved/Config/Mac/GameUserSettings.ini" 2>/dev/null
  return 0
}
