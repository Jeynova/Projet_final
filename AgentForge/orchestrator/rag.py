from pathlib import Path

def retrieve_snippets(tags, root: Path) -> str:
    # ultra simple : charge 3–5 md qui contiennent les tags
    acc = []
    for p in (root / "rag_snippets").glob("*.md"):
        txt = p.read_text(encoding="utf-8").lower()
        if any(t in txt for t in tags):
            acc.append(f"\n--- SNIPPET: {p.name} ---\n{txt}\n")
        if len(acc) >= 5:
            break
    return "\n".join(acc)