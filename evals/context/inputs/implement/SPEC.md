# Synthetic Spec v1
Status: APPROVED (fixture state only).
FR-1: select(items, key) returns only records whose string id equals key exactly.
No substring matching, case folding or whitespace normalization.
FR-2: No matching id returns an empty list.
FR-3: Keep input order and original record identities; do not modify input data.
Inputs contain dictionaries with string id fields. Malformed records are outside S1.
