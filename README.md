# GMEA Specification

**GMEA — Generalized Market Event Archive**

This repository is the public home for the GMEA specification and conformance suite.

## Current status

The target initial public release is:

```text
GMEA v0.8 — Public Conformance-Testable Candidate
```

GMEA is a proposed open archive format for immutable raw market events. GMEA v0.8 uses SQLite as the v1 container profile, Packed Event Blocks (PEB), PHYS-HYBRID conformance, semantic hashing, Merkle verification, and positive/negative `.gmea` conformance archives.

## Important

This repository has been created and seeded. The full v0.8 release bundle still needs to be committed/pushed from the local release package so that binary `.gmea` conformance archives and the zipped release bundle are preserved exactly.

Expected local release bundle:

```text
GMEA_v0_8_public_release_ready_bundle.zip
```

## Planned repository layout

```text
README.md
LICENSE
NOTICE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
GOVERNANCE.md
CHANGELOG.md
VERSION

docs/
  whitepaper/
  specs/
  conformance/
  release/

schema/
  GMEA_schema_v1_candidate_v0_8.sql

tools/
  python/
    GMEA_reference_validator_v0_5.py

testdata/
  positive/
  negative/
  expected/

manifest/
  GMEA_conformance_suite_manifest_v0_8.json

dist/
  GMEA_v0_8_public_release_ready_bundle.zip
```

## Validation commands

After the full bundle is committed, the following commands should pass:

```bash
python tools/python/GMEA_reference_validator_v0_5.py validate testdata/positive/GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
python tools/python/GMEA_reference_validator_v0_5.py validate testdata/positive/GMEA_conformance_positive_peb_deflate_v0_8.gmea
python tools/python/GMEA_reference_validator_v0_5.py schema-verify testdata/positive/GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
python tools/python/GMEA_reference_validator_v0_5.py decode-block testdata/positive/GMEA_conformance_positive_peb_uncompressed_v0_8.gmea
```

## Licensing plan

- Specifications and documentation: CC BY 4.0
- Reference code and workflows: Apache-2.0
- Test corpus: CC BY 4.0 for conformance/interoperability use
