# Intake plan v1

Status: APPROVED (fictional fixture authority only).
One standard-library module, public intake(records, destination) -> list[str].
RejectedRecord subclasses ValueError. Records are already schema-conforming.
Filter ~ names, validate supported kinds across the entire remaining batch,
then mkdir and iterate file records. Name policy stays inside that write loop.
Name timing: LATE; do not move its rejection into preflight or add rollback.
No new configuration, engine, helper layer, manifest or dependency is needed.
Verification: focused RED/GREEN plus full unittest discovery. Use temporary roots.
Existing green tests cover examples, not every kind value or all failure timing.
