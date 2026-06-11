# GMEA Semantic Hash Specification

## v1.0-candidate v0.8

Status: pre-1.0 conformance-testable candidate.

## 1. Scope

This document defines the semantic-hash model used by GMEA v0.8 for the SQLite container profile and GMEA-PEB-v1 L1 quote PHYS-HYBRID conformance suite.

## 2. Canonical JSON projection

GMEA semantic hash inputs use typed canonical JSON cells. JSON MUST use the GMEA canonical JSON subset aligned with RFC-8785 principles: UTF-8, lexicographic object keys, no insignificant whitespace, no floats, deterministic arrays, and explicit typed values.

Example typed cells:

```json
{"t":"int","v":"1767225600000000000"}
{"t":"uuidv7","v":"018f8b6b1c0170018000000000000002"}
{"t":"text","v":"l1_quote"}
```

## 3. PEB hash hierarchy

PEB uses three hashes:

1. `encoded_payload_hash = SHA-256(payload_blob)`.
2. `canonical_event_stream_hash = SHA-256("GMEA-PEB-EVENTSTREAM-v1\n" || canonical_event_json_line*)`.
3. `block_leaf_hash = SHA-256("GMEA-PEB-BLOCK-LEAF-v1\0" || block_id || encoded_payload_hash || canonical_event_stream_hash)`.

This separates transport/storage bytes from decoded event semantics. DEFLATE and uncompressed archives can have different encoded hashes while preserving equivalent canonical event streams.

## 4. Excluded tables

Signature and manifest tables that record or sign semantic hashes are excluded from the content semantic hash to avoid circular hashing. Implementations MUST NOT include `semantic_hash_manifest`, `finalization_manifest`, or `archive_signature` in the content semantic hash payload unless a future algorithm version explicitly changes this rule.

## 5. Merkle root

The C3+ Merkle tree is computed over ordered `block_leaf_hash` values. Ordered means `ORDER BY batch_id, block_sequence, block_id` under the normative v0.8 schema. Odd nodes are promoted unchanged. The v0.8 negative corpus includes a Merkle mismatch vector.

## 6. PHYS-HYBRID authority

For PHYS-HYBRID, PEB decoded event streams are authoritative. Skim tables are verified against decoded event streams, but skim rows do not replace the canonical event stream. If relational `event_core` tables are present, they MUST be absent or explicitly non-authoritative derived views.

## 7. v0.8 conformance corpus

The v0.8 corpus includes two positive archives and ten negative archives. Validators must pass the positive archives and fail closed on the negative archives with precise error categories.
