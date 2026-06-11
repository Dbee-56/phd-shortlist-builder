from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

session = requests.Session()

def get_recent_paper_topics(author_id: str) -> dict:
    """
    Fetch last 5 papers for this author.
    Returns their recent topics AND paper evidence links.
    """
    clean_id = author_id.split("/")[-1]

    url = "https://api.openalex.org/works"
    params = {
        "filter":   f"authorships.author.id:{clean_id}",
        "sort":     "publication_date:desc",  # newest first
        "per_page": 5                          # only last 5 papers
    }

    try:
        response = session.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return {"topics": [], "papers": []}

        works = response.json().get("results", [])

        topics  = []
        papers  = []

        for work in works:

            # ── Extract paper title + link ──
            title     = work.get("title", "")
            paper_url = work.get("doi") or work.get("id", "")
            year      = work.get("publication_year", "")

            if title:
                papers.append({
                    "title": title,
                    "year":  year,
                    "url":   f"https://doi.org/{paper_url}"
                            if paper_url.startswith("10.")
                            else paper_url
                })

            # ── Extract topics from THIS paper ──
            for concept in work.get("concepts", [])[:3]:
                name  = concept.get("display_name", "")
                score = concept.get("score", 0)

                # Only take high confidence topics
                if name and score > 0.3:
                    topics.append(name)

        # Remove duplicate topics
        unique_topics = list(dict.fromkeys(topics))

        return {
            "topics": unique_topics[:8],   # top 8 recent topics
            "papers": papers               # last 5 papers as evidence
        }

    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  Paper fetch error: {e}")
        return {"topics": [], "papers": []}

def enrich_author(author: dict) -> dict:

    author_id = author["author_id"].split("/")[-1]

    url = f"https://api.openalex.org/authors/{author_id}"

    try:
        response = session.get(url, timeout=15)

        if response.status_code != 200:
            return author

        data = response.json()

        author["works_count"] = data.get("works_count", 0)

        author["cited_by_count"] = data.get(
            "cited_by_count", 0
        )

        recent = get_recent_paper_topics(author["author_id"])
        author["research_topics"] = recent["topics"]
        author["recent_papers"]   = recent["papers"]

    except requests.exceptions.RequestException:
        pass

    return author



def enrich_all_authors(authors: list) -> list:

    print(f"\nEnriching {len(authors)} authors...")

    enriched = []

    with ThreadPoolExecutor(max_workers=40) as executor:

        future_to_author = {
            executor.submit(
                enrich_author,
                author
            ): author
            for author in authors
        }

        completed = 0

        for future in as_completed(future_to_author):

            completed += 1

            try:
                enriched.append(
                    future.result()
                )

            except Exception as e:
                print("Error:", e)

            if completed % 25 == 0:
                print(
                    f"Completed {completed}/{len(authors)}"
                )

    return enriched