# GMEA Packed Event Blocks Specification

## v1.0-candidate v0.8

Status: pre-1.0 conformance-testable candidate. This document defines the GMEA-PEB-v1 physical wire format used by the v0.8 PHYS-HYBRID conformance suite.

## 1. Scope

Packed Event Blocks (PEB) encode high-volume market events as compact columnar binary streams inside SQLite BLOBs. PEB is used by `GMEA-PHYS-PEB-v1` and `GMEA-PHYS-HYBRID-v1`. Relational metadata, block indexes, skim tables, time-rebase profiles, source-artifact metadata, Merkle roots, and signatures remain in ordinary SQLite tables.

## 2. Required container tables

The normative v0.8 DDL is `GMEA_schema_v1_candidate_v0_8.sql`. It includes the PEB tables `event_block`, `event_skim_l1_quote`, and `event_block_merkle_root` plus the minimal forensic metadata required for C3+ testing.

## 3. Physical-profile authority rule

When the declared archive profile is `GMEA-PHYS-HYBRID-v1` or `GMEA-PHYS-PEB-v1`, the PEB payload is the canonical event storage. Relational `event_core` and profile-payload tables MUST be absent or explicitly marked `non_authoritative_derived` in `archive_header`. `GMEA-PHYS-REL-v1` is the only profile in which relational event rows are authoritative.

## 4. Block size guidance

Writers SHOULD produce uncompressed PEB blocks in the 256 KiB to 4 MiB range. Readers claiming C2+ PEB support MUST support at least 16 MiB uncompressed blocks. Writers MAY use smaller blocks for test vectors and very small shards.

## 5. PEB byte layout

All integer length fields in the PEB wrapper are unsigned little-endian integers. The canonical layout is:

```text
bytes[0:8]    magic = "GMEAPEB1"
uint32_le     header_len
bytes         header_json, exactly header_len bytes
uint16_le     stream_count
repeated stream_count times:
  uint8       stream_name_len
  bytes       stream_name ASCII, exactly stream_name_len bytes
  uint32_le   stream_len
  bytes       stream_payload, exactly stream_len bytes
```

No trailing bytes are permitted. Unknown mandatory streams MUST fail closed. Required streams for the v0.8 L1 quote smoke profile are exactly:

```text
event_id_uuidv7
canonical_utc_delta_ns
bid_delta
ask_delta
flags
source_row_number_delta
```

The v0.8 reference validator requires `stream_order` in the header to match this order for the L1 quote smoke profile.

## 6. Header JSON

`header_json` MUST be serialized using the GMEA canonical JSON subset aligned with RFC-8785 principles:

- UTF-8;
- lexicographic object key order;
- no insignificant whitespace;
- no floating-point values;
- I-JSON-compatible string and scalar values;
- deterministic array order.

The decoded JSON object MUST re-serialize byte-for-byte to the stored header. If it does not, validation fails with `PEB header JSON is not canonical`.

Required v0.8 L1 quote header fields include:

```json
{
  "arrow_schema": {"fields": []},
  "base_ask_mantissa": 108520,
  "base_bid_mantissa": 108500,
  "base_canonical_utc_ns": 1767225600000000000,
  "encoding_profile": "GMEA-PEB-v1",
  "event_count": 3,
  "price_scale": -5,
  "profile_id": "l1_quote",
  "stream_order": [
    "event_id_uuidv7",
    "canonical_utc_delta_ns",
    "bid_delta",
    "ask_delta",
    "flags",
    "source_row_number_delta"
  ]
}
```

## 7. Normative byte-layout example

The following abbreviated example shows the v0.8 L1 quote smoke block structure. Hex bytes are illustrative except for fixed magic and length encodings.

```text
47 4d 45 41 50 45 42 31                         # "GMEAPEB1"
<4-byte little-endian header_len>                 # e.g. f1 00 00 00
7b 22 61 72 72 6f 77 ... 7d                       # canonical header JSON
06 00                                             # stream_count = 6
0f "event_id_uuidv7" <len32> <16*N bytes>
16 "canonical_utc_delta_ns" <len32> <uvarint deltas>
09 "bid_delta" <len32> <zigzag-varint deltas>
09 "ask_delta" <len32> <zigzag-varint deltas>
05 "flags" <len32> <uint8 flags>
17 "source_row_number_delta" <len32> <uvarint deltas>
```

An independent implementation can verify the concrete bytes by running:

```bash
python GMEA_reference_validator_v0_5.py decode-block GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
```

## 8. Stream encodings

`event_id_uuidv7` stores the binary 16-byte UUIDv7-compatible form for every event. C2+ archives MUST use UUIDv7-compatible bytes for GMEA-managed event identifiers.

`canonical_utc_delta_ns` stores unsigned varint deltas from `base_canonical_utc_ns`.

`bid_delta` and `ask_delta` store ZigZag-varint deltas from `base_bid_mantissa` and `base_ask_mantissa`.

`flags` stores one unsigned byte per event in the v0.8 L1 quote smoke profile.

`source_row_number_delta` stores unsigned varint deltas from zero.

## 9. Compression

`compression = none` MUST be supported. `compression = deflate` SHOULD be supported. `compression = zstd` MAY be supported by future implementations, but unsupported compression MUST fail closed. The v0.8 negative corpus includes an unsupported-compression archive.

## 10. Hashes

Each PEB block stores:

- `encoded_payload_hash`: SHA-256 over the exact stored payload bytes.
- `canonical_event_stream_hash`: SHA-256 over the decoded canonical event-stream projection.
- `block_leaf_hash`: SHA-256 over block identity and the two prior hashes.

For compressed payloads, `encoded_payload_hash` differs from the uncompressed archive, but the canonical event stream is independent of compression when decoded events are identical.

## 11. Skim tables

`GMEA-PHYS-HYBRID-v1` requires profile skim tables. The v0.8 L1 quote profile uses `event_skim_l1_quote`. A PHYS-HYBRID block without the skim row fails validation.

## 12. Merkle root

`event_block_merkle_root` stores Merkle roots over ordered `block_leaf_hash` values. The v0.8 odd-node policy is `promote_last_unchanged`. Mismatched roots fail validation.

## 13. BLOB implementation guidance

PEB payloads are immutable after write. Writers SHOULD avoid in-place BLOB mutation and SHOULD use bounded streaming APIs for large blocks where available. Readers SHOULD decode blocks under configured memory limits and MUST support at least 16 MiB uncompressed blocks for C2+ PEB support.

## 14. Derived Arrow and Parquet export

`arrow_schema` in the PEB header is metadata for derived export planning. Arrow IPC is not the canonical GMEA v1 physical profile. Parquet exports SHOULD embed source GMEA block hashes and Merkle-root metadata in derived-file metadata when possible.
