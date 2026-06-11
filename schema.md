# Schema Documentation

## Input Schema

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
    "education": [
      {
        "degree": "B.Tech Computer Science",
        "institution": "IIT Madras",
        "grade": "9.1 CGPA"
      }
    ],
    "skills": [
      "Python",
      "PyTorch",
      "Transformers"
    ],
    "publications": []
  }
]
```

---

### Input Fields

| Field              | Type          | Description                |
| ------------------ | ------------- | -------------------------- |
| name               | string        | Student name               |
| research_interests | array[string] | Student research interests |
| target_countries   | array[string] | Preferred PhD countries    |
| target_intake      | string        | Intended admission intake  |
| education          | array[object] | Academic background        |
| skills             | array[string] | Technical skills           |
| publications       | array         | Previous publications      |

---

## Output Schema

The system generates a ranked list of supervisor recommendations.

Example:

```json
{
  "name": "Sagi Eppel",
  "institution": "University of Toronto",
  "country_code": "CA",
  "works_count": 67,
  "cited_by_count": 481,
  "research_topics": [
    "Artificial intelligence",
    "Computer vision"
  ],
  "recent_papers": [
    {
      "title": "Shape and Texture Recognition in Large Vision-Language Models",
      "year": 2025,
      "url": "https://doi.org/..."
    }
  ],
  "similarity_score": 0.42,
  "llm_match_score": 91,
  "research_focus": [
    "Computer Vision",
    "Vision Language Models"
  ],
  "why_match": "Strong alignment with the student's interests in machine learning and computer vision.",
  "is_good_match": true
}
```

---

## Output Fields

| Field            | Type          | Description                                                |
| ---------------- | ------------- | ---------------------------------------------------------- |
| name             | string        | Professor name                                             |
| institution      | string        | Current institution                                        |
| country_code     | string        | Country ISO code                                           |
| works_count      | integer       | Number of publications                                     |
| cited_by_count   | integer       | Total citations                                            |
| research_topics  | array[string] | OpenAlex research topics                                   |
| recent_papers    | array[object] | Recent publications                                        |
| similarity_score | float         | Semantic similarity score                                  |
| llm_match_score  | integer       | GPT-generated match score (0–100)                          |
| research_focus   | array[string] | Main research areas identified by the LLM                  |
| why_match        | string        | Personalized explanation                                   |
| is_good_match    | boolean       | Whether the candidate appears suitable as a PhD supervisor |

---
