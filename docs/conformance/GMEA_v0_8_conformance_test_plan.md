# GMEA v0.8 Conformance Test Plan

## Scope

This plan covers the v0.8 pre-1.0 conformance-testable candidate for the SQLite container profile and the L1 quote PHYS-HYBRID PEB profile.

## Required commands

```bash
python GMEA_reference_validator_v0_5.py validate GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
python GMEA_reference_validator_v0_5.py schema-verify GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
python GMEA_reference_validator_v0_5.py decode-block GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
python GMEA_reference_validator_v0_5.py validate GMEA_conformance_positive_peb_deflate_v0_8.gmea
```

Each `GMEA_negative_v0_8_*.gmea` archive MUST fail closed with the expected error recorded in `GMEA_negative_corpus_v0_8_expected.json`.

## Positive coverage

- SQLite `application_id` and `user_version` are verified.
- Required v0.8 tables and indexes are present.
- PHYS-HYBRID authority rule is enforced.
- PEB blocks decode successfully.
- Skim rows match decoded event streams.
- Merkle root validates.
- DEFLATE and uncompressed payloads validate.

## Negative coverage

- encoded payload hash mismatch;
- skim mismatch;
- missing skim row;
- non-canonical PEB header;
- unsupported compression;
- malformed stream length;
- wrong stream count / trailing bytes;
- invalid event UUIDv7;
- invalid block UUIDv7;
- Merkle root mismatch.

## Public release readiness

The v0.8 package is suitable for public external implementation feedback. It is not GMEA 1.0.
