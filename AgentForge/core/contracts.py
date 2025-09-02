#!/usr/bin/env python3
"""
📋 CONTRACT UTILITIES
Contract merging and validation utilities
"""

from typing import Dict, Any


def is_contract_empty(c: dict) -> bool:
    """Check if a contract is empty (missing files or endpoints)"""
    c = c or {}
    has_files = isinstance(c.get('files'), list) and len(c['files']) > 0
    has_eps = isinstance(c.get('endpoints'), list) and len(c['endpoints']) > 0
    return not (has_files and has_eps)


def merge_contract(base: Dict[str, Any], add: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two contracts, combining files, endpoints, and tables"""
    base = base or {}
    add = add or {}
    out = {**base}
    
    # Merge files
    bf, af = base.get('files') or [], add.get('files') or []
    out['files'] = sorted(set(bf + af))
    
    # Merge endpoints (avoid duplicates by method+path)
    be = base.get('endpoints') or []
    ae = add.get('endpoints') or []
    seen = {(e.get('method','GET').upper(), e.get('path','')) for e in be}
    
    for e in ae:
        key = (e.get('method','GET').upper(), e.get('path',''))
        if key not in seen:
            be.append({'method': key[0], 'path': key[1]})
            seen.add(key)
    out['endpoints'] = be
    
    # Merge tables (avoid duplicates by name)
    bt = base.get('tables') or []
    at = add.get('tables') or []
    seen_t = {t.get('name','') for t in bt}
    
    for t in at:
        n = t.get('name','')
        if n and n not in seen_t:
            bt.append({'name': n})
            seen_t.add(n)
    out['tables'] = bt
    
    # Update source tracking
    src = base.get('source') or 'llm'
    out['source'] = f"{src}+merge"
    
    return out
