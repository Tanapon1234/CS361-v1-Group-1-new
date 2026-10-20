"""Import the 22 V1 lecturers (build/v1/serving/faculties/*.json) into the lecturer tables.

    cd backend
    uv run python -m scripts.import_v1_lecturers                 # DB from .env
    uv run python -m scripts.import_v1_lecturers --base-url http://localhost:8000

Safe to run again: lecturers are matched by email, and their educations / publication
profiles are only added when the lecturer has none yet. Research interests and expertise
are replaced with the V1 set. V1 profile image URLs are not imported (the API only takes
uploaded files); upload them again from /manage if needed.
"""

import argparse
import json
from pathlib import Path
from typing import Any

import httpx2

from scripts.api import add_target_arguments, call, ensure_master, find_lecturer, open_api

SOURCE = Path(__file__).resolve().parents[2] / "build" / "v1" / "serving" / "faculties"

PROVIDERS = {
    "google_scholar": "Google Scholar",
    "researchgate": "ResearchGate",
    "semantic_scholar": "Semantic Scholar",
    "scopus": "Scopus",
    "orcid": "ORCID",
    "other": "Other",
}


def import_lecturer(api: httpx2.Client, faculty: dict[str, Any]) -> tuple[str, bool]:
    contact = faculty["contact"]
    existing = find_lecturer(api, contact["email"])
    created = existing is None
    if created:
        existing = call(
            api,
            "POST",
            "/lecturers",
            json={
                "name_th": faculty["name"]["th"],
                "name_en": faculty["name"].get("en"),
                "rank": faculty.get("academic_position"),
                "office": contact.get("office"),
                "phone": contact.get("phone"),
                "phone_extension": contact.get("extension"),
                "email": contact["email"],
            },
        )
    lecturer_id = existing["lecturer_id"]
    base = f"/lecturers/{lecturer_id}"

    if call(api, "GET", f"{base}/educations")["meta"]["count"] == 0:
        for education in faculty.get("education", []):
            fields = ("degree", "field", "institution", "country")
            body = {key: education.get(key) for key in fields if education.get(key)}
            if body:
                call(api, "POST", f"{base}/educations", json=body)

    interest_ids = [
        ensure_master(api, "/research-interests", "name", name, "research_interest_id")
        for name in dict.fromkeys(faculty.get("research_interests", []))
    ]
    call(api, "PUT", f"{base}/research-interests", json={"research_interest_ids": interest_ids})

    expertise_ids = [
        ensure_master(api, "/expertise", "description", text, "expertise_id")
        for text in dict.fromkeys(faculty.get("expertise", []))
    ]
    call(api, "PUT", f"{base}/expertise", json={"expertise_ids": expertise_ids})

    if call(api, "GET", f"{base}/publication-profiles")["meta"]["count"] == 0:
        for profile in faculty.get("publication_profiles", []):
            provider = PROVIDERS.get(profile["provider"], profile["provider"])
            call(
                api,
                "POST",
                f"{base}/publication-profiles",
                json={"provider": provider, "url": profile["url"]},
            )

    for publication in faculty.get("selected_publications", []):
        import_publication(api, publication, lecturer_id)

    return lecturer_id, created


def import_publication(api: httpx2.Client, publication: dict[str, Any], lecturer_id: str) -> None:
    """Create it with this lecturer as the author, unless the DOI is already there."""
    doi = publication.get("doi")
    if doi and call(api, "GET", "/publications", params={"q": doi})["meta"]["total"] > 0:
        return
    call(
        api,
        "POST",
        "/publications",
        json={
            "title": publication["title"],
            "publication_year": publication.get("year"),
            "venue": publication.get("venue"),
            "volume": publication.get("volume"),
            "pages": publication.get("pages"),
            "doi": doi,
            "citation_text": publication.get("citation_text"),
            "lecturer_ids": [lecturer_id],
        },
    )


def import_all(api: httpx2.Client) -> int:
    """Import every V1 lecturer; returns how many were new."""
    files = sorted(SOURCE.glob("*.json"))
    if not files:
        raise SystemExit(f"No V1 files in {SOURCE}")

    created = 0
    for path in files:
        faculty = json.loads(path.read_text(encoding="utf-8"))
        _, is_new = import_lecturer(api, faculty)
        created += is_new
        print(f"{'created' if is_new else 'updated'}  {faculty['id']}")
    print(f"Done: {len(files)} lecturers ({created} new)")
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_target_arguments(parser)
    args = parser.parse_args()
    with open_api(args.base_url) as api:
        import_all(api)


if __name__ == "__main__":
    main()
