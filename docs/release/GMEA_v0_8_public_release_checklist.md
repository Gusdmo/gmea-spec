# GMEA v0.8 Public Release Checklist

Release title:

> GMEA v0.8 — Public Conformance-Testable Candidate

## Required assets

- [x] Whitepaper draft v0.8
- [x] PEB specification v0.8
- [x] Semantic hash specification v0.8
- [x] Normative schema SQL v0.8
- [x] Reference validator v0.5
- [x] Conformance test plan
- [x] Release notes
- [x] Conformance manifest
- [x] Validation summary
- [x] Positive uncompressed PEB archive
- [x] Positive DEFLATE PEB archive
- [x] Negative corpus archives
- [x] Expected negative results
- [x] Validator output JSON files
- [x] README with exact commands

## Recommended repository layout

```text
gmea-spec/
  README.md
  docs/
  schema/
  tools/
  conformance/
    positive/
    negative/
    expected/
    outputs/
  releases/v0.8/
```

The current release bundle keeps files in one directory for command reproducibility. A public repository may reorganize files after updating command examples accordingly.

## Pre-1.0 label

- [x] Marked as pre-1.0.
- [x] Does not claim v1.0 compatibility freeze.
- [x] Invites external implementation feedback.

## Suggested licenses

- Specification: CC BY 4.0.
- Reference validator/source code: Apache-2.0.

