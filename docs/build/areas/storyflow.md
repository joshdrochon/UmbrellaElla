# Story wiring in flow. Branch area/storyflow. Read docs/build/worker-rules.md first. Orphan Rule IDs from the audit (docs/build/rule-status.csv on area/audit, fd2bdd6; notes there say what is missing).
IDs: NAR-04 (flow calls the story skip handling: IsSkipPressForStory/HandleSkipPressed), NAR-07 and FLOW-49 (one ending
timeline: the story's living-departure ending and credits, then Journey Complete statistics in Director's Cut; flow and
story no longer run two separate timelines). NAR-05's light shaft/umbra visual belongs to artfx; you wire its trigger.
Lane: Flow/** (ending and skip logic only; artui edits widget paint code, do not restyle), Story/**, their tests.
