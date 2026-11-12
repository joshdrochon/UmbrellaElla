#!/usr/bin/env bash
# Stand-in for the packaged game in tests/test_honest_jam.py. The RunUAT stub "compiles" it (compile_stub.py): the
# line below becomes the values a real binary has built in (commit, workbench, platform, the live `// bake:` values).
# It never reads BUILD_INFO.txt. HOOK=0: a build before card 0.6 (no smoke hook): it only runs until closed. HOOK=1
# follows the smoke hook contract in tools/ue_run.py (SMOKE_OK, SMOKE_EFFECTIVE at=start and at=end, SMOKE_TITLE). INPUT=none: before
# MVP 2 (no umbrella input yet). INPUT_VZ: the Z velocity it measures while holding IA_Attack (GDD 1.3 ATTACK_DESCENT
# falls). A map named *StyleFrame* or L_Title has no player (input=none). With a title screen (card 0.21) and a hook
# that cannot pass it, input never reaches the umbrella (input=none).
# @COMPILED@
L=; X=1920; Y=1080; W=windowed; M=L_Graybox; C=0; R=; CRASH=; SHOT=; NOLOCK=; DD=0
for a in "$@"; do case "$a" in
  -abslog=*) L="${a#-abslog=}";; -ResX=*) X="${a#-ResX=}";; -ResY=*) Y="${a#-ResY=}";;
  -ReportExportPath=*) R="${a#-ReportExportPath=}";; -fullscreen) W=fullscreen;; -windowed) W=windowed;;
  -SmokeMap=*) M="${a#-SmokeMap=}"; M="${M##*/}";; -SmokeRestartCycles=*) C="${a#-SmokeRestartCycles=}";;
  -SmokeCrash) CRASH=1;; -SmokeShot=*) SHOT="${a#-SmokeShot=}";; -SmokeNoAspectLock) NOLOCK=--no-lock;;
  -SmokeDebugDraw) DD=1;;
esac; done
D="$(cd "$(dirname "$0")" && pwd)"
if [ "${HOOK:-1}" = "0" ]; then trap "exit 0" TERM; sleep 60 & wait; exit 0; fi
if [ -n "$R" ]; then
  mkdir -p "$R"
  echo '{"tests":[{"fullTestPath":"UmbrellaElla.Flow.TitleToPlayToSurvived","state":"Success","duration":38.2}]}' > "$R/index.json"
  [ -n "$L" ] && echo "LogAutomation: done" > "$L"
  exit 0
fi
[ -n "$CRASH" ] && mkdir -p "$D/UmbrellaEllaData/Saved/Crashes/forced$$"
: > "$L"
echo "[2026.11.12-19.14.03:000][  0]LogInit: Build: ++UE5+Release-5.8" >> "$L"
echo "[2026.11.12-19.14.03:001][  0]LogInit: Command Line: $*" >> "$L"   # as UE logs it (final-10 B M1)
[ "$WB" = "1" ] && echo "[2026.11.12-19.14.03:010][  0]LogUmbrellaElla: WORKBENCH_ON debug=1" >> "$L"
M_EFF="manifest=$MANIFEST"; [ -z "$MANIFEST" ] && M_EFF=""
echo "[2026.11.12-19.14.04:000][  1]LogUmbrellaElla: SMOKE_EFFECTIVE at=start commit=$COMMIT workbench=$WB platform=$PLATFORM $M_EFF $EFFECTIVE" >> "$L"
i=1; while [ "$i" -le "$C" ]; do
  echo "[2026.11.12-19.14.1$i:000][$i]LogUmbrellaElla: SMOKE_EFFECTIVE at=end outcome=fail commit=$COMMIT workbench=$WB platform=$PLATFORM $M_EFF $EFFECTIVE_END" >> "$L"
  echo "[2026.11.12-19.14.1$i:000][$i]LogUmbrellaElla: SMOKE_CYCLE n=$i actors=12 health=100 load_ms=900" >> "$L"; i=$((i + 1))
done
echo "[2026.11.12-19.14.18:001][904]LogUmbrellaElla: SMOKE_EFFECTIVE at=end outcome=quit commit=$COMMIT workbench=$WB platform=$PLATFORM $M_EFF $EFFECTIVE_END" >> "$L"
IN="input=ok input_vz=${INPUT_VZ:--140} gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=none"
case "$M" in *StyleFrame*|L_Title) IN="input=none";; esac
[ "${INPUT:-ok}" = "none" ] && IN="input=none"
if [ "$TITLE" = "1" ] && [ "$IN" != "input=none" ]; then
  if [ "$SKIP" = "1" ]; then echo "[2026.11.12-19.14.05:000][  2]LogUmbrellaElla: SMOKE_TITLE skipped=UUmbrellaTitleScreen::StartPlay" >> "$L"
  else IN="input=none"; fi
fi
# the measured view: the largest 16:9 box in the window (the camera's aspect lock), the window without it
if [ -n "$NOLOCK" ]; then VW=$X; VH=$Y; elif [ $((X * 9)) -gt $((Y * 16)) ]; then VW=$(( (Y * 16 + 8) / 9 )); VH=$Y
else VW=$X; VH=$(( (X * 9 + 8) / 16 )); fi
ASP=$(awk "BEGIN{printf \"%.3f\", $VW/$VH}")
if [ -n "$SHOT" ]; then   # the default-build screenshot: this stand-in game looks like the key art
  python3 "$FAKE_SHOT" "$SHOT" "$X" "$Y" --keyart $NOLOCK
  echo "[2026.11.12-19.14.08:000][300]LogUmbrellaElla: SMOKE_SHOT at_s=5 w=$X h=$Y" >> "$L"
fi
echo "[2026.11.12-19.14.18:002][905]LogUmbrellaElla: SMOKE_OK map=$M fps=58.4 worst_ms=24.1 commit=$COMMIT $IN res=${X}x${Y} win=$W view=${VW}x${VH} aspect=$ASP debugdraw=$DD textpx=20 load_ms=2140 workbench=$WB" >> "$L"
exit 0
