import json
import pycountry
import openalex
import enrich
import utils
import semantic_match
import llm

BASE_URL = "https://api.openalex.org"
MIN_CANDIDATES = 100

def main():
    # ── Load student ──
    with open("../data/student.json", "r", encoding="utf-8") as f:
        students = json.load(f)

    student = students[0]
    print(f"\nStudent : {student['name']}")

    # ── Get country codes ──
    country_codes = []
    for country_name in student["target_countries"]:
        country = pycountry.countries.get(name=country_name)
        if country:
            country_codes.append(country.alpha_2)
        else:
            print(f"⚠️  Unknown country: {country_name}")

    country_filter = "|".join(country_codes)
    print(f"Countries : {student['target_countries']}")
    print(f"Codes     : {country_codes}")

    openalex.search_with_country_filter(student,country_filter,country_codes)

    with open("../data/filtered_authors.json", "r", encoding="utf-8") as f:
        authors = json.load(f)

    enriched_authors = enrich.enrich_all_authors(authors)  
    verified_professors = utils.filter_professors(enriched_authors)

    for author in verified_professors:
        similarity = semantic_match.semantic_score_cal(author)
        author["similarity_score"] = similarity

    verified_professors.sort(key=lambda x:x["similarity_score"],reverse=True)
    top_60 = verified_professors[:60]

    result = llm.generate_shortlist(top_60, student)

if __name__ == "__main__":
    main()