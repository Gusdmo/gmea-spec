# GMEA v0.8 Release Notes

Status: public pre-1.0 conformance-testable candidate.

## What changed from v0.7

- Renamed the schema asset to `GMEA_schema_v1_candidate_v0_8.sql`.
- Marked the schema as normative DDL for v0.8 PHYS-HYBRID conformance testing.
- Added minimal C3+ forensic tables to the candidate schema: time rebase profile, offset segments, source artifact, coverage segment, audit event, finalization manifest, and signature hook.
- Added `idx_event_block_sequence` and `idx_skim_block` indexes.
- Added explicit PHYS-HYBRID authority comments: relational event rows are absent or non-authoritative when PEB/HYBRID is declared.
- Added validator `schema-verify` mode.
- Added missing-skim negative vector.
- Added validator JSON outputs for all positive and negative vectors.
- Updated documentation to point to the exact v0.8 schema and validator assets.

## Still pre-1.0

Remaining work includes broader profile coverage, public benchmarks, signature verification implementation, a C5 virtual-table prototype, and independent implementation feedback.
