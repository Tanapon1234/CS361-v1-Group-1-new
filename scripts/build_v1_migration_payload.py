#!/usr/bin/env python3
"""Transform V1 public faculty data (all 22 records) into V2 Aurora row payloads.

Reads local files that are exact mirrors of the private S3 data bucket
(``cs361-v1-faculty-data-g1-...``):

  data/v1/source/faculty_profiles.json   <-> s3://.../source/current/faculty_profiles.json
  data/v1/source/source-metadata.json    <-> s3://.../source/current/source-metadata.json
  build/v1/serving/faculties/{id}.json   <-> s3://.../serving/faculties/{id}.json

Mapping rules follow docs/v2/v1-to-v2-mapping.md (frozen for Issue #49).

Output: one JSON file per V2 table under build/v2/migration/, each a list of
row dicts in insert order. A separate loader script (run_v1_migration_to_aurora.sh)
sends these to Aurora via RDS Data API. This script makes no AWS calls.

Usage:
  python3 scripts/build_v1_migration_payload.py
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_METADATA_FILE = ROOT / "data" / "v1" / "source" / "source-metadata.json"
SERVING_LIST_FILE = ROOT / "build" / "v1" / "serving" / "faculties.json"
SERVING_DETAIL_DIR = ROOT / "build" / "v1" / "serving" / "faculties"
MANIFEST_FILE = ROOT / "build" / "v1" / "metadata" / "manifest.json"
OUT_DIR = ROOT / "build" / "v2" / "migration"
# Optional: {lower(doi): existing_work_item_id} for publications that already
# exist in Aurora under a different id (e.g. from the demo dataset seeded by
# Issue #80) so this migration links to them instead of creating duplicates.
EXISTING_DOI_MAP_FILE = OUT_DIR / "_existing_doi_work_items.json"
# Optional: [{"faculty_id": ..., "work_item_id": ...}] pairs already linked in
# Aurora (any role) so this migration does not add a second faculty_work_item
# row for the same real-world authorship relationship.
EXISTING_FWI_PAIRS_FILE = OUT_DIR / "_existing_faculty_work_item_pairs.json"

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: str, length: int = 16) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    return value


def parse_year(value):
    v = clean(value)
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


def combine_phone(phone, extension):
    phone = clean(phone)
    extension = clean(extension)
    if not phone:
        return None
    if extension:
        return f"{phone} ext. {extension}"
    return phone


def dedupe_key_interest(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def dedupe_key_publication(pub: dict) -> str:
    doi = clean(pub.get("doi"))
    if doi:
        return "doi:" + doi.strip().lower()
    title = re.sub(r"\s+", " ", (pub.get("title") or "").strip()).casefold()
    year = pub.get("year") or ""
    return f"title:{title}|year:{year}"


def main() -> None:
    source_metadata = load_json(SOURCE_METADATA_FILE)
    manifest = load_json(MANIFEST_FILE) if MANIFEST_FILE.exists() else {}
    detail_files = sorted(SERVING_DETAIL_DIR.glob("*.json"))
    faculty_profiles = [load_json(p) for p in detail_files]
    existing_doi_work_items = load_json(EXISTING_DOI_MAP_FILE) if EXISTING_DOI_MAP_FILE.exists() else {}
    existing_fwi_pairs = set()
    if EXISTING_FWI_PAIRS_FILE.exists():
        for pair in load_json(EXISTING_FWI_PAIRS_FILE):
            existing_fwi_pairs.add((pair["faculty_id"], pair["work_item_id"]))

    now = datetime.now(timezone.utc).isoformat()

    faculty_rows = []
    education_rows = []
    interest_rows = []
    work_item_rows = []
    publication_detail_rows = []
    faculty_work_item_rows = []
    source_record_rows = []

    seen_slugs = set()
    # dedupe_key -> work_item_id, pre-seeded with publications that already
    # exist in Aurora (from the demo dataset) keyed by "doi:<lower(doi)>"
    seen_publications: dict[str, str] = {
        f"doi:{doi.strip().lower()}": work_item_id
        for doi, work_item_id in existing_doi_work_items.items()
    }
    pre_existing_work_items = set(seen_publications.values())
    errors = []
    warnings = []

    combined_serving_text = "".join(p.read_text(encoding="utf-8") for p in detail_files)
    import_batch_id = "imp_v1_public_faculty_full"
    import_batch_source_hash = "sha256:" + sha256_hex(combined_serving_text)

    for faculty in faculty_profiles:
        slug = clean(faculty.get("id"))
        if not slug:
            errors.append({"error": "missing_id", "record": faculty})
            continue
        if not SLUG_RE.match(slug):
            errors.append({"error": "invalid_slug", "id": slug})
            continue
        if slug in seen_slugs:
            errors.append({"error": "duplicate_slug", "id": slug})
            continue
        seen_slugs.add(slug)

        name = faculty.get("name") or {}
        name_th = clean(name.get("th"))
        name_en = clean(name.get("en"))
        if not name_th and not name_en:
            errors.append({"error": "missing_name", "id": slug})
            continue

        contact = faculty.get("contact") or {}
        profile_image = faculty.get("profile_image") or {}
        faculty_id = f"fac_{slug}"

        faculty_rows.append({
            "id": faculty_id,
            "public_slug": slug,
            "name_th": name_th,
            "name_en": name_en,
            "academic_position": clean(faculty.get("academic_position")),
            "department": None,
            "office_public": clean(contact.get("office")),
            "phone_public": combine_phone(contact.get("phone"), contact.get("extension")),
            "email_public": clean(contact.get("email")),
            "profile_image_url": clean(profile_image.get("url")),
            "profile_image_alt": clean(profile_image.get("alt")) or name_th or name_en,
            "visibility": "PUBLIC",
            "status": "ACTIVE",
        })

        source_record_rows.append({
            "id": stable_id("src", "faculty", slug),
            "import_batch_id": import_batch_id,
            "source_system": "V1_PUBLIC_FACULTY",
            "source_record_key": f"faculty/{slug}",
            "source_section_code": "faculty_profile",
            "source_hash": "sha256:" + sha256_hex(json.dumps(faculty, sort_keys=True, ensure_ascii=False)),
            "row_number": None,
            "raw_record": faculty,
            "target_entity_type": "faculty",
            "target_entity_id": faculty_id,
            "status": "IMPORTED",
            "error_message": None,
        })

        for idx, edu in enumerate(faculty.get("education") or [], start=1):
            education_rows.append({
                "id": stable_id("edu", slug, str(idx)),
                "faculty_id": faculty_id,
                "degree": clean(edu.get("degree")),
                "field_of_study": clean(edu.get("field")),
                "institution": clean(edu.get("institution")),
                "country": clean(edu.get("country")),
                "graduation_year": parse_year(edu.get("graduation_year")),
                "display_order": idx,
            })
            source_record_rows.append({
                "id": stable_id("src", "faculty", slug, "education", str(idx)),
                "import_batch_id": import_batch_id,
                "source_system": "V1_PUBLIC_FACULTY",
                "source_record_key": f"faculty/{slug}/education/{idx}",
                "source_section_code": "education",
                "source_hash": "sha256:" + sha256_hex(json.dumps(edu, sort_keys=True, ensure_ascii=False)),
                "row_number": idx,
                "raw_record": edu,
                "target_entity_type": "faculty_education",
                "target_entity_id": stable_id("edu", slug, str(idx)),
                "status": "IMPORTED",
                "error_message": None,
            })

        def add_interests(items, interest_type, section):
            seen_local = {}
            order = 0
            for raw_value in items or []:
                v = clean(raw_value)
                if not v:
                    continue
                key = dedupe_key_interest(v)
                if key in seen_local:
                    continue
                seen_local[key] = v
                order += 1
                interest_rows.append({
                    "id": stable_id("int", slug, interest_type.lower(), str(order)),
                    "faculty_id": faculty_id,
                    "interest_type": interest_type,
                    "value": v,
                    "visibility": "PUBLIC",
                })
                source_record_rows.append({
                    "id": stable_id("src", "faculty", slug, section, str(order)),
                    "import_batch_id": import_batch_id,
                    "source_system": "V1_PUBLIC_FACULTY",
                    "source_record_key": f"faculty/{slug}/{section}/{order}",
                    "source_section_code": section,
                    "source_hash": "sha256:" + sha256_hex(v),
                    "row_number": order,
                    "raw_record": {"value": v},
                    "target_entity_type": "faculty_interest",
                    "target_entity_id": stable_id("int", slug, interest_type.lower(), str(order)),
                    "status": "IMPORTED",
                    "error_message": None,
                })

        add_interests(faculty.get("research_interests"), "RESEARCH_INTEREST", "research_interests")
        add_interests(faculty.get("expertise"), "EXPERTISE", "expertise")

        for idx, pub in enumerate(faculty.get("selected_publications") or [], start=1):
            title = clean(pub.get("title"))
            if not title:
                errors.append({"error": "publication_missing_title", "faculty": slug, "index": idx})
                continue
            year = pub.get("year")
            pub_year = year if isinstance(year, int) and 1900 <= year <= 3000 else None
            if year is not None and pub_year is None:
                warnings.append({"warning": "publication_year_out_of_range", "faculty": slug, "title": title})

            dkey = dedupe_key_publication(pub)
            if dkey in seen_publications:
                work_item_id = seen_publications[dkey]
                if work_item_id in pre_existing_work_items:
                    warnings.append({
                        "warning": "publication_linked_to_pre_existing_work_item",
                        "faculty": slug,
                        "title": title,
                        "work_item_id": work_item_id,
                    })
                    source_record_rows.append({
                        "id": stable_id("src", "publication", "link", slug, dkey),
                        "import_batch_id": import_batch_id,
                        "source_system": "V1_PUBLIC_FACULTY",
                        "source_record_key": f"faculty/{slug}/selected_publications/{dkey}",
                        "source_section_code": "selected_publications",
                        "source_hash": "sha256:" + sha256_hex(json.dumps(pub, sort_keys=True, ensure_ascii=False)),
                        "row_number": idx,
                        "raw_record": pub,
                        "target_entity_type": "work_item",
                        "target_entity_id": work_item_id,
                        "status": "IMPORTED",
                        "error_message": None,
                    })
            else:
                work_item_id = stable_id("wi_pub", dkey)
                seen_publications[dkey] = work_item_id

                work_item_rows.append({
                    "id": work_item_id,
                    "category_code": "RESEARCH",
                    "work_type_code": "PUBLICATION",
                    "title": title,
                    "description": clean(pub.get("citation_text")),
                    "start_date": None,
                    "end_date": None,
                    "visibility": "PUBLIC",
                    "status": "ACTIVE",
                    "source_score": None,
                    "source_weight": None,
                    "source_section_code": "selected_publications",
                    "import_batch_id": import_batch_id,
                    "source_record_id": stable_id("src", "publication", dkey),
                    "created_by": "SYSTEM",
                    "updated_by": "SYSTEM",
                })

                doi = clean(pub.get("doi"))
                publication_detail_rows.append({
                    "work_item_id": work_item_id,
                    "publication_title": title,
                    "venue": clean(pub.get("venue")),
                    "publisher": None,
                    "publication_year": pub_year,
                    "publication_date": None,
                    "doi": doi,
                    "isbn": None,
                    "issn": None,
                    "quartile": None,
                    "indexing_database": None,
                    "publication_kind": "journal_article",
                    "external_url": f"https://doi.org/{doi}" if doi else None,
                })

                source_record_rows.append({
                    "id": stable_id("src", "publication", dkey),
                    "import_batch_id": import_batch_id,
                    "source_system": "V1_PUBLIC_FACULTY",
                    "source_record_key": f"publication/{dkey}",
                    "source_section_code": "selected_publications",
                    "source_hash": "sha256:" + sha256_hex(json.dumps(pub, sort_keys=True, ensure_ascii=False)),
                    "row_number": idx,
                    "raw_record": pub,
                    "target_entity_type": "work_item",
                    "target_entity_id": work_item_id,
                    "status": "IMPORTED",
                    "error_message": None,
                })

            if (faculty_id, work_item_id) in existing_fwi_pairs:
                warnings.append({
                    "warning": "faculty_work_item_link_already_exists",
                    "faculty": slug,
                    "work_item_id": work_item_id,
                })
                continue

            faculty_work_item_rows.append({
                "id": stable_id("fwi", faculty_id, work_item_id, "author"),
                "faculty_id": faculty_id,
                "work_item_id": work_item_id,
                "academic_period_id": None,
                "evaluation_period_id": None,
                "role": "author",
                "contribution_order": None,
                "contribution_percent": None,
                "contribution_note": "Listed in V1 selected_publications; author order not normalized",
                "quantity": 1.00,
                "credits": None,
                "hours": None,
                "source_section_code": "selected_publications",
            })

        for idx, profile in enumerate(faculty.get("publication_profiles") or [], start=1):
            source_record_rows.append({
                "id": stable_id("src", "faculty", slug, "publication_profiles", str(idx)),
                "import_batch_id": import_batch_id,
                "source_system": "V1_PUBLIC_FACULTY",
                "source_record_key": f"faculty/{slug}/publication_profiles/{profile.get('provider', 'unknown')}/{idx}",
                "source_section_code": "publication_profiles",
                "source_hash": "sha256:" + sha256_hex(json.dumps(profile, sort_keys=True, ensure_ascii=False)),
                "row_number": idx,
                "raw_record": profile,
                "target_entity_type": "faculty",
                "target_entity_id": faculty_id,
                "status": "IMPORTED",
                "error_message": None,
            })

        if faculty.get("cv"):
            source_record_rows.append({
                "id": stable_id("src", "faculty", slug, "cv"),
                "import_batch_id": import_batch_id,
                "source_system": "V1_PUBLIC_FACULTY",
                "source_record_key": f"faculty/{slug}/cv",
                "source_section_code": "cv",
                "source_hash": "sha256:" + sha256_hex(json.dumps(faculty["cv"], sort_keys=True, ensure_ascii=False)),
                "row_number": None,
                "raw_record": faculty["cv"],
                "target_entity_type": "faculty",
                "target_entity_id": faculty_id,
                "status": "IMPORTED",
                "error_message": None,
            })

        if faculty.get("badges"):
            source_record_rows.append({
                "id": stable_id("src", "faculty", slug, "badges"),
                "import_batch_id": import_batch_id,
                "source_system": "V1_PUBLIC_FACULTY",
                "source_record_key": f"faculty/{slug}/badges",
                "source_section_code": "badges",
                "source_hash": "sha256:" + sha256_hex(json.dumps(faculty["badges"], sort_keys=True, ensure_ascii=False)),
                "row_number": None,
                "raw_record": faculty["badges"],
                "target_entity_type": "faculty",
                "target_entity_id": faculty_id,
                "status": "IMPORTED",
                "error_message": None,
            })

    import_batch_row = {
        "id": import_batch_id,
        "source_system": "V1_PUBLIC_FACULTY",
        "source_name": "build/v1/serving/faculties/{id}.json",
        "source_version": clean(source_metadata.get("source_version")) or clean(manifest.get("source_version")),
        "source_type": "JSON",
        "source_s3_key": "serving/faculties",
        "source_hash": import_batch_source_hash,
        "status": "SUCCEEDED" if not errors else "WARNING",
        "record_count": len(faculty_profiles),
        "valid_count": len(faculty_rows),
        "warning_count": len(warnings),
        "error_count": len(errors),
        "started_at": now,
        "completed_at": now,
        "created_by": "SYSTEM",
    }

    tables = {
        "import_batch": [import_batch_row],
        "faculty": faculty_rows,
        "faculty_education": education_rows,
        "faculty_interest": interest_rows,
        "work_item": work_item_rows,
        "publication_detail": publication_detail_rows,
        "faculty_work_item": faculty_work_item_rows,
        "source_record": source_record_rows,
    }

    for name, rows in tables.items():
        write_json(OUT_DIR / f"{name}.json", rows)

    summary = {
        "generated_at": now,
        "input_faculty_count": len(faculty_profiles),
        "counts": {name: len(rows) for name, rows in tables.items()},
        "errors": errors,
        "warnings": warnings,
    }
    write_json(OUT_DIR / "_summary.json", summary)

    print(f"Wrote payload to {OUT_DIR}")
    for name, rows in tables.items():
        print(f"  {name}: {len(rows)} rows")
    if errors:
        print(f"ERRORS: {len(errors)} (see _summary.json)")
    if warnings:
        print(f"WARNINGS: {len(warnings)} (see _summary.json)")


if __name__ == "__main__":
    main()
