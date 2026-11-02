# Unified local result catalog v1
Status: APPROVED synthetic target except any explicitly unresolved semantic.
No technical Plan has been approved. Only planning is authorized.

FR-01: Add a local unified read/admission boundary for web and batch result catalogs.
Keep legacy web_rows(path) and batch_rows(path) public return shapes and behaviors
compatible during transition. Reuse verified existing behavior where it meets the
contract; internal storage format and module choices are technical design choices.
FR-02: Identity is (origin, exact id), with origin web or batch. Same ID in different
origins represents two records. Preserve order within each origin; cross-origin
interleaving is unspecified. Preserve raw text in storage. Web display preserves
leading/trailing spaces; batch display strips them exactly as today. Do not globally
normalize stored text. IDs and texts are strings; no new normalization is approved.
FR-03: Preserve origin-specific state meaning in the new representation: web/done means converted; batch/done means delivered. Retain origin and raw state so neither claim becomes the other.
FR-04: Import both frozen legacy files into a separate explicit new target. Preserve
source bytes and every logical record, origin, ID, raw text and raw state. A failed
import (invalid JSON, invalid record, unknown state or conflicting same-origin ID)
exposes no partially imported target. Exact duplicates within one origin coalesce;
same-origin ID with differing text/state conflicts. The initial target must be empty
or absent. A completed exact same-source rerun is safe and preserves later new-target
admissions; different-source replay is rejected, never merged by guessing. Input
file order is source order; keep the first position for an exact duplicate.
FR-05: Operators can stop all writers for import and cutover verification. This
scope has no overlapping writers, background sync, execution scheduler, plugin
registry, network service, power-loss guarantee or remote filesystem support.
After switch, new-target admission successes must survive normal close/reopen;
same identity/same content retry is idempotent, conflicting retry fails unchanged.
FR-06: Before first successful new-target admission, operator rollback may return
to the byte-identical legacy files with writers stopped. After a new admission,
restoring the old snapshot alone would lose acknowledged data and is not an approved
rollback. Keep the new target and stop/repair forward; any lossless reverse migration
requires a separately specified and verified contract before it can be offered.
The Plan must identify the guard that separates these two operational states.

AC-01: Both origins contain ID '7'; both remain, with web text '  Alpha  ' and batch
raw text '  Beta  '. Legacy displays remain '  Alpha  ' and 'Beta', respectively.
AC-02: Legacy web/done reports converted; batch/done reports delivered. A unified
result must not imply a delivery claim for web or only conversion for batch.
AC-03: Import/refusal/replay, mixed validity, unknown states, exact duplicates and
conflicting identities preserve FR-02/04; readback verification precedes switch.
AC-04: A new acknowledged admission followed by reopen and an attempted snapshot
rollback cannot lose that admission. Prove the FR-06 guard, not just a backup path.

Excluded: running these checks during planning, approving the design, changing
legacy semantics, deleting old files or automatically migrating real installations.
