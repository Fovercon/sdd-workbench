# Identifier presentation and count totals

Version: 1
Status: APPROVED (synthetic fixture baseline only)

Inputs are eight ASCII digit identifier strings, or lists of nonnegative
integer counts as specified below. Invalid input policy is outside this change.

- FR-001 / AC-001: export_row(value) returns a dict with exactly the identifier
  field; its value follows C-001. No input mutation or persistence.
- FR-002 / AC-002: audit_label(value) returns `audit:` followed by the identifier
  presentation specified by C-001. It does not call export_row.
- C-001: in both export and audit presentations, replace the leading four
  identifier characters with `*` and retain the last four characters.
- FR-003 / AC-003: sum_counts(values) returns the arithmetic sum; an empty list
  returns zero. This behavior receives integers, not identifiers, and must not
  mutate inputs. Identifier presentation has no role in it.

Public function names and return shapes remain stable. No database, service,
dependency, UI, deployment or release change is requested.
