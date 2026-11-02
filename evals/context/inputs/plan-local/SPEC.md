# Export filtering v1
Status: APPROVED (synthetic fixture state only, not Plan approval).

FR-01: Extend exporter.export(rows) with optional keyword-only id_filter=None.
None means all records; any string, including empty string, selects exact ID equals.
Matching is case-sensitive, whitespace-significant, never substring matching.
FR-02: Keep the existing id,title CSV header, quoting, CRLF rows and input order.
Keep original record identities and values unchanged. No matches still gives header.
Inputs are lists of dictionaries with string id and title; validation of other
input types is excluded. No sorting, persistence, CLI or new formats are requested.
AC-01: Omitted/None filter matches existing output bytes for every valid input.
AC-02: Filter A selects both A records, not XA/a/space-prefixed/suffixed IDs.
AC-03: Empty filter selects empty ID, and no match returns the header alone.
AC-04: Values needing CSV quotes still round-trip; input values/order/identities stay.

This replaces no other repository behavior. Design approval remains pending.
