from orchestrator_v2.rag_store import RAGStore

def test_rag_add_and_retrieve(tmp_path):
    store = RAGStore(tmp_path / 'rag.json')
    store.add_document('doc1', 'FastAPI project with auth and posts', {'type': 'code'})
    res = store.similarity('auth posts', top_k=1)
    assert res and res[0]['doc_id'] == 'doc1'
