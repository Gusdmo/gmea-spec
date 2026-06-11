-- GMEA Schema v1.0-candidate v0.8
-- Normative DDL for PHYS-HYBRID conformance testing.
-- This file defines the minimum tables required for v0.8 PEB validation.
-- PHYS-HYBRID is the default C3+ profile.
-- Relational event_core/profile payload tables are intentionally absent when PHYS-HYBRID is declared.
-- If PHYS-REL tables are present in a PHYS-HYBRID archive, they MUST be marked non-authoritative derived views.
-- See GMEA_packed_event_blocks_spec_v1_0_candidate_v0_8.md for the canonical PEB wire format.
-- C2+ requirement: block_id and event_id streams MUST use UUIDv7-compatible 16-byte BLOB values.
-- source_id/instrument_id are internal INTEGER surrogates; canonical identity strings are stored in metadata tables.
-- Finalized archives MUST be created with no required WAL/SHM/journal/catalog sidecars.
-- Recommended finalization sequence: checkpoint WAL if used; PRAGMA journal_mode=DELETE; VACUUM INTO 'final.gmea'; compute semantic/file hashes; sign semantic hash.
PRAGMA application_id = 0x474D4541;
PRAGMA user_version = 8;
PRAGMA page_size = 8192;

CREATE TABLE archive_header (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE source_identity (
  source_id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL,
  venue_or_server TEXT NOT NULL,
  canonical_source_key TEXT NOT NULL UNIQUE
);

CREATE TABLE instrument_identity (
  instrument_id INTEGER PRIMARY KEY,
  source_symbol TEXT NOT NULL,
  asset_class TEXT NOT NULL,
  canonical_instrument_key TEXT NOT NULL UNIQUE
);

CREATE TABLE time_rebase_profile (
  time_rebase_profile_id INTEGER PRIMARY KEY,
  profile_hash BLOB NOT NULL CHECK(length(profile_hash)=32),
  source_time_basis TEXT NOT NULL,
  canonical_time_basis TEXT NOT NULL CHECK(canonical_time_basis='UTC'),
  offset_mode TEXT NOT NULL CHECK(offset_mode IN ('constant','variable','none')),
  reversibility_required INTEGER NOT NULL CHECK(reversibility_required IN (0,1)),
  UNIQUE(profile_hash)
);

CREATE TABLE time_rebase_offset_segment (
  offset_segment_id INTEGER PRIMARY KEY,
  time_rebase_profile_id INTEGER NOT NULL REFERENCES time_rebase_profile(time_rebase_profile_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  segment_start_utc_ns INTEGER NOT NULL,
  segment_end_utc_ns INTEGER NOT NULL,
  offset_minutes INTEGER NOT NULL,
  CHECK(segment_end_utc_ns > segment_start_utc_ns)
);
CREATE INDEX idx_rebase_segment_profile_time ON time_rebase_offset_segment(time_rebase_profile_id, segment_start_utc_ns, segment_end_utc_ns);

CREATE TABLE source_artifact (
  source_artifact_id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES source_identity(source_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  artifact_hash BLOB NOT NULL CHECK(length(artifact_hash)=32),
  artifact_name_redacted TEXT,
  row_count INTEGER CHECK(row_count IS NULL OR row_count >= 0),
  validator_version TEXT NOT NULL,
  UNIQUE(artifact_hash)
);

CREATE TABLE event_batch (
  batch_id INTEGER PRIMARY KEY,
  batch_sequence INTEGER NOT NULL UNIQUE,
  source_id INTEGER NOT NULL REFERENCES source_identity(source_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  instrument_id INTEGER NOT NULL REFERENCES instrument_identity(instrument_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  source_artifact_id INTEGER REFERENCES source_artifact(source_artifact_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  time_rebase_profile_id INTEGER REFERENCES time_rebase_profile(time_rebase_profile_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  batch_hash BLOB NOT NULL CHECK(length(batch_hash)=32)
);

CREATE TABLE event_block (
  block_id BLOB PRIMARY KEY CHECK(length(block_id)=16),
  batch_id INTEGER NOT NULL REFERENCES event_batch(batch_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  block_sequence INTEGER NOT NULL,
  physical_profile TEXT NOT NULL CHECK(physical_profile IN ('GMEA-PHYS-PEB-v1','GMEA-PHYS-HYBRID-v1')),
  profile_id TEXT NOT NULL,
  instrument_id INTEGER NOT NULL REFERENCES instrument_identity(instrument_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  source_id INTEGER NOT NULL REFERENCES source_identity(source_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  block_start_utc_ns INTEGER NOT NULL,
  block_end_utc_ns INTEGER NOT NULL,
  event_count INTEGER NOT NULL CHECK(event_count > 0),
  encoding_profile TEXT NOT NULL CHECK(encoding_profile='GMEA-PEB-v1'),
  compression TEXT NOT NULL CHECK(compression IN ('none','deflate','zstd')),
  uncompressed_size INTEGER NOT NULL CHECK(uncompressed_size > 0),
  compressed_size INTEGER NOT NULL CHECK(compressed_size > 0),
  encoded_payload_hash BLOB NOT NULL CHECK(length(encoded_payload_hash)=32),
  canonical_event_stream_hash BLOB NOT NULL CHECK(length(canonical_event_stream_hash)=32),
  block_leaf_hash BLOB NOT NULL CHECK(length(block_leaf_hash)=32),
  payload_blob BLOB NOT NULL,
  header_json BLOB NOT NULL,
  arrow_schema_json BLOB,
  UNIQUE(batch_id, block_sequence)
);
CREATE INDEX idx_event_block_time ON event_block(instrument_id, profile_id, block_start_utc_ns, block_end_utc_ns);
CREATE INDEX idx_event_block_batch ON event_block(batch_id, block_sequence);
CREATE INDEX idx_event_block_sequence ON event_block(batch_id, block_sequence);

CREATE TABLE event_skim_l1_quote (
  block_id BLOB PRIMARY KEY REFERENCES event_block(block_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  event_count INTEGER NOT NULL CHECK(event_count > 0),
  price_scale INTEGER NOT NULL CHECK(price_scale BETWEEN -18 AND 18),
  first_bid_mantissa INTEGER NOT NULL,
  last_bid_mantissa INTEGER NOT NULL,
  min_bid_mantissa INTEGER NOT NULL,
  max_bid_mantissa INTEGER NOT NULL,
  first_ask_mantissa INTEGER NOT NULL,
  last_ask_mantissa INTEGER NOT NULL,
  min_ask_mantissa INTEGER NOT NULL,
  max_ask_mantissa INTEGER NOT NULL,
  flags_or INTEGER NOT NULL
);
CREATE INDEX idx_skim_block ON event_skim_l1_quote(block_id);
CREATE INDEX idx_skim_l1_quote_bid_range ON event_skim_l1_quote(min_bid_mantissa, max_bid_mantissa);

CREATE TABLE coverage_segment (
  coverage_segment_id INTEGER PRIMARY KEY,
  instrument_id INTEGER NOT NULL REFERENCES instrument_identity(instrument_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  source_id INTEGER NOT NULL REFERENCES source_identity(source_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  segment_start_utc_ns INTEGER NOT NULL,
  segment_end_utc_ns INTEGER NOT NULL,
  event_count INTEGER NOT NULL CHECK(event_count >= 0),
  coverage_hash BLOB NOT NULL CHECK(length(coverage_hash)=32),
  CHECK(segment_end_utc_ns > segment_start_utc_ns)
);
CREATE INDEX idx_coverage_segment_time ON coverage_segment(instrument_id, source_id, segment_start_utc_ns, segment_end_utc_ns);

CREATE TABLE archive_audit_event (
  audit_event_id INTEGER PRIMARY KEY,
  audit_sequence INTEGER NOT NULL UNIQUE,
  event_type TEXT NOT NULL,
  event_time_utc_ns INTEGER NOT NULL,
  event_hash BLOB NOT NULL CHECK(length(event_hash)=32),
  previous_event_hash BLOB CHECK(previous_event_hash IS NULL OR length(previous_event_hash)=32)
);

CREATE TABLE event_block_merkle_root (
  scope TEXT PRIMARY KEY,
  leaf_count INTEGER NOT NULL CHECK(leaf_count >= 0),
  odd_node_policy TEXT NOT NULL CHECK(odd_node_policy='promote_last_unchanged'),
  merkle_root BLOB NOT NULL CHECK(length(merkle_root)=32)
) WITHOUT ROWID;
CREATE INDEX idx_event_block_merkle ON event_block_merkle_root(scope);

CREATE TABLE finalization_manifest (
  finalization_status TEXT NOT NULL CHECK(finalization_status IN ('open','finalized')),
  semantic_hash_algorithm TEXT NOT NULL,
  semantic_hash BLOB NOT NULL CHECK(length(semantic_hash)=32)
);

CREATE TABLE archive_signature (
  signature_id INTEGER PRIMARY KEY,
  signature_scope TEXT NOT NULL,
  signature_algorithm TEXT NOT NULL,
  signed_semantic_hash BLOB NOT NULL CHECK(length(signed_semantic_hash)=32),
  signing_key_id TEXT,
  signature_bytes BLOB
);

-- Finalized archives MUST NOT require WAL, SHM, journal, catalog, or sidecar files.
-- Writers MAY use WAL during construction but MUST checkpoint and finalize single-file archives.
