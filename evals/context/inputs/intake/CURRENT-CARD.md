# S1 revision1 — reject unsupported record kinds

Authority: user explicitly authorizes this one local repair and required checks.
Spec/Plan: current v1; prerequisite S0 complete. Mode: RED_GREEN.
Objective: unsupported kinds can no longer enter the file-writing path.
Surface: intake.py, tests/, IMPLEMENTATION.md. Other sources stay unchanged.
Stop condition: FR-02 demonstrated; FR-01/03/04 preserved; focused and full
regression pass; a concise receipt states actual behavior, evidence and limits.
Do not alter the approved name timing, ignore priority, output shape or exception.
First add a behavior test that fails for the unsupported-kind defect, then fix it.
Full regression: python3 -B -m unittest discover -s tests -v.
Receipt: IMPLEMENTATION.md using the skill's existing receipt guidance; no new
artifacts or execution cards. No commit/push/install/release authority.
