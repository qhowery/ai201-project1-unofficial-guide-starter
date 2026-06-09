import argparse
import json
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer


def load_chunks(chunks_path: Path) -> list[dict]:
    chunks = []
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(model_name)


def build_vector_store(chunks: list[dict], persist_directory: Path, collection_name: str = "professor_reviews") -> None:
    client = chromadb.PersistentClient(path=str(persist_directory))

    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(name=collection_name)

    collection = client.create_collection(name=collection_name)

    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["id"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "professor": chunk.get("professor", ""),
            "chunk_index": chunk.get("chunk_index", 0),
            "chunk_id": chunk["id"],
        }
        for chunk in chunks
    ]

    model = load_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
    embeddings = [embedding.tolist() for embedding in embeddings]

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    print(f"Embedded {len(chunks)} chunks into Chroma collection '{collection_name}'")


def retrieve(query: str, persist_directory: Path, collection_name: str = "professor_reviews", top_k: int = 5, professor: Optional[str] = None) -> list[dict]:
    client = chromadb.PersistentClient(path=str(persist_directory))
    collection = client.get_collection(name=collection_name)

    model = load_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    query_embeddings = [query_embedding[0].tolist()]

    # If a professor filter is provided, use Chroma's metadata filtering to restrict results
    query_kwargs = {
        "query_embeddings": query_embeddings,
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if professor:
        # filter where metadata 'professor' equals the provided name
        query_kwargs["where"] = {"professor": professor}

    result = collection.query(**query_kwargs)

    hits = []
    # result may have fewer than top_k if filter applied
    num_results = len(result["documents"][0])
    for idx in range(num_results):
        metadata = result["metadatas"][0][idx]
        hits.append(
            {
                "id": metadata.get("chunk_id"),
                "text": result["documents"][0][idx],
                "metadata": metadata,
                "distance": result["distances"][0][idx],
            }
        )
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and query a Chroma vector store for professor review chunks.")
    parser.add_argument("--build", action="store_true", help="Build the vector store from documents/chunks.jsonl.")
    parser.add_argument("--query", type=str, help="Run a retrieval query against the built store.")
    parser.add_argument("--chunks", default="documents/chunks.jsonl", help="Path to the chunk JSONL file.")
    parser.add_argument("--persist-dir", default="vectordb", help="Directory where Chroma stores vectors.")
    parser.add_argument("--collection", default="professor_reviews", help="Chroma collection name.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve.")
    args = parser.parse_args()

    persist_dir = Path(args.persist_dir)

    if args.build:
        chunks = load_chunks(Path(args.chunks))
        if not chunks:
            raise SystemExit(f"No chunks found in {args.chunks}")
        build_vector_store(chunks, persist_dir, collection_name=args.collection)

    if args.query:
        hits = retrieve(args.query, persist_dir, collection_name=args.collection, top_k=args.top_k)
        print(f"Query: {args.query}\n")
        for hit in hits:
            print(f"id: {hit['id']}")
            print(f"source: {hit['metadata']['source']}")
            print(f"professor: {hit['metadata']['professor']}")
            print(f"distance: {hit['distance']}")
            print(f"text: {hit['text']}\n")


if __name__ == "__main__":
    main()
