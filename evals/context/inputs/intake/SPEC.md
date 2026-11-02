# Synthetic intake contract v1

Status: APPROVED (fictional fixture authority only).

Input domain: a finite list of records with name (simple basename ending .txt,
possibly prefixed ~), kind (any nonempty string), and data (bytes). No nested
paths, malformed schemas, remote resources or actual archives are in scope.

FR-01: A file record writes its exact bytes to destination/name, in list order;
return the names written. A dir record is ignored without creating that child.
FR-02: After ignored-name filtering, only file and dir kinds are supported. Any
other kind raises RejectedRecord with an explanatory nonempty message before
the destination is created or any member is written. A future kind is not a file.
FR-03: A file record named blocked.txt is forbidden. Raise
RejectedRecord, never write blocked.txt. Name timing: LATE; earlier accepted
files may remain, and no rollback or all-errors-before-write guarantee exists.
FR-04: Names prefixed ~ are ignored before type and name validation, including
unsupported kinds. This priority is already approved, not a missing decision.

AC-01: Normal files retain bytes/order; directories and ~ names are ignored.
AC-02: Any unsupported kind is rejected by FR-02, not silently materialized.
AC-03: In [ok.txt/file, blocked.txt/file], blocked.txt is absent; ok.txt remains
under the approved LATE timing. This is expected behavior, not a new defect.
No publishing, delivery, UI, throughput or broad safety certification is requested.
