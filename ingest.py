import argparse
import html
import json
import re
from pathlib import Path
from typing import Dict, List


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&quot;|&#39;", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks: List[str] = []
    if not words:
        return chunks

    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def path_to_professor(path: Path) -> str:
    stem = path.stem
    professor = stem.replace("_", " ").replace("-", " ")
    professor = re.sub(r"\s+", " ", professor).strip()
    if professor.lower().endswith("reviews"):
        professor = professor[: -len(" reviews")].strip()
    return professor.title()


def load_documents(input_dir: Path) -> List[Dict]:
    docs = []
    for path in sorted(input_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            text = load_text_file(path)
            docs.append({
                "path": path,
                "raw_text": text,
                "source": path.name,
                "professor": path_to_professor(path),
            })
    return docs


def save_cleaned_documents(docs: List[Dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        cleaned_text = clean_text(doc["raw_text"])
        clean_path = output_dir / doc["source"]
        clean_path.write_text(cleaned_text, encoding="utf-8")
        doc["clean_text"] = cleaned_text


def make_chunks(docs: List[Dict], chunk_size: int, overlap: int) -> List[Dict]:
    chunks = []
    for doc in docs:
        clean_text_content = doc.get("clean_text") or clean_text(doc["raw_text"])
        if not clean_text_content:
            continue
        doc_chunks = chunk_text(clean_text_content, chunk_size=chunk_size, overlap=overlap)
        for idx, chunk in enumerate(doc_chunks):
            chunks.append(
                {
                    "id": f"{doc['source']}::{idx}",
                    "source": doc["source"],
                    "professor": doc["professor"],
                    "text": chunk,
                    "chunk_index": idx,
                }
            )
    return chunks


def save_chunks(chunks: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest and chunk professor review documents.")
    parser.add_argument("--input", default="documents/raw", help="Directory containing raw .txt/.md files")
    parser.add_argument("--clean-output", default="documents/cleaned", help="Directory to save cleaned text files")
    parser.add_argument("--chunks-output", default="documents/chunks.jsonl", help="JSONL file for chunk metadata")
    parser.add_argument("--chunk-size", type=int, default=200, help="Approximate number of tokens per chunk")
    parser.add_argument("--overlap", type=int, default=50, help="Approximate number of overlapping tokens between chunks")
    args = parser.parse_args()

    input_dir = Path(args.input)
    clean_output_dir = Path(args.clean_output)
    chunks_output_path = Path(args.chunks_output)

    docs = load_documents(input_dir)
    if not docs:
        raise SystemExit(f"No supported documents found in {input_dir}")

    save_cleaned_documents(docs, clean_output_dir)
    chunks = make_chunks(docs, chunk_size=args.chunk_size, overlap=args.overlap)
    save_chunks(chunks, chunks_output_path)

    print(f"Loaded {len(docs)} documents from {input_dir}")
    print(f"Saved {len(docs)} cleaned documents to {clean_output_dir}")
    print(f"Produced {len(chunks)} chunks and wrote them to {chunks_output_path}")
    print("Sample chunks:\n")
    for sample in chunks[:5]:
        print(f"- {sample['id']} ({sample['source']})")
        print(sample["text"][:300] + ("..." if len(sample["text"]) > 300 else ""))
        print()


if __name__ == "__main__":
    main()
