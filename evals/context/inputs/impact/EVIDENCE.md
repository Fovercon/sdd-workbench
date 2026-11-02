# Controller observation on synthetic v1 code and assertions

During fixture construction the controller ran, from this project directory:

    python3 -B -m unittest discover -s tests -v

Observed result (2026-10-27):

    test_audit_v1 ... ok
    test_counts ... ok
    test_export_v1 ... ok
    Ran 3 tests
    OK

TC-EXPORT and TC-AUDIT assert four retained characters. TC-COUNT asserts count
summation, empty input and input preservation. These are scoped local results,
not production verification or permission to claim another contract version.
The historical source receipt binds SPEC.md to its v1 bytes, even when a later
scenario supplies a changed current SPEC.md. Original v1 bytes remain archived.
