#!/usr/bin/env bash
# Independent review of one gate merge (Josh, Nov 12): a fresh Claude Code session that is not the build lead and not
# the area worker. Runs in the gate checkout, reads the merge diff against the area brief and the GDD Rule IDs, with the
# role card for the area's domain. Ends with "VERDICT: approve" or "VERDICT: changes" and a list.
# Usage: tools/build/review.sh <area> <evidence-file> <out-file>      (run from the gate checkout)
set -u
A="$1"; EV="$2"; OUT="$3"
case "$A" in
  keeper) ROLE=game-designer ;; enemies) ROLE=encounter-designer ;; visuals) ROLE=art-director ;;
  arena) ROLE=level-designer ;; story) ROLE=story ;; flow|settings) ROLE=ui-ux ;; *) ROLE=dev-lead ;;
esac
CARDS="pipeline/roles/$ROLE.md"
git diff --name-only HEAD^1 HEAD | grep -q '^Source/' && [ "$ROLE" != dev-lead ] && CARDS="$CARDS and pipeline/roles/dev-lead.md (C++ changed)"
git diff --name-only HEAD^1 HEAD | grep -q '^Audio/' && CARDS="$CARDS and pipeline/roles/audio.md (sound changed)"
PROMPT="You are the independent reviewer for one merge into Umbrella Ella's main branch. You did not write this code
and you are not the build lead. Do not edit, commit or push anything; read only.
Your role cards: $CARDS. Follow their review rules, adapted: there is no PR, the merge diff is \`git diff HEAD^1 HEAD\`
in this checkout, the area brief is docs/build/areas/$A.md (its Rule IDs and definition of done) and the rules every
area follows are docs/build/worker-rules.md. Check the diff against the GDD rows of those Rule IDs
(docs/gdd/GDD-SH1.0.md, docs/feature-manifest.json). The gate evidence (build, tests, checks) is in $EV; do not rerun
Unreal. Report real problems only: wrong behaviour against the GDD, bugs, broken contracts between areas, rule
violations a reader can see. Each with file:line, why, and the fix. Put style nits under 'Minor:'.
End your answer with exactly one line 'VERDICT: approve' or 'VERDICT: changes', then the numbered list of changes
(empty for approve), then 'Minor:' and its list."
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT claude -p "$PROMPT" --permission-mode bypassPermissions \
  --disallowedTools "Bash(git push:*)" "Bash(git commit:*)" Edit Write --model "${REVIEW_MODEL:-claude-sonnet-5-5}" > "$OUT" 2>&1
grep -q "^VERDICT: approve" "$OUT" && { echo "review: approve role=$ROLE"; exit 0; }
if grep -q "^VERDICT: changes" "$OUT"; then
  # "changes" with no numbered item after the verdict line (only Minor:) counts as approve with follow-ups.
  if sed -n '/^VERDICT: changes/,/^Minor/p' "$OUT" | grep -q -E '^[0-9]+\.'; then echo "review: changes role=$ROLE ($OUT)"; exit 1; fi
  echo "review: approve (minor only) role=$ROLE ($OUT)"; exit 0
fi
echo "review: no verdict role=$ROLE ($OUT)"; exit 2
