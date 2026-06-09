#!/usr/bin/env python3
from pathlib import Path
from generator import ask, _check_grading_keywords_in_hits
from embed import retrieve

print("=" * 80)
print("Testing Sedgewick grading question")
print("=" * 80)

question = "What is the common impression of Robert Sedgewick's grading style?"
print(f"\nQuestion: {question}\n")

# Test retrieval
print("Step 1: Retrieve chunks")
hits = retrieve(question, Path("vectordb"), top_k=5, professor="Robert Sedgewick")
print(f"Retrieved {len(hits)} hits")
for i, hit in enumerate(hits):
    print(f"\n  Hit {i+1}:")
    print(f"    Source: {hit['metadata']['source']}")
    print(f"    Professor: {hit['metadata']['professor']}")
    print(f"    Text preview: {hit['text'][:100]}...")

# Test grading keyword filter
print("\n" + "=" * 80)
print("Step 2: Check grading-keyword filter")
filter_result = _check_grading_keywords_in_hits(question, hits)
print(f"Filter result: {filter_result}")
if filter_result:
    print("→ Filter PASSED (grading keywords found or question doesn't ask about grading)")
else:
    print("→ Filter FAILED (question asks about grading but no keywords found)")

# Test full ask
print("\n" + "=" * 80)
print("Step 3: Full ask() function")
result = ask(question)
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
