import os
import re
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv()

from embed import retrieve
from pathlib import Path as _Path
try:
    from ingest import path_to_professor
except Exception:
    path_to_professor = None



def _build_prompt(question: str, hits: List[Dict]) -> str:
    docs = []
    for i, h in enumerate(hits, 1):
        src = h["metadata"]["source"] if "metadata" in h and "source" in h["metadata"] else h.get("source", "unknown")
        docs.append(f"[DOC_{i}] Source: {src}\n{h['text']}")

    docs_text = "\n\n".join(docs)

    system_instruction = (
        "You are an assistant that must answer using ONLY the information in the provided documents. "
        "Do NOT use any external knowledge or make assumptions. If the documents do not contain enough information to answer the question, respond exactly: \"I don't have enough information to answer that.\"\n\n"
        "Requirements:\n"
        "- Answer concisely (<=200 words) using only the documents below.\n"
        "- If the question asks about a specific aspect (e.g., grading style, teaching method, difficulty), "
        "you MUST answer that specific aspect. If the documents do not mention that aspect, respond: \"I don't have enough information to answer that.\"\n"
        "- After the answer, list the document sources used in the format: Sources: [DOC_1, DOC_3]\n"
        "- If the answer cannot be determined from the documents, ONLY respond with the exact sentence above.\n"
    )

    prompt = f"{system_instruction}\nQuestion: {question}\n\nDocuments:\n{docs_text}\n\nAnswer:"
    return prompt


def _groq_generate(prompt: str) -> str:
    try:
        from groq import Groq
    except Exception:
        raise
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    client = Groq()
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=256,
        temperature=0.0,
    )

    if hasattr(response, "choices") and response.choices:
        return response.choices[0].message.content or ""
    return str(response)


def _extractive_fallback(question: str, hits: List[Dict]) -> Dict:
    # Very small extractive fallback: pick sentences from top hits that contain question keywords
    qwords = re.findall(r"\w+", question.lower())
    if not qwords:
        return {"answer": "I don't have enough information to answer that.", "sources": []}

    matches = []
    for h in hits:
        text = h["text"]
        sentences = re.split(r'(?<=[.?!])\s+', text)
        for sent in sentences:
            s_low = sent.lower()
            # match at least one keyword (ignore stopwords by using first 6 content words)
            if any(w in s_low for w in qwords[:6]):
                matches.append((h["metadata"]["source"], sent.strip()))
    if not matches:
        return {"answer": "I don't have enough information to answer that.", "sources": []}

    # Use up to 3 sentences
    used = matches[:3]
    answer = " ".join(s for _, s in used)
    sources = list(dict.fromkeys([s for s, _ in [(u[0], u[1]) for u in used]]))
    return {"answer": answer, "sources": sources}


def _check_grading_keywords_in_hits(question: str, hits: List[Dict]) -> bool:
    """
    Check if question asks about grading/grading style, and if so, whether any hit mentions grading philosophy keywords.
    Returns True if question doesn't ask about grading (pass through), or if grading philosophy keywords are found.
    Returns False if question asks about grading but no philosophy keywords found (fail - insufficient info).
    """
    # Grading philosophy/style keywords (not student letter grades)
    grading_philosophy_keywords = {
        "grading policy", "grading style", "grading philosophy", "grading approach",
        "grades fairly", "grades harshly", "grades leniently",
        "harsh grader", "easy grader", "fair grader", "tough grader", "lenient grader", "strict grader",
        "harsh grading", "easy grading", "fair grading", "tough grading", "lenient grading", "strict grading",
        "rigorous grading", "rigorous grader",
        "grade fairly", "grade harshly", "grade leniently",
        "grading curve", "curved", "curving", "curves grades",
        "rubric", "rubrics", "grading criteria", "grading rubric"
    }
    
    question_low = question.lower()
    
    # Check if question asks about grading
    if not any(kw in question_low for kw in ["grading", "grade", "how does", "marking"]):
        return True  # Question doesn't ask about grading, pass through
    
    # Question asks about grading - check if any hit contains grading philosophy keywords
    for hit in hits:
        text = hit["text"].lower()
        if any(kw in text for kw in grading_philosophy_keywords):
            return True  # Found grading philosophy keywords
    
    return False  # Question asks about grading but no philosophy keywords found


def _check_domain_confidence(hits: List[Dict], threshold: float = 1.25) -> bool:
    """
    Return False when the top hit is too distant, suggesting the query is outside the professor review domain.
    """
    if not hits:
        return False
    return hits[0]["distance"] <= threshold


def ask(question: str, top_k: int = 5, persist_dir: str = "vectordb") -> Dict:
    # Try to detect a professor name in the question by comparing to filenames in documents/raw
    professor_name = None
    try:
        raw_dir = _Path("documents/raw")
        if raw_dir.exists() and path_to_professor:
            prof_list = []
            for p in sorted(raw_dir.iterdir()):
                if p.is_file():
                    prof_list.append(path_to_professor(p))

            q_low = question.lower()
            # try exact/full name match first
            for prof in prof_list:
                if prof.lower() in q_low:
                    professor_name = prof
                    break

            if not professor_name:
                # try last-name matches but prefer matches where first name also appears
                for prof in prof_list:
                    last = prof.split()[-1].lower()
                    if last and last in q_low:
                        # check if first name appears as well
                        first = prof.split()[0].lower()
                        if first in q_low:
                            professor_name = prof
                            break
                # if still not found, pick last-name match only if unique
                if not professor_name:
                    last_matches = [p for p in prof_list if p.split()[-1].lower() in q_low]
                    if len(last_matches) == 1:
                        professor_name = last_matches[0]
    except Exception:
        professor_name = None

    # Retrieve with optional professor filter; fall back to unfiltered if filtered retrieval returns nothing
    hits = retrieve(question, Path(persist_dir), top_k=top_k, professor=professor_name) if professor_name else retrieve(question, Path(persist_dir), top_k=top_k)
    if not hits and professor_name:
        hits = retrieve(question, Path(persist_dir), top_k=top_k)

    if not hits:
        return {"answer": "I don't have enough information to answer that.", "sources": []}

    # Reject queries that appear outside the document domain
    if not _check_domain_confidence(hits):
        return {"answer": "I don't have enough information to answer that.", "sources": []}

    # Check if question asks about grading style and if retrieved chunks contain grading keywords
    if not _check_grading_keywords_in_hits(question, hits):
        return {"answer": "I don't have enough information to answer that.", "sources": []}

    prompt = _build_prompt(question, hits)

    try:
        gen = _groq_generate(prompt)
        # post-process: try to extract sources from the model output (look for 'Sources: [DOC_1, DOC_2]')
        sources = []
        m = re.search(r"Sources:\s*\[(.*?)\]", gen)
        if m:
            refs = [r.strip() for r in m.group(1).split(",")]
            for r in refs:
                if r.startswith("DOC_"):
                    # map DOC_n to source filename
                    idx = int(r.split("_")[1]) - 1
                    if 0 <= idx < len(hits):
                        sources.append(hits[idx]["metadata"]["source"])
        # if no explicit sources, fall back to metadata
        if not sources:
            sources = list(dict.fromkeys([h["metadata"]["source"] for h in hits]))
        return {"answer": gen.strip(), "sources": sources}
    except Exception:
        # fallback to extractive answer
        return _extractive_fallback(question, hits)
