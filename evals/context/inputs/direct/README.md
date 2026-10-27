# Identifier selection

select(items, key) returns every input record whose string id equals key exactly.
Keep input order and original objects. Do not mutate inputs, normalize case or trim
whitespace. No match returns an empty list. Inputs have string id fields.
