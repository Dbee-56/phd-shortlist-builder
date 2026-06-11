import time
import requests
import json

BASE_URL = "https://api.openalex.org"
MIN_CANDIDATES = 100

# with open("../data/student.json", "r", encoding="utf-8") as f:
#     students = json.load(f)

# student = students[0]

# country_filter = find_country_code(student)

# Search Works on related topics
def search_works(query, country_filter=None, pages=2, per_page=100):
    """Search OpenAlex works (papers) by query and optional country filter."""
    works = []

    for page in range(1, pages + 1):

        params = {
            "search":   query,
            "page":     page,
            "per-page": per_page
        }

        if country_filter:
            params["filter"] = f"authorships.institutions.country_code:{country_filter}"

        try:
            response = requests.get(
                f"{BASE_URL}/works",
                params=params,
                timeout=30
            )

            if response.status_code != 200:
                print(f"  ⚠️  Failed page {page}: {response.status_code}")
                continue

            data  = response.json()
            batch = data.get("results", [])
            works.extend(batch)

            # Small delay — be polite to API
            time.sleep(0.3)

        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Request error on page {page}: {e}")
            continue

    return works


# ─────────────────────────────────────────────
# EXTRACT AUTHORS FROM WORKS
# ─────────────────────────────────────────────

def extract_authors(works):
    """
    Extract unique authors from a list of works.
    For each author, tries ALL their institutions (not just [0])
    to find a country_code.
    """
    authors = {}

    for work in works:
        for authorship in work.get("authorships", []):

            author     = authorship.get("author", {})
            author_id  = author.get("id")

            if not author_id:
                continue

            institutions = authorship.get("institutions", [])

            # ── FIX 1: Loop ALL institutions, not just [0] ──
            country_code     = None
            institution_name = None

            for inst in institutions:
                code = inst.get("country_code")
                name = inst.get("display_name")

                if code:                        # found a valid country
                    country_code     = code
                    institution_name = name
                    break                       # stop at first valid one

                if name and not institution_name:
                    institution_name = name     # save name even if no code

            # ── Store author (keep richest data if seen before) ──
            if author_id not in authors:
                authors[author_id] = {
                    "author_id":        author_id,
                    "name":             author.get("display_name"),
                    "country_code":     country_code,
                    "institution":      institution_name,
                    "country_resolved": country_code is not None
                }
            else:
                # Already seen — update if we now have better data
                existing = authors[author_id]

                if not existing["country_code"] and country_code:
                    existing["country_code"]     = country_code
                    existing["institution"]      = institution_name
                    existing["country_resolved"] = True

    return list(authors.values())


def filter_by_country(authors: list, allowed_codes: list) -> list:
    """
    Filter authors to only those in allowed countries.

    2-level strategy per author:
      Level 1 — Use country_code already extracted from papers
      Level 2 — If still null: SKIP (safer than guessing)
    """
    print(f"\n  Filtering {len(authors)} authors for countries: {allowed_codes}")

    passed                = []
    skipped_wrong_country = 0
    skipped_null_country  = 0
    resolved_via_fallback = 0

    for author in authors:

        country_code = author.get("country_code")

        if country_code:
            if country_code in allowed_codes:
                passed.append(author)
            else:
                skipped_wrong_country += 1
            continue

        else:
            skipped_null_country += 1
            print(f"      ❌ Could not resolve country — skipping")

    print(f"\n  ── Country Filter Results ──────────────────")
    print(f"  Input authors             : {len(authors)}")
    print(f"  Passed ✅                 : {len(passed)}")
    print(f"  Skipped (wrong country)   : {skipped_wrong_country}")
    print(f"  Skipped (null/unresolved) : {skipped_null_country}")
    print(f"  Resolved via fallback     : {resolved_via_fallback}")

    return passed

def search_with_country_filter(student,country_filter,country_codes):
    # ════════════════════════════════
    # PASS 1 — Search WITH country filter
    # ════════════════════════════════
    print("\n" + "─"*55)
    print("PASS 1: Searching with country filter")
    print("─"*55)

    unique_authors = {}

    for interest in student["research_interests"]:
        print(f"\n  Searching: '{interest}'")

        works   = search_works(query=interest, country_filter=country_filter, pages=2)
        authors = extract_authors(works)

        print(f"  → {len(works)} papers → {len(authors)} authors extracted")

        for author in authors:
            unique_authors[author["author_id"]] = author

    candidate_authors = list(unique_authors.values())
    print(f"\nPass 1 total unique authors : {len(candidate_authors)}")

    # ── Apply country filter to Pass 1 results ──
    # (API filter is approximate — must verify manually too)
    candidate_authors = filter_by_country(candidate_authors, country_codes)
    print(f"Pass 1 after country filter : {len(candidate_authors)}")

    # ════════════════════════════════
    # PASS 2 — Fallback (no country filter, filter manually)
    # ════════════════════════════════
    if len(candidate_authors) < MIN_CANDIDATES:
        print("\n" + "─"*55)
        print(f"PASS 2: Fallback — only {len(candidate_authors)} found, need {MIN_CANDIDATES}")
        print("─"*55)

        fallback_raw = {}

        for interest in student["research_interests"]:
            print(f"\n  Fallback searching: '{interest}'")

            works   = search_works(query=interest, country_filter=None, pages=5)
            authors = extract_authors(works)

            print(f"  → {len(works)} papers → {len(authors)} authors extracted")

            for author in authors:
                # Only add if NOT already in our list
                if author["author_id"] not in unique_authors:
                    fallback_raw[author["author_id"]] = author

        fallback_list = list(fallback_raw.values())
        print(f"\n  New authors from fallback : {len(fallback_list)}")

        # ── Filter fallback results by country ──
        fallback_filtered = filter_by_country(fallback_list, country_codes)

        # ── Merge with Pass 1 results ──
        for author in fallback_filtered:
            unique_authors[author["author_id"]] = author

        candidate_authors = list(unique_authors.values())

    # ════════════════════════════════
    # FINAL RESULTS
    # ════════════════════════════════
    print("\n" + "="*55)
    print("FINAL RESULTS")
    print("="*55)
    print(f"  Total verified authors : {len(candidate_authors)}")

    print("\n  Sample (first 20):")
    print(f"  {'Name':<30} {'Institution':<35} {'Country'}")
    print(f"  {'─'*30} {'─'*35} {'─'*7}")

    for author in candidate_authors[:20]:
        name    = (author["name"]        or "Unknown")[:29]
        inst    = (author["institution"] or "Unknown")[:34]
        country =  author["country_code"] or "???"
        print(f"  {name:<30} {inst:<35} {country}")

    # ── Save results ──
    with open("../data/filtered_authors.json", "w") as f:
        json.dump(candidate_authors, f, indent=2)

    print(f"\n  💾 Saved to: data/filtered_authors.json")

