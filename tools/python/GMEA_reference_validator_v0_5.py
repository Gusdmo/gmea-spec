#!/usr/bin/env python3
"""GMEA reference validator and decoder v0.5.

Scope: conformance-testable candidate v0.8 for the SQLite container profile and
GMEA-PEB-v1 L1 quote PHYS-HYBRID profile.

This remains a small, strict, standard-library-only reference implementation so
independent implementers can compare pass/fail behavior and decoded event JSON.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, struct, sys, zlib
from pathlib import Path
from typing import Any
APP_ID=0x474D4541
PEB_MAGIC=b"GMEAPEB1"
MAX_REQUIRED_UNCOMPRESSED_BLOCK=16*1024*1024
REQUIRED_STREAMS=["event_id_uuidv7","canonical_utc_delta_ns","bid_delta","ask_delta","flags","source_row_number_delta"]
REQUIRED_TABLES=[
    "archive_header","source_identity","instrument_identity","time_rebase_profile",
    "time_rebase_offset_segment","source_artifact","event_batch","event_block",
    "event_skim_l1_quote","coverage_segment","archive_audit_event",
    "event_block_merkle_root","finalization_manifest","archive_signature",
]
REQUIRED_INDEXES=["idx_event_block_time","idx_event_block_batch","idx_event_block_sequence","idx_skim_block"]

def _reject_float(obj:Any)->None:
    if isinstance(obj,float): raise ValueError("JSON float is not permitted in v0.8 canonical subset")
    if isinstance(obj,dict):
        for v in obj.values(): _reject_float(v)
    elif isinstance(obj,list):
        for v in obj: _reject_float(v)

def canonical_json(obj:Any)->bytes:
    _reject_float(obj)
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256(data:bytes)->bytes: return hashlib.sha256(data).digest()
def is_uuidv7_bytes(b:bytes)->bool:
    return isinstance(b,(bytes,bytearray)) and len(b)==16 and ((b[6]>>4)==0x7) and ((b[8]&0xC0)==0x80)

def uvarint_decode_stream(data:bytes,count:int)->list[int]:
    vals=[]; i=0
    for _ in range(count):
        shift=0; value=0
        while True:
            if i>=len(data): raise ValueError("truncated varint stream")
            b=data[i]; i+=1; value|=(b&0x7F)<<shift
            if not (b&0x80): break
            shift+=7
            if shift>63: raise ValueError("varint too large")
        vals.append(value)
    if i!=len(data): raise ValueError("varint stream has trailing bytes")
    return vals

def zigzag_decode(n:int)->int: return (n>>1)^-(n&1)

def parse_peb_payload(uncompressed_payload:bytes):
    if len(uncompressed_payload)<14 or uncompressed_payload[:8]!=PEB_MAGIC:
        raise ValueError("bad PEB magic")
    pos=8
    (header_len,)=struct.unpack_from("<I", uncompressed_payload, pos); pos+=4
    if header_len<=0 or pos+header_len>len(uncompressed_payload): raise ValueError("bad PEB header length")
    header_bytes=uncompressed_payload[pos:pos+header_len]; pos+=header_len
    header=json.loads(header_bytes.decode("utf-8"))
    if header_bytes != canonical_json(header): raise ValueError("PEB header JSON is not canonical")
    if pos+2>len(uncompressed_payload): raise ValueError("missing stream count")
    (stream_count,)=struct.unpack_from("<H", uncompressed_payload, pos); pos+=2
    streams={}
    for _ in range(stream_count):
        if pos>=len(uncompressed_payload): raise ValueError("truncated stream header")
        name_len=uncompressed_payload[pos]; pos+=1
        if name_len==0: raise ValueError("empty stream name")
        if pos+name_len+4>len(uncompressed_payload): raise ValueError("truncated stream name or length")
        name=uncompressed_payload[pos:pos+name_len].decode("ascii"); pos+=name_len
        if name in streams: raise ValueError("duplicate stream name")
        (stream_len,)=struct.unpack_from("<I", uncompressed_payload, pos); pos+=4
        if pos+stream_len>len(uncompressed_payload): raise ValueError("stream length exceeds payload")
        streams[name]=uncompressed_payload[pos:pos+stream_len]; pos+=stream_len
    if pos != len(uncompressed_payload): raise ValueError("PEB payload has trailing bytes")
    missing=[s for s in REQUIRED_STREAMS if s not in streams]
    if missing: raise ValueError("missing required stream: "+','.join(missing))
    if header.get("stream_order") != REQUIRED_STREAMS: raise ValueError("PEB stream_order is not canonical for l1_quote v0.8")
    if "arrow_schema" not in header: raise ValueError("PEB header missing arrow_schema")
    return header, header_bytes, streams

def decode_l1_quote_peb(uncompressed_payload:bytes):
    header,_hb,streams=parse_peb_payload(uncompressed_payload)
    if header.get("encoding_profile")!="GMEA-PEB-v1": raise ValueError("unsupported encoding profile")
    if header.get("profile_id")!="l1_quote": raise ValueError("only l1_quote v0.8 smoke profile supported")
    count=int(header["event_count"])
    price_scale=int(header["price_scale"])
    if not (-18 <= price_scale <= 18): raise ValueError("price_scale outside v0.8 L1 quote bounds")
    base_t=int(header["base_canonical_utc_ns"]); base_bid=int(header["base_bid_mantissa"]); base_ask=int(header["base_ask_mantissa"])
    ids=streams["event_id_uuidv7"]
    if len(ids)!=16*count: raise ValueError("event_id_uuidv7 stream length mismatch")
    event_ids=[ids[i*16:(i+1)*16] for i in range(count)]
    for eid in event_ids:
        if not is_uuidv7_bytes(eid): raise ValueError("event_id is not UUIDv7-compatible 16-byte value")
    dts=uvarint_decode_stream(streams["canonical_utc_delta_ns"],count)
    bid_d=[zigzag_decode(v) for v in uvarint_decode_stream(streams["bid_delta"],count)]
    ask_d=[zigzag_decode(v) for v in uvarint_decode_stream(streams["ask_delta"],count)]
    flags=list(streams["flags"])
    if len(flags)!=count: raise ValueError("flags stream length mismatch")
    row_d=uvarint_decode_stream(streams["source_row_number_delta"],count)
    out=[]; t=base_t; bid=base_bid; ask=base_ask; row=0
    for i in range(count):
        t+=dts[i]; bid+=bid_d[i]; ask+=ask_d[i]; row+=row_d[i]
        out.append({
            "event_id":{"t":"uuidv7","v":event_ids[i].hex()},
            "profile_id":{"t":"text","v":"l1_quote"},
            "canonical_utc_time_ns":{"t":"int","v":str(t)},
            "bid_mantissa":{"t":"int","v":str(bid)},
            "ask_mantissa":{"t":"int","v":str(ask)},
            "price_scale":{"t":"int","v":str(price_scale)},
            "flags":{"t":"int","v":str(flags[i])},
            "source_row_number":{"t":"int","v":str(row)},
        })
    return header,out

def canonical_event_stream_hash(events):
    h=hashlib.sha256(); h.update(b"GMEA-PEB-EVENTSTREAM-v1\n")
    for ev in events:
        h.update(canonical_json(ev)); h.update(b"\n")
    return h.digest()

def block_leaf_hash(block_id:bytes, encoded_hash:bytes, event_hash:bytes)->bytes:
    return sha256(b"GMEA-PEB-BLOCK-LEAF-v1\0" + block_id + encoded_hash + event_hash)

def merkle_root(leaves:list[bytes])->bytes:
    if not leaves: return b""
    level=list(leaves)
    while len(level)>1:
        nxt=[]
        for i in range(0,len(level),2):
            if i+1<len(level): nxt.append(sha256(b"GMEA-MERKLE-NODE-v1\0"+level[i]+level[i+1]))
            else: nxt.append(level[i])
        level=nxt
    return level[0]

def maybe_decompress(payload:bytes, compression:str, expected_uncompressed_size:int)->bytes:
    if compression=="none": uncompressed=payload
    elif compression=="deflate": uncompressed=zlib.decompress(payload)
    else: raise ValueError("unsupported compression: "+compression)
    if len(uncompressed)!=expected_uncompressed_size: raise ValueError("uncompressed size mismatch")
    if len(uncompressed)>MAX_REQUIRED_UNCOMPRESSED_BLOCK: raise ValueError("block exceeds required reader support limit")
    return uncompressed

def scalar(conn, sql, default=None):
    row=conn.execute(sql).fetchone(); return row[0] if row else default

def validate_container(conn):
    checks=[]
    app=conn.execute("PRAGMA application_id").fetchone()[0]
    if app!=APP_ID: raise ValueError(f"bad application_id: {app!r}")
    checks.append("application_id=GMEA")
    uv=conn.execute("PRAGMA user_version").fetchone()[0]
    if uv<8: raise ValueError("user_version below v0.8 candidate")
    checks.append("user_version>=8")
    return checks

def validate_schema(conn):
    checks=[]
    tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing=[t for t in REQUIRED_TABLES if t not in tables]
    if missing: raise ValueError("schema missing required tables: "+','.join(missing))
    checks.append("required tables present")
    indexes={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    missing_idx=[i for i in REQUIRED_INDEXES if i not in indexes]
    if missing_idx: raise ValueError("schema missing required indexes: "+','.join(missing_idx))
    checks.append("required indexes present")
    phys=scalar(conn,"SELECT value FROM archive_header WHERE key='physical_profile'")
    rel_auth=scalar(conn,"SELECT value FROM archive_header WHERE key='relational_event_tables_authority'")
    if phys in ("GMEA-PHYS-HYBRID-v1","GMEA-PHYS-PEB-v1") and "event_core" in tables and rel_auth!="non_authoritative_derived":
        raise ValueError("event_core table present as authoritative under PEB physical profile")
    checks.append("relational/PEB authority rule satisfied")
    return checks

def validate_skim(conn, block_id, events):
    row=conn.execute("SELECT event_count,price_scale,first_bid_mantissa,last_bid_mantissa,min_bid_mantissa,max_bid_mantissa,first_ask_mantissa,last_ask_mantissa,min_ask_mantissa,max_ask_mantissa,flags_or FROM event_skim_l1_quote WHERE block_id=?",(block_id,)).fetchone()
    if row is None: raise ValueError("PHYS-HYBRID block missing event_skim_l1_quote row")
    bids=[int(e["bid_mantissa"]["v"]) for e in events]; asks=[int(e["ask_mantissa"]["v"]) for e in events]; flags=[int(e["flags"]["v"]) for e in events]; price_scale=int(events[0]["price_scale"]["v"])
    fo=0
    for f in flags: fo|=f
    expected=(len(events),price_scale,bids[0],bids[-1],min(bids),max(bids),asks[0],asks[-1],min(asks),max(asks),fo)
    if tuple(row)!=expected: raise ValueError("event_skim_l1_quote mismatch")

def validate_peb(conn):
    rows=conn.execute("SELECT block_id,batch_id,block_sequence,physical_profile,event_count,compression,uncompressed_size,compressed_size,encoded_payload_hash,canonical_event_stream_hash,block_leaf_hash,payload_blob,header_json,arrow_schema_json FROM event_block ORDER BY batch_id,block_sequence,block_id").fetchall()
    if not rows: raise ValueError("no event_block rows")
    reports=[]; leaves=[]
    for block_id,batch_id,block_sequence,physical_profile,event_count,compression,uncompressed_size,compressed_size,encoded_hash,event_hash,leaf_hash,payload,header_json,arrow_schema_json in rows:
        if not is_uuidv7_bytes(block_id): raise ValueError("block_id is not UUIDv7-compatible 16-byte value")
        if physical_profile=="GMEA-PHYS-HYBRID-v1" and block_sequence is None: raise ValueError("missing block_sequence")
        if sha256(payload)!=encoded_hash: raise ValueError("encoded payload hash mismatch")
        if len(payload)!=compressed_size: raise ValueError("compressed size mismatch")
        uncomp=maybe_decompress(payload, compression, int(uncompressed_size))
        header,actual_header_bytes,streams=parse_peb_payload(uncomp)
        if header_json != actual_header_bytes: raise ValueError("event_block.header_json does not match PEB payload header")
        if arrow_schema_json is not None and arrow_schema_json != canonical_json(header.get("arrow_schema")):
            raise ValueError("event_block.arrow_schema_json does not match header arrow_schema")
        decoded_header,events=decode_l1_quote_peb(uncomp)
        if len(events)!=event_count: raise ValueError("decoded event count mismatch")
        eh=canonical_event_stream_hash(events)
        if eh!=event_hash: raise ValueError("canonical event stream hash mismatch")
        lf=block_leaf_hash(block_id, encoded_hash, event_hash)
        if lf!=leaf_hash: raise ValueError("block leaf hash mismatch")
        if physical_profile=="GMEA-PHYS-HYBRID-v1": validate_skim(conn, block_id, events)
        leaves.append(lf)
        reports.append({"block_id_hex":block_id.hex(),"event_count":len(events),"compression":compression,"physical_profile":physical_profile})
    mr=merkle_root(leaves)
    row=conn.execute("SELECT leaf_count,odd_node_policy,merkle_root FROM event_block_merkle_root WHERE scope='archive'").fetchone()
    if row is None: raise ValueError("missing archive Merkle root")
    leaf_count,odd_policy,root=row
    if leaf_count!=len(leaves): raise ValueError("Merkle leaf_count mismatch")
    if odd_policy!="promote_last_unchanged": raise ValueError("unsupported Merkle odd-node policy")
    if root!=mr: raise ValueError("Merkle root mismatch")
    return {"block_count":len(reports),"blocks":reports,"merkle_root_hex":mr.hex()}

def validate(path:Path, schema_verify:bool=True):
    conn=sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        checks=validate_container(conn)
        if schema_verify:
            checks.extend(validate_schema(conn))
        peb=validate_peb(conn)
        checks.append("PEB blocks validate")
        checks.append("Merkle root validates")
        return {"passed":True,"checks":checks,"peb":peb}
    finally: conn.close()

def decode_block(path:Path, block_id_hex:str|None=None):
    conn=sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        if block_id_hex:
            row=conn.execute("SELECT block_id,compression,uncompressed_size,payload_blob FROM event_block WHERE block_id=?",(bytes.fromhex(block_id_hex),)).fetchone()
        else:
            row=conn.execute("SELECT block_id,compression,uncompressed_size,payload_blob FROM event_block ORDER BY batch_id,block_sequence,block_id LIMIT 1").fetchone()
        if row is None: raise ValueError("block not found")
        block_id,compression,usize,payload=row
        uncomp=maybe_decompress(payload, compression, int(usize))
        header,events=decode_l1_quote_peb(uncomp)
        return {"block_id_hex":block_id.hex(),"compression":compression,"header":header,"events":events}
    finally: conn.close()

def write_or_print(report, outp:Path|None):
    txt=json.dumps(report, indent=2, sort_keys=True)
    if outp: outp.write_text(txt, encoding="utf-8")
    print(txt)

def main(argv):
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd")
    val=sub.add_parser("validate"); val.add_argument("archive", type=Path); val.add_argument("--json-output", type=Path); val.add_argument("--no-schema-verify", action="store_true")
    sch=sub.add_parser("schema-verify"); sch.add_argument("archive", type=Path); sch.add_argument("--json-output", type=Path)
    dec=sub.add_parser("decode-block"); dec.add_argument("archive", type=Path); dec.add_argument("--block-id-hex"); dec.add_argument("--json-output", type=Path)
    ap.add_argument("legacy_archive", nargs="?", type=Path); ap.add_argument("--json-output", dest="legacy_json_output", type=Path)
    args=ap.parse_args(argv)
    outp=None
    try:
        if args.cmd=="decode-block": report=decode_block(args.archive,args.block_id_hex); passed=True; outp=args.json_output
        elif args.cmd=="schema-verify":
            conn=sqlite3.connect(f"file:{args.archive}?mode=ro", uri=True)
            try: report={"passed":True,"checks":validate_container(conn)+validate_schema(conn)}; passed=True
            finally: conn.close()
            outp=args.json_output
        elif args.cmd=="validate": report=validate(args.archive, not args.no_schema_verify); passed=bool(report.get("passed")); outp=args.json_output
        elif args.legacy_archive: report=validate(args.legacy_archive); passed=bool(report.get("passed")); outp=args.legacy_json_output
        else: ap.error("archive path or subcommand required")
    except Exception as e:
        report={"passed":False,"error":str(e)}; passed=False
        outp=getattr(args,"json_output",None) or getattr(args,"legacy_json_output",None)
    write_or_print(report,outp)
    return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main(sys.argv[1:]))
