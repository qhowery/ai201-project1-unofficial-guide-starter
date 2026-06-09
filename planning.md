# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

--- I chose the domain "student reviews of CS professors at Princeton University". It is valuable because incoming students can be informed of their professors. It's hard to find because Princeton does not back this with an official review site. 

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RateMyProfessor | Brian Kernighan reviews | `documents/raw/kernighan_reviews.txt` |
| 2 | RateMyProfessor | Kevin Wayne reviews | `documents/raw/wayne_reviews.txt` |
| 3 | RateMyProfessor | Kai Li reviews | `documents/raw/li_reviews.txt` |
| 4 | RateMyProfessor | Andrew Appel reviews | `documents/raw/andrew_appel_reviews.txt` |
| 5 | RateMyProfessor | Andrew Appel alternate reviews | `documents/raw/appel_reviews.txt` |
| 6 | RateMyProfessor | Fei-Fei Li reviews | `documents/raw/fei_fei_li_reviews.txt` |
| 7 | RateMyProfessor | Rebecca Fiebrink reviews | `documents/raw/rebecca_fiebrink_reviews.txt` |
| 8 | RateMyProfessor | Robert Schapire reviews | `documents/raw/robert_schapire_reviews.txt` |
| 9 | RateMyProfessor | Robert Sedgewick reviews | `documents/raw/robert_sedgewick_reviews.txt` |
| 10 | RateMyProfessor | Sanjeev Arora reviews | `documents/raw/sanjeev_arora_reviews.txt` |
| 11 | RateMyProfessor | Douglas Clark reviews | `documents/raw/douglas_clark_reviews.txt` |

> Local review documents are stored as plain text files in `documents/raw/` and processed by `ingest.py`.
---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 200 words (approximately 1200–1500 characters)

**Overlap:** 50 words (approximately 300–400 characters)

**Reasoning:**
- RateMyProfessor review pages are built from short, user-generated comments that often jump between workload, exams, teaching style, and grading.
- A 200-word chunk keeps each chunk focused on a short review segment while preserving enough context for meaning.
- The 50-word overlap prevents important opinions from being split across chunk boundaries, especially when a single review comment spans multiple topics.
- Preprocessing removes HTML boilerplate and navigation artifacts while preserving professor names, ratings, and source metadata.

**Final chunk count:** 13 chunks across 11 documents.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers

**Top-k:** 5

**Production tradeoff reflection:**
- all-MiniLM-L6-v2 is a strong fit for short review text because it is fast, cost-efficient, and effective for semantic similarity on conversational text.
- If cost were not a constraint, I would choose a larger embedding model such as OpenAI’s text-embedding-3-large or a domain-finetuned variant to capture subtle cues in professor feedback and grading comments.
- For real users I would weigh accuracy versus latency: higher-quality embeddings can improve retrieval precision, but they are slower and more expensive.
- Since the domain is primarily English and review-focused, multilingual support is less important than robustness to informal phrasing.
- I would also consider an out-of-domain detection threshold in production so the system can refuse unrelated queries rather than attempt to answer them from noisy review text.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Brian Kernighan’s lecture speed and clarity? | Students should say his lectures are fast-paced, technically deep, and generally clear for engaged learners. |
| 2 | How do students describe homework and exams in Kevin Wayne’s classes? | Students should report that his homework and exams are challenging, proof-heavy, and require consistent effort. |
| 3 | What do reviewers say about Kai Li’s availability or office hours? | Expected answer: she is helpful and responsive, but office hours can be limited or hard to schedule. |
| 4 | What is the common impression of Robert Sedgewick’s grading style? | Expected answer: grading is rigorous and strict, but many students consider it fair. |
| 5 | How do students characterize Andrew Appel’s teaching style and workload? | Expected answer: his teaching is rigorous and detail-oriented, with a heavy workload and strong emphasis on correctness. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. The source pages may include navigation, ads, or other non-review text that could pollute embeddings and retrieval.
   - Mitigation: strip HTML boilerplate, only index review text, and preserve source metadata per chunk.

2. Reviews often mix multiple topics in a single comment, so chunk boundaries could separate workload, exam, and teaching-style signals.
   - Mitigation: use moderate overlap and validate retrieval on test queries to ensure topic continuity.

3. Grounded generation can still hallucinate if the LLM sees loosely related chunks.
   - Mitigation: use a strict prompt that instructs the model to answer only from retrieved evidence and to say "I don’t know" when the documents do not contain the answer.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```mermaid
flowchart TD
  A[Document Ingestion] --> B[Chunking]
  B --> C[Embedding + Vector Store]
  C --> D[Retrieval]
  D --> E[Generation]

  A -->|ingest.py| B
  B -->|chunk_text()| C
  C -->|SentenceTransformers + Chroma| D
  D -->|top-k similarity search| E
  E -->|generator.py| User
```

- Document Ingestion: scrape or load RateMyProfessor pages, clean text, remove navigation/HTML boilerplate.
- Chunking: split reviews into 200-word chunks with 50-word overlap and attach professor/source metadata.
- Embedding + Vector Store: embed chunks with all-MiniLM-L6-v2 and store vectors in Chroma.
- Retrieval: run top-5 similarity search on query embeddings.
- Generation: use a grounded prompt to answer from retrieved chunks and cite sources.

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
- Tool: ChatGPT or Copilot.
- Input: this Chunking Strategy section and sample RateMyProfessor review text.
- Expected output: a `chunk_text()` implementation that splits on sentences, applies overlap, and records professor/source metadata.
- Verification: run the function on sample page text and confirm chunk lengths, overlap, and metadata are correct.

**Milestone 4 — Embedding and retrieval:**
- Tool: ChatGPT or Copilot.
- Input: Retrieval Approach section and sample chunk data.
- Expected output: a vector store builder and a retrieval function returning the top-5 most relevant chunks.
- Verification: query known phrases and confirm retrieved chunks match expected professor review content.

**Milestone 5 — Generation and interface:**
- Tool: ChatGPT or Copilot.
- Input: Grounded Generation prompt structure and retrieved chunk examples.
- Expected output: a grounded response generator that uses retrieved evidence and cites professor sources.
- Verification: run the 5 evaluation questions and confirm answers are evidence-based and correctly attributed.
