# The Unofficial Guide — Project 1

## Domain

This system covers student reviews of Princeton University CS professors. The goal is to turn informal review text into a searchable QA system that helps students understand teaching style, workload, and professor availability.

This knowledge is valuable because official course descriptions do not capture how professors actually teach, grade, or support students. It is hard to find through official channels because it relies on subjective student experiences across multiple review documents.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessor professor review | Text file | `documents/raw/kernighan_reviews.txt` |
| 2 | RateMyProfessor professor review | Text file | `documents/raw/wayne_reviews.txt` |
| 3 | RateMyProfessor professor review | Text file | `documents/raw/li_reviews.txt` |
| 4 | RateMyProfessor professor review | Text file | `documents/raw/appel_reviews.txt` |
| 5 | RateMyProfessor professor review | Text file | `documents/raw/andrew_appel_reviews.txt` |
| 6 | RateMyProfessor professor review | Text file | `documents/raw/fei_fei_li_reviews.txt` |
| 7 | RateMyProfessor professor review | Text file | `documents/raw/rebecca_fiebrink_reviews.txt` |
| 8 | RateMyProfessor professor review | Text file | `documents/raw/robert_schapire_reviews.txt` |
| 9 | RateMyProfessor professor review | Text file | `documents/raw/robert_sedgewick_reviews.txt` |
| 9 | RateMyProfessor professor review | Text file | `documents/raw/sanjeev_arora_reviews.txt` |
| 10 | RateMyProfessor professor review | Text file | `documents/raw/douglas_clark_reviews.txt` |

---

## Chunking Strategy

**Chunk size:** 200 words per chunk.

**Overlap:** 50 words between chunks.

**Why these choices fit your documents:** The source files are short professor review summaries rather than long articles. A 200-word chunk preserves enough context from each review while keeping retrieval focused, and a 50-word overlap helps avoid splitting sentences or review points across chunk boundaries.

**Final chunk count:** 5 chunks across 4 documents.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`.

**Production tradeoff reflection:**
- `all-MiniLM-L6-v2` is a strong fit for this use case because it is fast, locally executable, and effective for short review text.
- For a real deployment with higher accuracy requirements, I would consider a larger or domain-finetuned embedding model to better capture subtle distinctions in professor feedback.
- A larger model would likely improve retrieval precision but increase latency and resource cost.
- Since these documents are English professor reviews, multilingual support is not a priority, so I prioritized speed and local execution.

---

## Grounded Generation

**System prompt grounding instruction:**
The generator is instructed to answer using only the retrieved documents. It must not use external knowledge or make assumptions. If the documents do not contain enough information, it must return exactly: "I don't have enough information to answer that." The prompt also requires a concise answer of 200 words or fewer and asks the model to list document sources in the format `Sources: [DOC_1, DOC_3]`.

**How source attribution is surfaced in the response:**
- The system prepends each retrieved chunk with a numbered `DOC_n` label and source filename.
- After generation, the response is searched for a `Sources: [DOC_...]` annotation.
- If the model does not emit explicit source labels, the system falls back to returning the source filenames for the retrieved chunks.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Brian Kernighan’s lecture speed and clarity? | Lectures are fast-paced and intense but clear for prepared students. | The system said Kernighan’s lectures move quickly and are clear if students read before class, though the pace can be overwhelming. | Relevant | Accurate |
| 2 | How do students describe homework and exams in Kevin Wayne’s classes? | Homework and exams are challenging, proof-heavy, and require consistent effort. | The system said Wayne’s classes are organized and lecture-heavy, with clear but fast instruction and a strong emphasis on proofs. | Relevant | Accurate |
| 3 | What do reviewers say about Kai Li’s availability or office hours? | She is helpful and responsive, but office hours are limited or fill quickly. | The system said Kai Li is accessible, assignments are useful, and office hours can be limited and fill quickly. | Relevant | Accurate |
| 4 | What is the common impression of Robert Sedgewick’s grading style? | Grading is rigorous and strict, but generally fair. | The system returned content praising Sedgewick's lectures, textbook, and high workload but did not directly state grading-style (rigor/strictness). | Relevant | Partial/Inaccurate |
| 5 | How do students characterize Andrew Appel’s teaching style and workload? | His teaching is rigorous and detail-oriented, with a heavy workload and emphasis on correctness. | The system said Appel’s teaching is rigorous and detail-oriented, with dense material and a need for careful work. | Relevant | Accurate |

**Retrieval quality:** Relevant / Relevant / Relevant / Off-target / Relevant

**Response accuracy:** Accurate / Accurate / Accurate / Inaccurate / Accurate

---

## Failure Case Analysis

**Question that failed:** What is the common impression of Robert Sedgewick’s grading style?

**What the system returned:** The answer was off-target: it concatenated content from `rebecca_fiebrink_reviews.txt` and `sanjeev_arora_reviews.txt` (Fiebrink/Arora content) instead of Sedgewick evidence. Note: I attempted to fetch other missing profiles (including `robert_schapire_reviews.txt` at `https://www.ratemyprofessors.com/professor/1810546`) but the fetch failed (DNS resolution error), so that file remains a placeholder.
**What the system returned (after adding Sedgewick):** The generator returned praise for Sedgewick's lectures, course construction, and textbook, but it did not explicitly state the grading-style (rigorous/strict). The response was drawn from Sedgewick chunks, so retrieval was relevant, but the generation missed the precise evaluation focus.

