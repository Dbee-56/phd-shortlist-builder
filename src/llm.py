import os
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts  import PromptTemplate
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

def assign_tier(similarity_score: float) -> str:
    """
    Assign tier based on cosine similarity score.
 
    Thresholds chosen based on cosine similarity distribution:
      High similarity  (0.45+) → reach   (top match, competitive PI)
      Medium           (0.30+) → target  (good realistic match)
      Lower            (<0.30) → safety  (weaker match but still relevant)
    """
    if similarity_score >= 0.45:
        return "reach"
    elif similarity_score >= 0.30:
        return "target"
    else:
        return "safety"
    
# ─────────────────────────────────────────────
# BATCH WHY_MATCH GENERATION (6 calls instead of 60)
# ─────────────────────────────────────────────

BATCH_PROMPT = PromptTemplate(
    input_variables=[
        "student_name",
        "student_interests", 
        "student_background",
        "professors_batch"
    ],
    template="""
You are helping a student write personalised PhD application emails.

STUDENT NAME: {student_name}
STUDENT RESEARCH INTERESTS: {student_interests}
STUDENT BACKGROUND: {student_background}

Below are {batch_size} professors. For EACH professor write a personalised
3-4 sentence why_match explaining why they are a good supervisor match.

Rules:
- Be SPECIFIC — mention professor's actual research topics
- Connect it to student's actual interests
- NO generic phrases like "highly regarded" or "excellent mentor"

PROFESSORS:
{professors_batch}

Reply ONLY in this exact JSON format, nothing else:
[
  {{
    "author_id": "https://openalex.org/A123",
    "why_match": "2-3 sentences here..."
  }},
  ...
]
"""
)


def format_batch_for_prompt(batch: list) -> str:
    """
    Format a batch of professors into readable text for the prompt.
    """
    lines = []
    for i, prof in enumerate(batch, 1):
        papers = " | ".join([
            p["title"] for p in prof.get("recent_papers", [])[:2]
        ])
        topics = ", ".join(prof.get("research_topics", [])[:4])
        
        lines.append(
            f"{i}. ID: {prof['author_id']}\n"
            f"   Name: {prof['name']}\n"
            f"   Institution: {prof['institution']}\n"
            f"   Topics: {topics}\n"
            f"   Recent Papers: {papers}"
        )
    return "\n\n".join(lines)


def generate_why_match_batch(
    batch: list,
    student: dict
) -> dict:
    """
    Generate why_match for a batch of 10 professors in ONE LLM call.
    Returns dict: { author_id → why_match string }
    """
    professors_text = format_batch_for_prompt(batch)

    prompt_text = BATCH_PROMPT.format(
        student_name       = student.get("name", "the student"),
        student_interests  = ", ".join(student.get("research_interests", [])),
        student_background = student.get("intro_call_summary", ""),
        professors_batch   = professors_text,
        batch_size         = len(batch)
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt_text)])
        raw      = response.content.strip()

        # Strip markdown code fences if LLM adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        results  = json.loads(raw)

        # Convert list → dict keyed by author_id
        return {
            item["author_id"]: item["why_match"]
            for item in results
        }

    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON parse error in batch: {e}")
        # Fallback: return empty so individual fallback kicks in
        return {}

    except Exception as e:
        print(f"    ⚠️  Batch LLM error: {e}")
        return {}


def generate_all_why_matches(
    top_60: list,
    student: dict,
    batch_size: int = 10
) -> dict:
    """
    Process all professors in batches of 10.
    Returns dict: { author_id → why_match string }

    60 professors / 10 per batch = 6 API calls total
    """
    print(f"\n  Generating why_match in batches of {batch_size}...")
    print(f"  Total professors : {len(top_60)}")
    print(f"  Total API calls  : {len(top_60) // batch_size + 1}\n")

    all_why_matches = {}

    # Split into batches
    batches = [
        top_60[i : i + batch_size]
        for i in range(0, len(top_60), batch_size)
    ]

    for i, batch in enumerate(batches, 1):
        print(f"  Batch [{i}/{len(batches)}] — {len(batch)} professors...")

        batch_results = generate_why_match_batch(batch, student)

        if batch_results:
            all_why_matches.update(batch_results)
            print(f"    ✅ Got {len(batch_results)} why_matches")
        else:
            # Batch failed — generate fallback for each professor
            print(f"    ⚠️  Batch failed — using fallback text")
            for prof in batch:
                topics = ", ".join(prof.get("research_topics", [])[:3])
                interests = ", ".join(student.get("research_interests", [])[:2])
                all_why_matches[prof["author_id"]] = (
                    f"Prof. {prof['name']}'s work on {topics} "
                    f"aligns with the student's interest in {interests}."
                )

    print(f"\n  Total why_matches generated: {len(all_why_matches)}")
    return all_why_matches

def generate_shortlist(top_60: list, student: dict, output_dir: str = "../sample_output") -> dict:

    print("\n" + "="*55)
    print("  GENERATING FINAL SHORTLIST")
    print("="*55)

    # ── Generate ALL why_matches in 6 batch calls ──
    all_why_matches = generate_all_why_matches(top_60, student, batch_size=10)

    shortlist = []

    for professor in top_60:
        author_id = professor["author_id"]

        # Get why_match from batch results
        why_match = all_why_matches.get(author_id)

        # If missing for any reason use fallback
        if not why_match:
            topics    = ", ".join(professor.get("research_topics", [])[:3])
            interests = ", ".join(student.get("research_interests", [])[:2])
            why_match = (
                f"Prof. {professor['name']}'s work on {topics} "
                f"aligns with the student's interest in {interests}."
            )

        entry = build_entry(professor, student, why_match)
        shortlist.append(entry)

    # # Sort by similarity score
    # shortlist.sort(key=lambda x: x["similarity_score"], reverse=True)

    output = {
        "student_name": student.get("name"),
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total":        len(shortlist),
        "tier_summary": {
            "reach":  sum(1 for e in shortlist if e["tier"] == "reach"),
            "target": sum(1 for e in shortlist if e["tier"] == "target"),
            "safety": sum(1 for e in shortlist if e["tier"] == "safety"),
        },
        "shortlist": shortlist
    }

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "result.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  ✅ Saved → {filepath}")
    print(f"  Total  : {output['total']}")
    print(f"  Reach  : {output['tier_summary']['reach']}")
    print(f"  Target : {output['tier_summary']['target']}")
    print(f"  Safety : {output['tier_summary']['safety']}")

    return output


# Updated build_entry — now accepts why_match as parameter
def build_entry(professor: dict, student: dict, why_match: str) -> dict:
    return {
        "name":           professor.get("name"),
        "institution":    professor.get("institution"),
        "country":        professor.get("country_code"),
        "contact_email":  None,
        "research_focus": ", ".join(professor.get("research_topics", [])[:5]),
        "evidence": {
            "papers": professor.get("recent_papers", []),
            "openalex_profile": professor.get("author_id")
        },
        "why_match":        why_match,
        "tier":             assign_tier(professor["similarity_score"])
    }