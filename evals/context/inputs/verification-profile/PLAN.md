# Summary service PLAN v2

Status: APPROVED (synthetic baseline only)

P-01: Public boundary summarize(request) uses an external generate(request) adapter.
Owned code validates request_id/text and response shape and preserves request_id.
Generate emits a candidate summary; format rejection and content assessment are
distinct. An offline adapter substitute controls deterministic response/error cases.
P-02: Future semantic evaluation records input/candidate versions, DOMAIN revision,
rubric identity, sample IDs/split, generator/judge identities, per-dimension labels,
reviewer decisions, unresolved/adjudicated items and actual execution provenance.
No test implementation or current-run evidence exists yet.
P-03: data/examples.jsonl is development/calibration material, not held-out.
data/reviews.json preserves independent reviewer observations and old labels;
none of the actors are authorized to overwrite it. A future owner-custodied sealed
set is described only by data/dataset.json. Its content and labels are unavailable
here; do not invent them or claim they have been evaluated.
P-04: Reuse the existing verification design format in VERIFICATION.md. Define a
profile as an identified set of domain rules, data roles and evidence decisions;
no new service/schema framework, fixed document suite or live benchmark is needed.
