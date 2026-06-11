# GMEA Peer-Review Response Matrix v0.8

| Review item | v0.8 action |
| --- | --- |
| Release v0.7 publicly as conformance-testable candidate | Advanced package to v0.8 after incorporating release-polish items; still pre-1.0. |
| Rename schema to `.sql` and mark normative | Created `GMEA_schema_v1_candidate_v0_8.sql` with normative v0.8 header. |
| Add missing indexes | Added `idx_event_block_sequence` and `idx_skim_block`. |
| Clarify PHYS-HYBRID authority | Whitepaper, PEB spec, semantic-hash spec, schema, and validator now state/enforce that relational event tables are absent or non-authoritative under PEB/HYBRID. |
| Add schema file to conformance manifest | Added `schema_file` to `GMEA_conformance_suite_manifest_v0_8.json`. |
| Add schema verification mode | Added `schema-verify` command to `GMEA_reference_validator_v0_5.py`; output included. |
| Include validator outputs | Added positive, negative, decode-block, and schema-verify output JSON files. |
| Add missing-skim negative vector | Added `GMEA_negative_v0_8_missing_skim.gmea` and expected output. |
| Keep v0.8 pre-1.0 | All v0.8 docs label the package as pre-1.0 conformance-testable candidate. |
