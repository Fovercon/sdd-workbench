# Design contract v1

Status: APPROVED (synthetic baseline)
Prepared against: SPEC v1, C-001, FR-001/002/003 and AC-001/002/003.

- D-MASK: presentation.py::mask_identifier retains four trailing characters.
  export_row and audit_label both call it. This shared dependency realizes C-001
  for two independently observable outputs; neither calls the other.
- D-COUNT: presentation.py::sum_counts directly sums count values. It calls no
  identifier helper, consumes no identifier configuration and has no shared
  mutable state with D-MASK.

Keep these public interfaces and shapes. An identifier policy change must be
checked against both consumers. Other changes need their own authority.
