from generator import ask

questions = [
    "What do students say about Brian Kernighan’s lecture speed and clarity?",
    "How do students describe homework and exams in Kevin Wayne’s classes?",
    "What do reviewers say about Kai Li’s availability or office hours?",
    "What is the common impression of Robert Sedgewick’s grading style?",
    "How do students characterize Andrew Appel’s teaching style and workload?",
]

results = []
for i, q in enumerate(questions, 1):
    print(f"\n=== Question {i} ===")
    print(q)
    res = ask(q)
    ans = res.get("answer") if isinstance(res, dict) else str(res)
    sources = res.get("sources", []) if isinstance(res, dict) else []
    print('\nAnswer:')
    print(ans)
    print('\nSources:')
    for s in sources:
        print('-', s)
    results.append({"question": q, "answer": ans, "sources": sources})

# Write results to file
import json
with open('evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('\nWrote evaluation_results.json')
