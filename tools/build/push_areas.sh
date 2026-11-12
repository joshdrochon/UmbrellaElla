#!/usr/bin/env bash
# Push every local area/* branch to origin when it has new commits (WIP included), so a teammate can pick up any branch.
# Usage: tools/build/push_areas.sh          once
#        tools/build/push_areas.sh --loop   every 120 s until killed (Mac build lead runs this in the background)
cd "$(git rev-parse --show-toplevel)" || exit 1
push_once() {
  for b in $(git for-each-ref --format='%(refname:short)' refs/heads/area/); do
    l=$(git rev-parse "$b"); r=$(git rev-parse -q --verify "refs/remotes/origin/$b" || echo none)
    if [ "$l" != "$r" ]; then git push -q origin "$b:$b" 2>&1 | tail -1; echo "$(date +%H:%M) pushed $b ${l:0:7}"; fi
  done
}
if [ "${1:-}" = "--loop" ]; then while :; do push_once; sleep 120; done; else push_once; fi
