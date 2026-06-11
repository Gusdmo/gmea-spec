# GMEA v0.8 — Public Conformance-Testable Candidate

**Status:** pre-1.0 public conformance-testable candidate.

GMEA, the **Generalized Market Event Archive**, is a single-file `.gmea` archive format for forensic market-event data. GMEA v0.8 uses SQLite as its normative v1 container profile and PHYS-HYBRID Packed Event Blocks (PEB) as the default C3+ forensic physical profile.

This release is intended for external implementers to validate readers, writers, decoders, and conformance tooling. It is **not** v1.0; feedback and independent implementation reports are expected before v1.0.

## Release Contents

Core specification documents:

- `GMEA_whitepaper_peer_review_draft_v0_8.md`
- `GMEA_packed_event_blocks_spec_v1_0_candidate_v0_8.md`
- `GMEA_semantic_hash_spec_v1_0_candidate_v0_8.md`
- `GMEA_schema_v1_candidate_v0_8.sql`
- `GMEA_v0_8_conformance_test_plan.md`
- `GMEA_v0_8_release_notes.md`
- `GMEA_peer_review_response_matrix_v0_8.md`

Reference tooling:

- `GMEA_reference_validator_v0_5.py`

Conformance metadata:

- `GMEA_conformance_suite_manifest_v0_8.json`
- `GMEA_v0_8_validation_summary.json`
- `GMEA_negative_corpus_v0_8_expected.json`

Positive test archives:

- `GMEA_conformance_positive_peb_uncompressed_v0_8.gmea`
- `GMEA_conformance_positive_peb_deflate_v0_8.gmea`

Negative test archives:

- `GMEA_negative_v0_8_corrupted_payload.gmea`
- `GMEA_negative_v0_8_skim_mismatch.gmea`
- `GMEA_negative_v0_8_missing_skim.gmea`
- `GMEA_negative_v0_8_noncanonical_header.gmea`
- `GMEA_negative_v0_8_unsupported_compression.gmea`
- `GMEA_negative_v0_8_malformed_stream_length.gmea`
- `GMEA_negative_v0_8_wrong_stream_count.gmea`
- `GMEA_negative_v0_8_invalid_event_uuid.gmea`
- `GMEA_negative_v0_8_invalid_block_uuidv7.gmea`
- `GMEA_negative_v0_8_merkle_mismatch.gmea`

Precomputed validator outputs are included for both positive and negative vectors.

## Quick Start

Run from the release directory with Python 3.10+.

Validate the positive uncompressed archive:

```bash
python GMEA_reference_validator_v0_5.py validate GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
```

Verify that the archive schema matches the v0.8 candidate schema expectations:

```bash
python GMEA_reference_validator_v0_5.py schema-verify GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
```

Decode the first PEB block from the positive uncompressed archive:

```bash
python GMEA_reference_validator_v0_5.py decode-block GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
```

Validate the positive DEFLATE archive:

```bash
python GMEA_reference_validator_v0_5.py validate GMEA_conformance_positive_peb_deflate_v0_8.gmea
```

Validate a negative archive. This should fail closed with the expected error:

```bash
python GMEA_reference_validator_v0_5.py validate GMEA_negative_v0_8_missing_skim.gmea
```

## Expected Results

The v0.8 release candidate expects:

- positive archives: **PASS**;
- negative archives: **fail closed** with the errors recorded in `GMEA_negative_corpus_v0_8_expected.json`;
- `schema-verify`: **PASS** on positive archives;
- `decode-block`: emits a typed canonical event stream projection.

## Normative Schema

The normative DDL for v0.8 PHYS-HYBRID conformance testing is:

```text
GMEA_schema_v1_candidate_v0_8.sql
```

The schema defines the minimum tables required for v0.8 PEB validation, including `event_block`, `event_skim_l1_quote`, `event_block_merkle_root`, source/instrument identity tables, time-rebase metadata, source artifacts, coverage segments, finalization metadata, and signatures.

## Physical Profile

GMEA v0.8 uses:

```text
GMEA-PHYS-HYBRID-v1
```

as the default C3+ forensic profile.

PHYS-HYBRID combines:

- SQLite relational metadata and forensic control tables;
- Packed Event Blocks stored as immutable BLOB payloads;
- block-level skim tables for coarse SQL filtering;
- Merkle roots for C3+ verification.

## Important Pre-1.0 Notes

GMEA v0.8 is intentionally **not** v1.0. Remaining pre-1.0 work includes:

- broader profile coverage beyond the current L1 quote PEB corpus;
- public benchmark corpus publication;
- signature verification implementation;
- C5 virtual-table prototype;
- independent implementation feedback.

## Suggested Public Release Title

```text
GMEA v0.8 — Public Conformance-Testable Candidate
```

## Suggested Licensing

Recommended release licensing:

- specification documents: CC BY 4.0;
- reference code and validator: Apache-2.0.

Final license selection should be made by the project owner before public repository publication.
