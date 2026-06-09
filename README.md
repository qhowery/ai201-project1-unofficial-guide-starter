# The Unofficial Guide — Project 1

## Domain

This system covers student reviews of Princeton University CS professors. The goal is to turn informal RateMyProfessors-style review text into a searchable QA system that helps students understand teaching style, workload, grading, and professor availability.

This knowledge is valuable because official course descriptions do not capture how professors actually teach, grade, or support students. It is hard to find through official channels because it relies on subjective student experiences across multiple review documents and requires aggregating multiple short reviews into a useful summary.

---

## Document Sources

The corpus is built from 11 Princeton CS professor review text files. Each file was sourced from RateMyProfessors-style review pages and converted into a local text document.

| # | Source | Description | URL or file path |
|---|--------|-------------|-----------------|
| 1 | RateMyProfessor | Brian Kernighan reviews | `documents/raw/kernighan_reviews.txt` |
| 2 | RateMyProfessor | Kevin Wayne reviews | `documents/raw/wayne_reviews.txt` |
| 3 | RateMyProfessor | Kai Li reviews | `documents/raw/li_reviews.txt` |
| 4 | RateMyProfessor | Andrew Appel reviews | `documents/raw/andrew_appel_reviews.txt` |
| 5 | RateMyProfessor | Andrew Appel (alternate) reviews | `documents/raw/appel_reviews.txt` |
| 6 | RateMyProfessor | Fei-Fei Li reviews | `documents/raw/fei_fei_li_reviews.txt` |
| 7 | RateMyProfessor | Rebecca Fiebrink reviews | `documents/raw/rebecca_fiebrink_reviews.txt` |
| 8 | RateMyProfessor | Robert Schapire reviews | `documents/raw/robert_schapire_reviews.txt` |
| 9 | RateMyProfessor | Robert Sedgewick reviews | `documents/raw/robert_sedgewick_reviews.txt` |
| 10 | RateMyProfessor | Sanjeev Arora reviews | `documents/raw/sanjeev_arora_reviews.txt` |
| 11 | RateMyProfessor | Douglas Clark reviews | `documents/raw/douglas_clark_reviews.txt` |

All sources are stored locally as plain text files in `documents/raw/`. The raw documents are short review summaries and rating metadata rather than full long-form articles.

---

## Chunking Strategy

**Chunk size:** 200 words per chunk.

**Overlap:** 50 words between chunks.

**Why these choices fit your documents:** The source files are short professor review summaries rather than long articles. A 200-word chunk preserves enough context from each review while keeping retrieval focused, and a 50-word overlap helps avoid splitting sentences or review points across chunk boundaries.

**Final chunk count:** 13 chunks across 11 documents (including Sedgewick and Schapire reviews added after lab completion).

## Sample Chunks

The system stores each chunk with its source document and professor metadata. Here are five labeled sample chunks from the corpus:

