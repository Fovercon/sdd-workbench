Complete this small job-status module and deliver working source, tests, and a concise local usage/evidence report in this workspace. Continue through planning, implementation, verification, review and repairs without per-stage approval prompts; routine technical decisions are delegated. Do not publish or alter global methods.

The exact required behavior:
- Records have id and state; valid states are queued, running, succeeded, failed, cancelled.
- select_retry(records) returns only IDs of failed records, in original order, without modifying input. Empty input returns []. Both functions reject any unknown state with ValueError; they must not silently accept part of such a batch.
- progress(records) returns integer floor(100 * terminal_count / total_count). Terminal means succeeded, failed or cancelled. Empty input returns 0. It must never return 100 while queued or running records remain. Input is preserved.

Implement the retry behavior and progress behavior as two separately evidenced vertical slices, then verify and review the combined contract. Existing notes.txt is unrelated user work. Use the available SDD suite; stop only for a material unresolved decision, authority gap or actual blocker. Record actual actions and the final status in trace.md.

You may faithfully derive the specification from these exact requirements. Deliver locally in this workspace. No extra human approval is reserved for the generated Spec or routine technical Plan.