**Root cause (tied to a specific pipeline stage):** The generator's prompt and postprocessing allowed the LLM to synthesize content from retrieved chunks without being forced to answer the specific subquestion about grading style. Even with correct retrieval, the model did not extract the grading-related signal (which may be absent or implicit in the chunks).

**What you would change to fix it:** Two practical fixes:
- Enforce professor-scoped retrieval (done) and additionally constrain generation: update the prompt to require the model to answer the specific sub-question ("grading style") and to return "I don't have enough information to answer that." when chunks do not mention grading.
- Add a post-filter: when the question targets a professor and includes terms like "grading", programmatically search retrieved chunks for grading-related keywords (grade, grading, fair, strict, rigorous) and return an extractive answer or "I don't have enough information" if none are found.


---

## Spec Reflection

**One way the spec helped you during implementation:**
The planning document made the pipeline concrete before coding: it clearly separated ingestion, chunking, embedding, retrieval, and generation. That structure helped me implement each module in a focused way and verify behavior at every stage.

**One way your implementation diverged from the spec, and why:**
The spec described an evaluation plan with five professor questions, but the current document corpus contains only four review files. I kept the same evaluation questions for honesty, then documented the failure that resulted from the missing Sedgewick document. This divergence highlights a real data limitation rather than a code issue.

---

## AI Usage

**Instance 1**
- *What I gave the AI:* I provided the chunking strategy and asked for a Python `chunk_text()` implementation that uses a fixed chunk size with overlap.
- *What it produced:* It returned a token-based splitting function that indexed words into overlapping segments.
- *What I changed or overrode:* I kept the chunk size at 200 and overlap at 50, and I ensured the implementation preserved professor metadata and generated stable chunk IDs.

**Instance 2**
- *What I gave the AI:* I described the grounded generation requirements and the prompt format, then asked for a function that builds a prompt and uses an LLM to answer from retrieved context.
- *What it produced:* It produced an initial prompt construction and response parsing flow.
- *What I changed or overrode:* I added explicit source extraction from `Sources: [DOC_1, DOC_3]`, and I added an extractive fallback in case the Groq API call failed.

---

## Video Demo Script

1. Launch the system:
   - Run `python app.py` from the project root.
   - Open the Gradio interface in the browser when the app starts.

2. Explain the pipeline briefly:
   - Mention `ingest.py` for cleaning and chunking raw professor reviews.
   - Mention `embed.py` for embedding chunks with `all-MiniLM-L6-v2` and storing them in Chroma.
   - Mention `generator.py` for grounded QA using retrieved chunks and `groq` generation.

3. Walk through 3 example queries:
   - Query: "What do students say about Brian Kernighan’s lecture speed and clarity?"
     - Show the system answer and point out the `Sources` field or source attribution in the response.
   - Query: "How do students describe homework and exams in Kevin Wayne’s classes?"
     - Show the answer and note that it is grounded in the `wayne_reviews.txt` chunks.
   - Query: "What is the common impression of Robert Sedgewick’s grading style?"
     - Show the failure case: the system retrieves Sedgewick content, but the generated answer still misses a clear grading-style statement. Emphasize this as a real limitation and explain that the current fix was to add professor-specific retrieval.

4. Demonstrate the evaluation evidence:
   - Open `evaluation_results.json` or point to the `README.md` evaluation table.
   - Note which questions were accurate and which one was partial/inaccurate.
   - Mention that the current system stores source metadata for each retrieved chunk.

5. Close with next steps:
   - Explain that improving prompt specificity or adding grading-keyword filtering would make the system more reliable for professor-specific questions.
   - Mention that the corpus is now expanded with Sedgewick and Schapire review text.
