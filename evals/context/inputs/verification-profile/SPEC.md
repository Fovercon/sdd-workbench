# Repair request summary SPEC v2

Status: APPROVED (synthetic baseline only)

FR-01: The offline summary service accepts one request with request_id and text.
It returns exactly request_id (same string) and summary (nonempty string), JSON.
FR-02: Summary meaning follows DOMAIN revision2. Equivalent wording is allowed;
no exact reference prose is mandated. Critical false commitments and changed
quantities must be distinguished from stylistic preference.
FR-03: Evidence must keep structural validity, semantic quality and reviewer
disagreement separate, with actual sample roles and version identities.
AC-01: A valid JSON reply with a false deadline does not establish semantic pass.
AC-02: A faithful paraphrase need not equal a reference string to pass.
AC-03: Revision1 labels do not certify revision2; their disagreement with current
meaning must remain visible rather than silently relabeling past evidence.
NFR-01: Local/PR validation must be deterministic and offline. Model execution
and held-out evaluation need separate authorization; none is granted in this task.
Non-goals: production data, UI, model selection, load tests, implementation,
automatic deployment or a universally representative benchmark.
