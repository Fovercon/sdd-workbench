# Third-party notices

The project-view renderer includes Mermaid 12.2.0 as a compressed offline browser
asset. Preserve the upstream license and bundled dependency notices when distributing it:

- [MIT license](skills/sdd-workflow-router/scripts/project_view_lib/vendor/MERMAID-LICENSE)
- [Source and integrity metadata](skills/sdd-workflow-router/scripts/project_view_lib/vendor/provenance.json)

The original JavaScript is stored in `mermaid-12.2.0.min.js.gz`; decompression does
not modify its bytes. Its notices are also retained in the rendered board.

Suite material was extracted from Fovercon/AI-Native-SDD. The exact source identity
and portability edits are recorded in [UPSTREAM.json](docs/UPSTREAM.json).
No project-wide open-source license has been selected in this initial package;
the third-party MIT notice above applies to the bundled Mermaid asset.
