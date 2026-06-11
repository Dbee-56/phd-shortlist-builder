# ─────────────────────────────────────────────
# PROFESSOR VERIFICATION
# ─────────────────────────────────────────────

# Known company/industry keywords — not universities
NON_ACADEMIC_KEYWORDS = [
    "google", "microsoft", "amazon", "meta", "apple",
    "deepmind", "openai", "ibm", "samsung", "huawei",
    "research lab", "inc.", "ltd", "corp", "technologies"
]

def is_academic_institution(institution_name: str) -> bool:
    """
    Check if institution is a university, not a company.
    """
    if not institution_name:
        return False

    name_lower = institution_name.lower()

    # ── Reject known companies ──
    for keyword in NON_ACADEMIC_KEYWORDS:
        if keyword in name_lower:
            return False

    # ── Accept known academic words ──
    academic_keywords = [
        "university", "université", "universität",
        "college", "institute", "school of",
        "faculty", "polytechnic", "academia"
    ]
    for keyword in academic_keywords:
        if keyword in name_lower:
            return True

    # ── Unknown — give benefit of doubt ──
    return True


def check_signal_1(author: dict) -> bool:
    """
    Signal 1: Has enough papers?
    PhD student typically has < 5 papers.
    Professor typically has 10+.
    """
    works_count = author.get("works_count", 0)
    return works_count >= 10


def check_signal_2(author: dict) -> bool:
    """
    Signal 2: Has enough citations?
    PhD student: 0–50 citations
    Professor: 500+ citations
    We use 100 as a safe lower threshold.
    """
    cited_by_count = author.get("cited_by_count", 0)
    return cited_by_count >= 200


def check_signal_3(author: dict) -> bool:
    """
    Signal 3: Is institution a real university?
    Rejects companies like Google, Microsoft etc.
    """
    institution = author.get("institution", "")
    return is_academic_institution(institution)


def verify_professor(author: dict) -> dict:
    """
    Run all 3 signals and compute a score.
    Author needs score >= 3 to be considered a real PI.

    Returns author with added fields:
      - pi_score       : 0, 1, 2, or 3
      - is_pi          : True / False
      - pi_fail_reason : why they were rejected (if any)
    """
    s1 = check_signal_1(author)   # enough papers?
    s2 = check_signal_2(author)   # enough citations?
    s3 = check_signal_3(author)   # academic institution?

    score = sum([s1, s2, s3])
    is_pi = score >= 3

    # Build fail reason for transparency
    fail_reasons = []
    if not s1:
        fail_reasons.append(
            f"only {author.get('works_count', 0)} papers (need 10+)"
        )
    if not s2:
        fail_reasons.append(
            f"only {author.get('cited_by_count', 0)} citations (need 200+)"
        )
    if not s3:
        fail_reasons.append(
            f"institution '{author.get('institution')}' not academic"
        )

    author["pi_score"]       = score
    author["is_pi"]          = is_pi
    author["pi_fail_reason"] = ", ".join(fail_reasons) if fail_reasons else None

    return author


def filter_professors(authors: list) -> list:
    """
    Run PI verification on all authors.
    Returns only verified professors.
    """
    print(f"\n{'='*50}")
    print("PROFESSOR VERIFICATION")
    print(f"{'='*50}")
    print(f"  Checking {len(authors)} authors...\n")

    verified    = []
    rejected    = []

    for author in authors:
        result = verify_professor(author)

        if result["is_pi"]:
            verified.append(result)
        else:
            rejected.append(result)
            print(
                f"  SKIP  {author['name']:<30}"
                f" | score={result['pi_score']}"
                f" | {result['pi_fail_reason']}"
            )

    print(f"\n  ── Verification Results ──")
    print(f"  Input      : {len(authors)}")
    print(f"  Verified PI: {len(verified)}")
    print(f"  Rejected   : {len(rejected)}")

    return verified