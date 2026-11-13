# Settings contents. Branch area/settings2. Read docs/build/worker-rules.md first. Orphan Rule IDs from the audit (docs/build/rule-status.csv on area/audit, fd2bdd6; notes there say what is missing).
IDs: FLOW-44 (developer menu contents are OPEN in the GDD: pick the GDD's candidate options as an agent default, record a
decision row, build them Director-only behind the flag) and FLOW-45 (text scale and reduced motion stored but not read:
expose them through a settings API and make gameplay-side readers use reduced motion (camera shake, flashes); the UI text
scale itself is read by the artui area's shared UI style: write the request in your requests file, settings2.md under docs/build/requests).
Lane: Settings/**, UI/Settings/**, Tests/Settings/**, plus the reader lines in Field/** or Feedback/** camera shake only.
