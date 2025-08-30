"""Lightweight RAG (Retrieval Augmented Generation) store.

Pure-Python, dependency-free bag-of-words TF-IDF style similarity.
Optimized for small corpus (tens / low hundreds of docs) – good enough for
agent contextual grounding.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import math, re, json, time
from pathlib import Path

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")

@dataclass
class Document:
    doc_id: str
    text: str
    metadata: Dict[str, Any]
    added: float

class RAGStore:
    def __init__(self, persist_path: Optional[Path] = None):
        self.persist_path = persist_path or Path(__file__).parent / "rag_store.json"
        self.docs: Dict[str, Document] = {}
        self.df: Dict[str, int] = {}
        self._dirty = False
        self._load()

    # ---------------- Persistence ----------------
    def _load(self):
        if self.persist_path.exists():
            try:
                data = json.loads(self.persist_path.read_text())
                for d in data.get("docs", []):
                    doc = Document(d['doc_id'], d['text'], d.get('metadata', {}), d.get('added', time.time()))
                    self.docs[doc.doc_id] = doc
                self._rebuild_df()
            except Exception:
                pass

    def _save(self):
        if not self._dirty:
            return
        try:
            payload = {"docs": [doc.__dict__ for doc in self.docs.values()]}
            self.persist_path.write_text(json.dumps(payload, indent=2))
            self._dirty = False
        except Exception:
            pass

    # ---------------- Indexing -------------------
    def _tokenize(self, text: str) -> List[str]:
        return [t.lower() for t in TOKEN_RE.findall(text)][:500]  # cap per doc

    def _rebuild_df(self):
        self.df.clear()
        for doc in self.docs.values():
            seen = set()
            for tok in self._tokenize(doc.text):
                if tok in seen:
                    continue
                self.df[tok] = self.df.get(tok, 0) + 1
                seen.add(tok)

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        if not text.strip():
            return
        # Short circuit duplicates with same id
        self.docs[doc_id] = Document(doc_id, text[:8000], metadata or {}, time.time())
        self._dirty = True
        self._rebuild_df()
        self._save()

    # ---------------- Retrieval ------------------
    def similarity(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.docs:
            return []
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []
        # Query term frequencies
        q_tf: Dict[str, int] = {}
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0) + 1
        N = len(self.docs) or 1
        # Query vector (tf-idf)
        q_vec: Dict[str, float] = {}
        for t, c in q_tf.items():
            df = self.df.get(t, 0) or 1
            idf = math.log(N / df)
            q_vec[t] = (c / len(q_tokens)) * idf
        # Score docs
        scores = []
        for doc in self.docs.values():
            d_tokens = self._tokenize(doc.text)
            if not d_tokens:
                continue
            d_tf: Dict[str, int] = {}
            for t in d_tokens:
                d_tf[t] = d_tf.get(t, 0) + 1
            doc_vec: Dict[str, float] = {}
            for t, c in d_tf.items():
                if t not in q_vec:
                    continue
                df = self.df.get(t, 0) or 1
                idf = math.log(N / df)
                doc_vec[t] = (c / len(d_tokens)) * idf
            # Cosine similarity
            dot = sum(q_vec[t] * doc_vec.get(t, 0.0) for t in q_vec)
            q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
            d_norm = math.sqrt(sum(v * v for v in doc_vec.values())) or 1.0
            score = dot / (q_norm * d_norm)
            scores.append((score, doc))
        scores.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, doc in scores[:top_k]:
            snippet = doc.text[:400].replace('\n', ' ')
            out.append({
                'doc_id': doc.doc_id,
                'score': round(score, 4),
                'snippet': snippet,
                'metadata': doc.metadata
            })
        return out

    def contextualize(self, query: str, top_k: int = 3) -> str:
        retrieved = self.similarity(query, top_k=top_k)
        if not retrieved:
            return ''
        parts = []
        for r in retrieved:
            parts.append(f"[DOC {r['doc_id']} S={r['score']}] {r['snippet']}")
        return '\n'.join(parts)

__all__ = ["RAGStore", "Document"]
