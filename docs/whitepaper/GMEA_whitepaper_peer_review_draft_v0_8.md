# GMEA — Generalized Market Event Archive

## Whitepaper peer-review draft v0.8: public conformance-testable candidate

Status: pre-1.0 public conformance-testable candidate. GMEA v0.8 is intended to be released for external implementer feedback. It does not declare GMEA 1.0.

Version 0.8 packages the normative PHYS-HYBRID conformance core: a complete candidate schema file, reference validator/decoder, positive and negative `.gmea` archives, expected JSON outputs, and a conformance manifest. The purpose of v0.8 is to let an independent implementer run the test suite and determine whether a reader/validator agrees with the reference implementation.

## Abstract

GMEA is a single-file, SQLite-contained archive format for immutable raw market events. It preserves original source evidence, supports lossless source-time to canonical-UTC rebasing, verifies append-only batch semantics, and supports authenticity through semantic hashes and signatures. GMEA uses SQLite as a relational metadata and control-plane container, while high-volume event data is stored in Packed Event Blocks (PEB): compact columnar binary payloads embedded in SQLite BLOBs. The v0.8 candidate makes PHYS-HYBRID the default forensic profile for C3+ conformance: PEB payloads plus SQL-visible skim tables.

## Normative stance

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL are to be interpreted as described by RFC 2119 and RFC 8174 when written in capitals.

## Public file identity

The canonical public extension is `.gmea`. GMEA v1 uses SQLite as the normative container profile, identified internally by `PRAGMA application_id = 0x474D4541` and `PRAGMA user_version >= 8` for this v0.8 candidate. The extension identifies the GMEA archive contract, not a generic SQLite database.

A conforming finalized `.gmea` archive MUST be a single file and MUST NOT require WAL, SHM, journal, catalog, signature, or sidecar files for interpretation or verification. Catalogs MAY exist as rebuildable discovery indexes across archives, but they are not part of a shard's forensic authority.

## Physical profiles

GMEA defines three physical profiles:

| Profile | Purpose | Canonical event storage | SQL event visibility |
| --- | --- | --- | --- |
| `GMEA-PHYS-REL-v1` | C0/C1 bridge, small archives, debugging, smoke tests | relational event rows | direct SQL |
| `GMEA-PHYS-PEB-v1` | compact production payloads | packed binary event blocks | block-level SQL |
| `GMEA-PHYS-HYBRID-v1` | default forensic production profile | packed binary event blocks plus skims | block-level SQL plus profile skims |

When `GMEA-PHYS-HYBRID-v1` or `GMEA-PHYS-PEB-v1` is the declared physical profile, relational `event_core` or profile-payload rows MUST be absent or explicitly marked as non-authoritative derived views. `GMEA-PHYS-REL-v1` is the only profile in which relational event rows are the canonical event storage.

## Packed Event Blocks

PEB uses a magic header (`GMEAPEB1`), a canonical JSON block header, a stream-count field, and length-prefixed typed streams. Header JSON MUST be serialized using the GMEA canonical JSON subset aligned with RFC-8785 principles: UTF-8, lexicographic object keys, no insignificant whitespace, no floats, and I-JSON-compatible values.

Writers SHOULD target uncompressed PEB block sizes from 256 KiB to 4 MiB. Readers claiming C2+ PEB support MUST support at least 16 MiB uncompressed blocks. All PEB numeric length fields are unsigned little-endian integers.

PEB headers SHOULD include an `arrow_schema` field for derived Arrow and Parquet export planning. Arrow IPC is not the canonical v1 physical profile; it is a derived export target.

## Identifiers

C2+ archives MUST use UUIDv7-compatible 16-byte BLOB identifiers for GMEA-managed `block_id` and `event_id` values. The canonical text form MAY be exposed by readers, but the archive representation is binary.

## Normative schema asset

The v0.8 normative DDL for PHYS-HYBRID conformance testing is:

`GMEA_schema_v1_candidate_v0_8.sql`

That schema defines the minimum tables required for v0.8 PEB validation, including `event_block`, `event_skim_l1_quote`, `event_block_merkle_root`, `time_rebase_profile`, `time_rebase_offset_segment`, `source_artifact`, `coverage_segment`, `archive_audit_event`, `finalization_manifest`, and `archive_signature`.

## Hashing and Merkle roots

Each PEB block has three hashes:

- `encoded_payload_hash`: SHA-256 of the stored compressed or uncompressed payload bytes.
- `canonical_event_stream_hash`: SHA-256 of the decoded canonical event stream projection.
- `block_leaf_hash`: SHA-256 over block identity plus the two prior hashes.

C3+ PHYS-HYBRID archives SHOULD store a Merkle root over ordered block leaf hashes. The v0.8 odd-node policy is `promote_last_unchanged` and is tested in the conformance corpus.

## Queryability

PHYS-HYBRID archives provide SQL-visible block indexes and profile-specific skim tables. These support coarse filtering without decoding every event. Full event-level access is provided by the reference decoder. For C5 implementations, a SQLite virtual-table extension exposing decoded events is RECOMMENDED but not REQUIRED.

## Time and reversibility

GMEA stores canonical UTC time and original source time evidence. Time-rebase offset metadata belongs inside archive metadata and event/profile metadata, not in the filename. Filenames are reconstructable convenience labels. A conforming archive MUST preserve enough source-time evidence to recover the original source timestamp representation or the declared canonical source timestamp representation for each normalized event.

## Conformance classes

- C0: CSV Bridge.
- C1: Core Archive.
- C2: Append-only Archive; PEB and UUIDv7 IDs required when using packed profiles.
- C3: Forensic Archive; PHYS-HYBRID required by default, Merkle root expected, source evidence strengthened.
- C4: Signed Archive.
- C5: Certified implementation; reference validator, negative corpus, safe-reader posture, and virtual table extension recommended.

## v0.8 conformance assets

The v0.8 package includes:

- `GMEA_schema_v1_candidate_v0_8.sql`
- `GMEA_reference_validator_v0_5.py`
- positive PEB archives for uncompressed and DEFLATE payloads
- negative PEB archives for corrupted payload, skim mismatch, missing skim, non-canonical header, unsupported compression, malformed stream length, wrong stream count, invalid event UUIDv7, invalid block UUIDv7, and Merkle mismatch
- validator outputs for each positive and negative archive
- decode-block output for the uncompressed positive archive
- schema-verify output for the uncompressed positive archive
- `GMEA_conformance_suite_manifest_v0_8.json`

## Release posture

GMEA v0.8 is suitable for public release as a pre-1.0 conformance-testable candidate. External implementers can run the validator, inspect the schema, decode a positive PEB archive, and verify that malformed archives fail closed with expected errors.

## Remaining before v1.0

GMEA v0.8 is conformance-testable but still pre-1.0. Remaining work includes broader market-event profile coverage beyond the L1 quote smoke profile, benchmark corpus publication, signature verification implementation beyond schema hooks, a C5 virtual-table prototype, public repository governance, and independent implementation feedback.
