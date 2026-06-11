# PhD Supervisor Recommendation System

## Overview

This project recommends potential PhD supervisors for a student profile using a combination of:

* OpenAlex API for researcher discovery
* Semantic similarity matching using Sentence Transformers
* GPT-based evaluation using LangChain
* Country-aware filtering and PI verification

The system takes a student profile as input and generates a ranked shortlist of potential PhD supervisors along with personalized explanations for why each supervisor matches the student's background and interests.

---

## Features

* Researcher discovery using OpenAlex
* Country-specific supervisor recommendations
* PI (Principal Investigator) verification
* Semantic matching using publication titles
* LLM-based recommendation refinement
* Personalized `why_match` explanations
* Fully automated end-to-end pipeline
* Provider-independent LLM integration through LangChain

---

## Architecture

```text
Student Profile
        ↓
Country Filtering
        ↓
OpenAlex Retrieval
        ↓
Author Enrichment
        ↓
PI Verification
        ↓
Semantic Similarity Ranking
        ↓
Top Candidate Selection
        ↓
LLM Evaluation
        ↓
Final Shortlist
```

---

## Data Sources

### OpenAlex

OpenAlex is used for:

* Researcher discovery
* Publication metadata
* Citation statistics
* Research topics
* Institution information

Website:

https://openalex.org

---

### Large Language Model (LLM)

The final recommendation stage uses an LLM through LangChain to:

* Evaluate supervisor suitability
* Generate personalized recommendations
* Produce research focus areas
* Create `why_match` explanations

---

## Input Format

The system expects a student profile in JSON format.

Example:

```json
[
  {
    "name": "Priya Sharma",
    "research_interests": [
      "Machine Learning",
      "Natural Language Processing",
      "Computer Vision"
    ],
    "target_countries": [
      "Canada",
      "United Kingdom"
    ],
    "target_intake": "Fall 2025",
    "skills": [
      "Python",
      "PyTorch",
      "Transformers"
    ]
  }
]
```

Place the file at:

```text
data/student.json
```

---

## Project Structure

```text
project/
│
├── src/
│   ├── main.py
│   ├── openalex.py
│   ├── enrich.py
│   ├── semantic_match.py
│   ├── utils.py
│   └── llm.py
│
├── data/
│   ├── student.json
│
├── sample_output/
│   └── result.json
│
├── README.md
├── DECISIONS.md
├── schema.md
└── requirements.txt
```

---

## Pipeline Details

### Step 1: Load Student Profile

The student profile is loaded from:

```text
data/student.json
```

---

### Step 2: Country Filtering

Target countries are converted into ISO country codes using `pycountry`.

Example:

```text
Canada → CA
United Kingdom → GB
```

Only researchers associated with the selected countries are considered.

---

### Step 3: Researcher Retrieval

OpenAlex is queried using the student's research interests.

Candidate researchers are collected and stored for further processing.

---

### Step 4: Author Enrichment

For each researcher, the system retrieves:

* Publication count
* Citation count
* Research topics
* Recent publications

---

### Step 5: PI Verification

Researchers are filtered to identify likely PhD supervisors.

The verification process uses:

* Publication volume
* Citation statistics
* Research activity
* Affiliation information

This step removes many non-faculty researchers and low-confidence candidates.

---

### Step 6: Semantic Matching

A semantic similarity score is calculated between:

Student Profile:

```text
Research Interests
+
Skills
```

and

Professor Profile:

```text
Recent Publication Titles
```

using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This produces a deterministic ranking signal.

---

### Step 7: Candidate Selection

Candidates are sorted by similarity score.

The highest-ranked candidates are selected for LLM evaluation.

Current implementation:

```text
Top 60 Candidates
```

---

### Step 8: LLM Evaluation

The LLM evaluates each candidate and generates:

* Match score
* Research focus
* Personalized why_match explanation

---
## Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## OpenAI API Key

By default, the project uses OpenAI through LangChain.

Set your API key:

### Linux / Mac

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
```

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
```

---

## Using Other LLM Providers

An OpenAI API key is **not mandatory** if you want to use a different LLM provider.

The project uses LangChain, making it easy to switch providers.

Supported alternatives include:

* Anthropic Claude
* Google Gemini
* Azure OpenAI
* Ollama

To switch providers:

1. Install the corresponding LangChain package.
2. Update the LLM initialization inside `llm.py`.
3. Provide the required API key or endpoint configuration.

For example, the current implementation uses:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)
```

Replacing this block with another LangChain-supported provider is typically sufficient.

No changes are required in the rest of the application because all LLM interactions are abstracted through LangChain.

---

## Running the Project

Run the complete pipeline:

```bash
python main.py
```

The pipeline executes end-to-end and generates a ranked shortlist for the student profile.

---

## Output

The final shortlist is saved as:

```text
sample_output/result.json
```

---

## Output Format

Each recommendation contains information similar to:

```json
{
  "name": "Professor Name",
  "institution": "University Name",
  "country_code": "CA",
  "research_topics": [],
  "recent_papers": [],
  "similarity_score": 0.78,
  "llm_match_score": 88,
  "research_focus": [],
  "why_match": "Explanation of alignment",
  "is_good_match": true
}
```

Refer to `schema.md` for the complete schema definition.

---

## Design Trade-offs

### Precision Over Recall

The system prioritizes recommendation quality over recommendation quantity.

Potentially relevant researchers may be excluded if confidence is low.

### Semantic Filtering Before LLM Evaluation

Embedding-based filtering is performed before LLM evaluation to reduce:

* API cost
* Latency
* Token usage

### Hard Country Constraint

Recommendations are restricted to the student's selected countries.

This ensures compliance with user preferences.

### Modular Architecture

Each stage of the pipeline is separated into dedicated modules, making the system easier to debug, test, and extend.

---

## Known Limitations

* OpenAlex affiliation data may occasionally be incomplete.
* PI verification is heuristic-based and may not perfectly identify all supervisors.
* LLM-generated scores may vary slightly between runs.
* Some interdisciplinary researchers may rank lower if their recent publication titles do not strongly overlap with the student's profile.
* Recommendation quality depends on the quality of available metadata.

---

## Reproducibility

The complete recommendation pipeline can be reproduced using:

```bash
python main.py
```

provided that:

* Dependencies are installed
* A valid LLM provider is configured
* A student profile exists in `data/student.json`

No manual intervention is required after setup.

---

## Deliverables

This repository includes:

* README.md
* DECISIONS.md
* schema.md
* Source code
* Sample output JSON

as required by the assignment specification.

---

## Author

Developed as part of a PhD Supervisor Recommendation System assignment.
