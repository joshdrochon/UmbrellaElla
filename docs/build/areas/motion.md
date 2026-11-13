# Reduced motion everywhere (FLOW-45). Branch area/motion. Read docs/build/worker-rules.md first.
settings2 stores reduced motion and exposes a read API (Settings/ accessibility reader), but the screens and effects that move
do not read it yet. Make each one read it at the point of use, in the submission build too: camera shake and scroll lead
(Arena/, Level/), screen flashes and effect intensity (Feedback/ VFX, already wired for reduced flash), HUD hand motion
(UI/HUD), menu transitions (UI/Menus, Flow/). No behaviour change with reduced motion off. Tests: with it on, each reader
reduces its motion; with it off, unchanged. Lane: only the reading lines in those folders, plus tests. Done: worker-rules DoD.
