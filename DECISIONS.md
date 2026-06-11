# 📋 Decision Log — PhD Shortlist Builder

This document explains the key technical and architectural decisions made during the development of this project, and the reasoning behind each choice.

---

## 1. Why OpenAlex over Google Scholar / Scopus / PubMed?

**Decision:** Use OpenAlex as the primary academic search API.

**Reasoning:**
- **Free & open** — No API key required, no rate-limit paywalls
- **Rich metadata** — Returns author affiliations, institution country, h-index, and works in a single response
- **Country filtering** — Supports filtering authors by institution country natively, which is core to this tool
- **Actively maintained** — OpenAlex is backed by a non-profit (OurResearch) and regularly updated

**Alternatives considered:**
| API | Why Rejected |
|-----|-------------|
| Google Scholar | No official API; scraping violates ToS |
| Scopus / Web of Science | Paid API, institutional access required |
| PubMed | Biomedical focus only; not general enough |
| Semantic Scholar | Good alternative; lacks country-level filtering |

---

## 2. Why a Two-Stage Filtering Pipeline (Semantic Score → LLM)?

**Decision:** First score all candidates with a lightweight semantic model, then pass only the top 60 to the LLM.

**Reasoning:**
- **Cost efficiency** — LLM API calls are expensive. Running GPT-4 on 500+ raw candidates would be wasteful and slow
- **LLM context limits** — Passing hundreds of full author profiles would exceed context windows
- **Speed** — Sentence transformers run locally and are fast; LLM calls are slow
- **Quality** — Pre-filtering ensures the LLM only reasons over genuinely relevant candidates, improving output quality

**Flow rationale:**
```
500+ raw authors → semantic filter → top 60 → LLM → final shortlist of ~10-15
```

This mirrors how a human would work: first skim resumes for keywords, then deeply evaluate the best ones.

---

## 3. Why LangChain for LLM Integration?

**Decision:** Use LangChain as the abstraction layer for LLM calls in `llm.py`.

**Reasoning:**
- **Provider flexibility** — Swapping OpenAI for Claude, Gemini, or a local Ollama model requires changing only 2 lines (see README)
- **Prompt management** — LangChain's prompt templates make it easy to iterate on the shortlisting prompt without touching logic
- **Future extensibility** — If we add memory, chains, or agents later, LangChain supports this natively

**Trade-off:** LangChain adds a dependency and abstraction layer. For a simple single-LLM use case, calling the OpenAI SDK directly would be lighter. We accepted this trade-off for long-term flexibility.

---

## 4. Why `utils.filter_professors()` — What Counts as a "Verified Professor"?

**Decision:** Add a filtering step after enrichment to remove non-faculty results.

**Reasoning:**
- OpenAlex returns all authors, including PhD students, postdocs, and industry researchers
- PhD supervisors must be active faculty with an institutional affiliation
- Filtering by position/affiliation metadata reduces noise before semantic scoring
- This improves the signal-to-noise ratio for downstream steps

---

## 5. Why Semantic Similarity Scoring Before LLM Ranking?

**Decision:** Use `sentence-transformers` to compute a similarity score between the student's research interests and each professor's publication abstracts.

**Reasoning:**
- Keyword matching alone misses conceptually related work (e.g., "deep learning" vs "neural networks")
- Semantic embeddings capture meaning, not just vocabulary overlap
- Running this locally (no API cost) makes it viable for large candidate pools
- The score gives a deterministic, reproducible ranking signal unlike LLM outputs

**Model choice:** A lightweight model (e.g., `all-MiniLM-L6-v2`) balances speed and accuracy for this use case.

---

## 6. Why Top 60 Candidates to the LLM?

**Decision:** Pass exactly the top 60 semantically scored professors to the LLM.

**Reasoning:**
- 60 profiles fit comfortably within a 128k context window with room for the prompt and output
- Empirically, the top 60 by semantic score contains all genuinely relevant supervisors
- Fewer than 60 risks missing niche but highly relevant professors who scored slightly lower
- More than 60 increases cost and risks the LLM losing focus on the most relevant candidates

This number can be tuned via the `top_60 = verified_professors[:60]` line in `main.py`.

---

## 7. Why `pycountry` for Country Name → Code Conversion?

**Decision:** Use the `pycountry` library to convert country names like "United States" to ISO codes like "US".

**Reasoning:**
- OpenAlex filters require ISO 3166-1 alpha-2 country codes, not plain text names
- `pycountry` is a lightweight, offline library with no API dependency
- It handles edge cases like "United Kingdom" vs "UK" vs "GB"
- The warning for unknown countries (`⚠️ Unknown country`) helps surface data issues early

---