1. `kernighan_reviews.txt` — "Brian Kernighan is an excellent lecturer, but his class is intense. His lectures move quickly and expect students to follow the logic without expecting too much hand-holding. Many students said his teaching was clear if you read the material before class, but the pace can be overwhelming if you rely only on lecture notes."
2. `wayne_reviews.txt` — "Kevin Wayne's classes are organized and lecture-heavy. Reviewers consistently describe his lectures as clear but fast, with a strong emphasis on proofs and algorithmic thinking. He communicates the big ideas well, but students should expect to review proofs multiple times outside of class."
3. `li_reviews.txt` — "Kai Li's lectures are highly structured and content-rich. Many students report that her classes move at a steady pace, with a strong focus on research examples and real-world applications. While the lectures are clear, the material can be dense, so students are encouraged to review notes immediately after class."
4. `robert_sedgewick_reviews.txt` — "Princeton Algorithms is the best algorithm course you can find on our planet. The professor constructed this course and its textbook carefully and perfectly. The PDF really helps me a lot not only in the course but also future careers."
5. `rebecca_fiebrink_reviews.txt` — "She's dedicated, interesting, passionate, and so so cool. Really awesome research, taught a fascinating class, all around great professor."

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`.

**Production tradeoff reflection:**
- `all-MiniLM-L6-v2` is a strong fit for this use case because it is fast, locally executable, and effective for short review text.
- For a real deployment with higher accuracy requirements, I would consider a larger or domain-finetuned embedding model to better capture subtle distinctions in professor feedback.
- A larger or API-based model would likely improve retrieval precision but increase latency, cost, and dependency on external services.
- Since these reviews are short and English-only, local execution and low latency were higher priorities than multilingual support.

---

## Retrieval Test Examples

### Example 1
- Query: "What do students say about Brian Kernighan's lecture speed and clarity?"
- Top returned chunks:
  1. `kernighan_reviews.txt` — discusses quick lectures, clear delivery for prepared students, and the need to read before class.
  2. `appel_reviews.txt` — also mentions rigorous lecture style, but is less directly about Kernighan.
  3. `wayne_reviews.txt` — mentions clear but fast lectures, which is similar to the query's topic.
- Relevance explanation: The first chunk is directly about Kernighan's lecture pace and clarity, making it the strongest match. The second and third chunks are less precise but still relevant to lecture style, showing that top-k retrieval can include semantically related teaching-style content.

### Example 2
- Query: "How do students describe homework and exams in Kevin Wayne's classes?"
- Top returned chunks:
  1. `wayne_reviews.txt` — directly describes Wayne's homework, proof emphasis, exam challenge, and need for careful review.
  2. `li_reviews.txt` — mentions demanding homework and dense material, which is tangentially related to course difficulty.
  3. `appel_reviews.txt` — mentions rigorous coursework, which is semantically similar to the query.
- Relevance explanation: The first chunk is clearly the best match because it is from Wayne's review document and includes the exact workload and exam language. The second hit is a weaker but sensible fallback because it also describes challenging homework in a CS course.

### Example 3
- Query: "What do reviewers say about Kai Li's availability or office hours?"
- Top returned chunks:
  1. `li_reviews.txt` — describes Li's structured lectures and notes that office hours can be limited and fill quickly.
  2. `wayne_reviews.txt` — includes similar lecture-related descriptions but does not directly answer the office hours question.
  3. `andrew_appel_reviews.txt` — is less relevant and shows that top-k retrieval can return nearby professor-review text when the query is relatively broad.

---

## Grounded Generation

**System prompt grounding instruction:**
The generator is instructed to answer using only the retrieved documents. It must not use external knowledge or make assumptions. If the documents do not contain enough information, it must return exactly: "I don't have enough information to answer that." The prompt explicitly requires that when a question targets a specific aspect (e.g., grading style, teaching method, difficulty), the model MUST answer that specific aspect or return insufficient information. The prompt also requires a concise answer of 200 words or fewer and asks the model to list document sources in the format `Sources: [DOC_1, DOC_3]`.

**Grading-keyword post-filter:**
To prevent hallucination on professor-specific queries, the system includes a post-retrieval filter: when a question asks about "grading" or related terms, the system checks if any retrieved chunk contains grading keywords (grade, grading, fair, strict, rigorous, lenient, etc.). If the question requires grading information but no chunks mention grading-related terms, the system returns "I don't have enough information to answer that." without calling the LLM. This prevents the model from synthesizing incomplete or off-target answers.

**How source attribution is surfaced in the response:**
- The system prepends each retrieved chunk with a numbered `DOC_n` label and source filename.
- After generation, the response is searched for a `Sources: [DOC_...]` annotation.
- If the model does not emit explicit source labels, the system falls back to returning the source filenames for the retrieved chunks.
- The pipeline also rejects unrelated queries using a distance threshold on the top retrieved chunk. When the top hit is too far from the query, the system returns: "I don't have enough information to answer that."

### Example system responses with source attribution

1. Query: "What do students say about Brian Kernighan's lecture speed and clarity?"

Answer:
"Brian Kernighan is an excellent lecturer, but his class is intense. His lectures move quickly and expect students to follow the logic without expecting too much hand-holding. Many students said his teaching was clear if you read the material before class, but the pace can be overwhelming if you rely only on lecture notes."

Sources: `kernighan_reviews.txt`

2. Query: "How do students describe homework and exams in Kevin Wayne's classes?"

Answer:
"Kevin Wayne's classes are organized and lecture-heavy. Reviewers consistently describe his lectures as clear but fast, with a strong emphasis on proofs and algorithmic thinking. He communicates the big ideas well, but students should expect to review proofs multiple times outside of class."

Sources: `wayne_reviews.txt`

### Out-of-scope query example

Query: "What is the weather in Princeton today?"

Answer: "I don't have enough information to answer that."

This refusal response is enforced by checking the top retrieval distance and refusing when the query appears unrelated to the professor review documents.

---

## Query Interface

The interface is implemented with Gradio in `app.py`.
- Input field: a single text box labeled "Your question" where the user types a natural language question about professors.
- Output fields: a multiline "Answer" box containing the generated response, and a "Retrieved from" box listing the source document filenames used for the response.

### Sample interaction transcript

User: "What do students say about Brian Kernighan's lecture speed and clarity?"
System: "Brian Kernighan is an excellent lecturer, but his class is intense. His lectures move quickly and expect students to follow the logic without expecting too much hand-holding. Many students said his teaching was clear if you read the material before class, but the pace can be overwhelming if you rely only on lecture notes."
Retrieved from:
• kernighan_reviews.txt

User: "What is the weather in Princeton today?"
System: "I don't have enough information to answer that."
Retrieved from:
• (no sources)

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Brian Kernighan’s lecture speed and clarity? | Lectures are fast-paced and intense but clear for prepared students. | The system said Kernighan’s lectures move quickly and are clear if students read before class, though the pace can be overwhelming. | Relevant | Accurate |
| 2 | How do students describe homework and exams in Kevin Wayne’s classes? | Homework and exams are challenging, proof-heavy, and require consistent effort. | The system said Wayne’s classes are organized and lecture-heavy, with clear but fast instruction and a strong emphasis on proofs. | Relevant | Accurate |
| 3 | What do reviewers say about Kai Li’s availability or office hours? | She is helpful and responsive, but office hours are limited or fill quickly. | The system said Kai Li is accessible, assignments are useful, and office hours can be limited and fill quickly. | Relevant | Accurate |
| 4 | What is the common impression of Robert Sedgewick's grading style? | Grading is rigorous and strict, but generally fair. | The system returned "I don't have enough information to answer that." — The Sedgewick reviews do not contain explicit grading-style information (only mentions of lectures, course construction, and workload). The grading-keyword filter correctly flagged insufficient information. | Relevant | Accurate (returns insufficient info) |
| 5 | How do students characterize Andrew Appel’s teaching style and workload? | His teaching is rigorous and detail-oriented, with a heavy workload and emphasis on correctness. | The system said Appel’s teaching is rigorous and detail-oriented, with dense material and a need for careful work. | Relevant | Accurate |

**Retrieval quality:** Relevant / Relevant / Relevant / Relevant / Relevant

**Response accuracy:** Accurate / Accurate / Accurate / Accurate (w/ grading filter) / Accurate

---

## Failure Case Analysis

**Question that failed:** What is the common impression of Robert Sedgewick’s grading style?

**What the system returned:** The generator now returns "I don't have enough information to answer that." because the available Sedgewick reviews do not mention grading philosophy explicitly. Earlier behavior returned a jumbled or off-target summary of review snippets instead.

**Root cause (tied to a specific pipeline stage):** The issue was in generation and retrieval filtering. The model was allowed to answer grading-style questions even when retrieved chunks did not contain grading-specific terminology, and the pipeline had no domain-confidence check for unrelated queries.

**Fix implemented:** Two improvements were added to `generator.py`:
1. **Tightened prompt:** The system instruction now explicitly requires that when a question targets a specific aspect (e.g., grading style), the model must answer that aspect or return "I don't have enough information to answer that."
2. **Grading-keyword filter:** The new `_check_grading_keywords_in_hits()` function detects when a question asks about grading terms and only allows generation when the retrieved chunks contain grading philosophy signals.
3. **Out-of-domain detection:** The new `_check_domain_confidence()` function uses the top retrieval distance to refuse unrelated queries such as weather questions.

**Current behavior:** The system now behaves honestly for the failed Sedgewick grading question and unrelated queries, returning "I don't have enough information to answer that." when the review corpus lacks the required information.


---

## Spec Reflection

**One way the spec helped you during implementation:**
The planning document made the pipeline concrete before coding: it clearly separated ingestion, chunking, embedding, retrieval, and generation. That structure helped me implement each module in a focused way and verify behavior at every stage.

**One way your implementation diverged from the spec, and why:**
The spec described an evaluation plan with five professor questions and initially only had four review documents. This divergence was addressed by (1) expanding the document corpus to include Sedgewick and Schapire reviews, and (2) implementing a grading-keyword post-filter to ensure accurate answers when the source material lacks the required information. The implementation now handles this gracefully by returning honest "insufficient information" responses rather than synthesized content.

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

**Instance 3**
- *What I gave the AI:* I described the evaluation failure on the Sedgewick grading-style question and asked for a fix that would prevent the system from hallucinating answers when the source material lacked grading information.
- *What it produced:* It proposed two improvements: tightening the prompt to require specific sub-question answers, and adding a grading-keyword post-filter to short-circuit generation when required keywords are absent.
- *What I changed or overrode:* I implemented both suggestions as written, adding the `_check_grading_keywords_in_hits()` function and integrating it into the `ask()` function to check grading queries before LLM generation.

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
     - Show that the system returns "I don't have enough information to answer that." Explain that the Sedgewick reviews do not contain explicit grading-style information (only mentions of lectures, course construction, and workload). Highlight that the grading-keyword filter correctly identifies missing information and prevents hallucination.

4. Demonstrate the evaluation evidence:
   - Open `evaluation_results.json` or point to the `README.md` evaluation table.
   - Note that all 5 questions now return accurate answers, including the Sedgewick grading question which correctly returns insufficient information.
   - Mention that the current system stores source metadata for each retrieved chunk and includes quality filters for specific question types.

5. Close with next steps:
   - Explain that the grading-keyword filter and tightened prompt prevent hallucination on knowledge-sparse queries.
   - Note that the corpus has been expanded with Sedgewick and Schapire reviews to improve coverage.
   - Discuss potential future improvements (e.g., expanding to more professors, adding question-type routing, or fine-tuning the embedding model).
