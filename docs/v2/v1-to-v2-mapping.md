# V1 to V2 Data Mapping

เอกสารนี้เป็น mapping baseline สำหรับ Issue #49 - Define V1 to V2 Data Mapping

เป้าหมายคือกำหนดกติกาให้ทีม data/backend ใช้ทำ demo dataset, migration/import และ V1 compatibility projection โดยไม่ต้องเดาว่า field จาก V1 ต้องลง V2 table/column ไหน

เอกสารนี้เป็น design/mapping เท่านั้น ยังไม่รัน migration จริง และยังไม่ insert ข้อมูลเข้า Aurora

---

## Input Sources

ใช้ไฟล์ต่อไปนี้เป็นฐาน:

| Source | Purpose |
|---|---|
| `data/v1/source/faculty_profiles.json` | source snapshot จาก public faculty website |
| `data/v1/source/source-metadata.json` | metadata ของ source snapshot |
| `build/v1/serving/faculties.json` | V1 public list contract |
| `build/v1/serving/faculties/{id}.json` | V1 public detail contract |
| `build/v1/metadata/manifest.json` | serving build manifest |
| `build/v1/metadata/preparation-summary.json` | preparation evidence |
| `fixtures/v1/` | compatibility fixtures |

Observed V1 dataset summary:

| Item | Count |
|---|---:|
| Faculty records | 22 |
| Education entries | 65 |
| Research interest entries | 78 |
| Expertise entries | 17 |
| Selected publications | 7 |
| External publication profile links | 31 |
| CV links | 10 |
| Badges | 1 |

---

## Scope Boundary

This mapping covers V1 public faculty data only. It does not map the workload form PDF into V2.

In scope for Issue #49:

- public faculty profile data from V1
- education entries from V1 profile detail
- research interests and expertise from V1 profile detail
- selected publications from V1 profile detail
- external academic profile links from V1 profile detail
- V1 source/provenance metadata needed for migration traceability

Out of scope for Issue #49:

- official workload form scoring
- teaching workload rows from PDF forms
- supervision/advising workload rows from PDF forms
- service workload rows from PDF forms
- multi-year demo workload generation
- actual database migration execution

Those items are handled by later migration/demo dataset cards after this mapping is frozen.

---

## V1 Field Inventory

The mapping was checked against both V1 list and V1 detail serving shapes.

### V1 Faculty List Contract

Source: `build/v1/serving/faculties.json`

| V1 field | Meaning | V2 handling |
|---|---|---|
| `id` | public faculty slug used by V1 routes | preserve as `faculty.public_slug` |
| `name.th` | Thai display name | `faculty.name_th` |
| `name.en` | English display name | `faculty.name_en` |
| `academic_position` | public academic position | `faculty.academic_position` |
| `profile_image.url` | public profile image URL | `faculty.profile_image_url` |
| `profile_image.alt` | image alt/display text | `faculty.profile_image_alt` |
| `research_interests[]` | public research interests shown in list/card views | `faculty_interest` with `interest_type = RESEARCH_INTEREST` |
| `expertise[]` | public expertise keywords shown in list/card views | `faculty_interest` with `interest_type = EXPERTISE` |

### V1 Faculty Detail Contract

Source: `build/v1/serving/faculties/{id}.json`

| V1 field | Meaning | V2 handling |
|---|---|---|
| `id` | public faculty slug | `faculty.public_slug` |
| `name.th` / `name.en` | display names | `faculty.name_th` / `faculty.name_en` |
| `academic_position` | public rank/title | `faculty.academic_position` |
| `profile_image.url` / `profile_image.alt` | public image fields | `faculty.profile_image_url` / `faculty.profile_image_alt` |
| `contact.office` | public office location | `faculty.office_public` |
| `contact.phone` / `contact.extension` | public phone and extension | combined into `faculty.phone_public`; raw extension preserved |
| `contact.email` | public email | `faculty.email_public` |
| `education[]` | education history | one row per item in `faculty_education` |
| `research_interests[]` | research interests | one row per item in `faculty_interest` |
| `expertise[]` | expertise keywords | one row per item in `faculty_interest` |
| `selected_publications[]` | public selected publications | `work_item`, `publication_detail`, `faculty_work_item` |
| `publication_profiles[]` | external academic profile links | preserve in `source_record.raw_record`; schema gap for normalized table |
| `cv` | CV link/object when present | preserve in `source_record.raw_record`; schema gap for normalized faculty document |
| `badges[]` | public badge/profile labels when present | preserve in `source_record.raw_record`; schema gap for normalized badge table |

### V1 Source Metadata Contract

Source: `data/v1/source/source-metadata.json`

| V1 field | Meaning | V2 handling |
|---|---|---|
| `source` | human-readable source label | normalize stable code into `import_batch.source_system` |
| `provider` / `domain` | source ownership/context | preserve in `source_record.raw_record` and import notes |
| `directory_url` | directory page used for collection | preserve in provenance raw record |
| `captured_at` | capture timestamp | preserve in provenance raw record |
| `record_count` | expected faculty count | `import_batch.record_count` |
| `source_version` | snapshot version | `import_batch.source_version` |
| `capture_method` | collection method/evidence note | `import_batch.source_name` or import notes |

---

## Target V2 Tables

V1 data maps into these V2 schema areas:

| V1 concept | V2 target |
|---|---|
| Faculty identity/profile | `faculty` |
| Education | `faculty_education` |
| Research interests | `faculty_interest` with `interest_type = RESEARCH_INTEREST` |
| Expertise | `faculty_interest` with `interest_type = EXPERTISE` |
| Selected publications | `work_item`, `publication_detail`, `faculty_work_item` |
| Source snapshot and per-record provenance | `import_batch`, `source_record` |
| External publication profiles | preserve in `source_record.raw_record`; schema gap for normalized faculty-level links |
| CV/badges | preserve in `source_record.raw_record`; schema gap for normalized faculty-level assets |

Full field mapping table:

- `data/v2/mappings/v1-to-v2-field-mapping.csv`

---

## Core Rules

### Preserve V1 Public Slug

V1 `id` is the public URL slug and must be preserved exactly:

```text
V1 build/v1/serving/faculties/{id}.json:id
→ V2 faculty.public_slug
```

Rules:

- Do not generate a new slug.
- Do not transliterate or rewrite the slug.
- If duplicate V1 ids exist, fail/hold migration.
- If id does not match the expected slug pattern `^[a-z0-9]+(-[a-z0-9]+)*$`, mark mapping error.
- V2 internal `faculty.id` should be deterministic, for example `fac_{public_slug}`.

Example:

```text
V1 id: kasidit-chanchio
V2 faculty.public_slug: kasidit-chanchio
V2 faculty.id: fac_kasidit-chanchio
```

### Default Visibility

V1 serving data is already public-safe. Data migrated from V1 public serving files defaults to:

```text
visibility = PUBLIC
status = ACTIVE
```

Do not create `INTERNAL` or `RESTRICTED` records from V1 public data unless a future source explicitly marks a field that way.

### Missing Values

General rules:

- Empty string should become `null` unless the target column is required.
- Optional missing arrays become no rows, not empty placeholder rows.
- Required missing values fail the record or hold it for manual review.
- Invalid email/URL/year values should not be silently corrected; record a warning/error in import evidence.
- Preserve original raw values in `source_record.raw_record` even when normalized target fields are null.

### Source Traceability

Every migrated faculty and child record should be traceable back to V1:

```text
import_batch.source_system = V1_PUBLIC_FACULTY
source_record.source_record_key = logical V1 key
source_record.raw_record = original V1 JSON object or child item
```

Recommended source record keys:

```text
faculty/{public_slug}
faculty/{public_slug}/education/{index}
faculty/{public_slug}/research_interests/{index}
faculty/{public_slug}/expertise/{index}
faculty/{public_slug}/selected_publications/{dedupe_key}
faculty/{public_slug}/publication_profiles/{provider}/{index}
```

---

## Faculty Mapping

Target table: `faculty`

| V1 field | V2 column | Rule |
|---|---|---|
| `id` | `public_slug` | preserve as-is |
| `id` | `id` | deterministic internal id, for example `fac_{id}` |
| `name.th` | `name_th` | trim, keep original Thai text |
| `name.en` | `name_en` | trim, keep original English text |
| `academic_position` | `academic_position` | trim |
| `contact.office` | `office_public` | optional public value |
| `contact.phone` + `contact.extension` | `phone_public` | combine when extension exists, e.g. `0-2986-9156 ext. 200` |
| `contact.email` | `email_public` | validate email shape |
| `profile_image.url` | `profile_image_url` | validate URL shape |
| `profile_image.alt` | `profile_image_alt` | use V1 alt; if missing, use display name as fallback warning |

Required:

- `public_slug`
- at least one of `name_th` or `name_en`

Optional:

- `academic_position`
- contact fields
- profile image fields

---

## Education Mapping

Target table: `faculty_education`

Each V1 `education[]` item becomes one row.

| V1 field | V2 column | Rule |
|---|---|---|
| parent `id` | `faculty_id` | resolve through `faculty.public_slug` |
| `education[].degree` | `degree` | trim |
| `education[].field` | `field_of_study` | trim |
| `education[].institution` | `institution` | trim |
| `education[].country` | `country` | trim |
| `education[].graduation_year` | `graduation_year` | parse integer if numeric |
| array order | `display_order` | preserve V1 order, 1-based recommended |

Year rule:

- Preserve the numeric source year as given.
- Do not convert Buddhist Era to Gregorian automatically in this card.
- If a future report needs CE/BE normalization, open a separate decision because current source mixes Thai context but does not explicitly label year system per entry.

---

## Research Interests / Expertise Mapping

Target table: `faculty_interest`

| V1 field | V2 column | Rule |
|---|---|---|
| parent `id` | `faculty_id` | resolve through `faculty.public_slug` |
| `research_interests[]` | `interest_type` | constant `RESEARCH_INTEREST` |
| `research_interests[]` | `value` | trim text |
| `expertise[]` | `interest_type` | constant `EXPERTISE` |
| `expertise[]` | `value` | trim text |
| source order | source/projection order | preserve order in source/projection; schema has no display_order column |

Deduplication:

- Deduplicate exact/casefold duplicates per faculty and interest type.
- Preserve original spelling/case from the first occurrence.
- Do not merge research interest and expertise even when text matches; they are different types.

Schema note:

- `faculty_interest` currently has no `display_order`. If display order becomes important for V2 UI, add a schema follow-up.

---

## Selected Publications Mapping

V1 `selected_publications[]` becomes:

```text
work_item
publication_detail
faculty_work_item
source_record
```

### work_item

| V1 field | V2 column | Rule |
|---|---|---|
| publication `title` | `work_item.title` | required |
| publication `citation_text` | `work_item.description` | preserve citation text for display/traceability |
| constant | `category_code` | `RESEARCH` |
| constant | `work_type_code` | `PUBLICATION` |
| constant | `visibility` | `PUBLIC` |
| constant | `status` | `ACTIVE` |
| source section | `source_section_code` | `selected_publications` |
| publication source record | `source_record_id` | child `source_record` for this publication |

### publication_detail

| V1 field | V2 column | Rule |
|---|---|---|
| `title` | `publication_title` | required |
| `venue` | `venue` | optional |
| `year` | `publication_year` | integer, must be 1900-3000 if present |
| `doi` | `doi` | normalize trim/lowercase for duplicate check; preserve display value if desired |
| `url` if present in future | `external_url` | validate URL |

### faculty_work_item

| V1 field | V2 column | Rule |
|---|---|---|
| parent `id` | `faculty_id` | resolve through `faculty.public_slug` |
| generated publication work id | `work_item_id` | link to publication work item |
| listed on faculty profile | `role` | `AUTHOR` |
| unavailable in V1 | `contribution_percent` | null |
| unavailable in V1 | `contribution_order` | null unless future parser extracts author order |
| source note | `contribution_note` | `Listed in V1 selected_publications; author order not normalized` |

Duplicate rule:

1. If DOI exists, use `lower(trim(doi))` as primary duplicate key.
2. If DOI is missing, use normalized `title + publication_year`.
3. If duplicate publication appears under multiple faculty profiles, create one `work_item` and multiple `faculty_work_item` rows.

Schema gaps for publications:

- V1 has `volume`, `pages`, and `citation_text`.
- Current `publication_detail` has no `volume`, `pages`, or `citation_text` columns.
- Mapping stores `citation_text` in `work_item.description`.
- `volume` and `pages` must be preserved in `source_record.raw_record`.
- If normalized volume/pages are required later, add columns or an extension table before #66.

---

## External Publication Profiles

V1 `publication_profiles[]` contains provider links such as:

```text
google_scholar
researchgate
semantic_scholar
other
```

Current V2 schema does not have a faculty-level external profile table. `evidence_reference` is not appropriate because `work_item_id` is required.

Mapping decision for V2 baseline:

```text
publication_profiles[] -> source_record.raw_record
```

Rules:

- Preserve provider and URL exactly in child `source_record` rows.
- Validate provider is present.
- Validate URL shape when present.
- Do not map publication profiles into `evidence_reference` until schema supports faculty-level references or nullable/non-work evidence.

Compatibility note:

- If V1 public projection must continue showing these links before schema is extended, projection can copy them from the faculty source records.

Open schema decision:

- Add `faculty_external_profile` or generalized `profile_link` table if V2 needs searchable/admin-editable external profiles.

---

## Profile Image / CV / Badges

### Profile Image

Profile image is directly supported:

```text
profile_image.url -> faculty.profile_image_url
profile_image.alt -> faculty.profile_image_alt
```

### CV

V1 detail records may include `cv`.

Current V2 schema has no faculty-level document/reference table. `evidence_reference` requires `work_item_id`, so CV should not be forced into it.

Mapping decision:

```text
cv -> source_record.raw_record
```

If future V2 UI needs CV display/editing, add `faculty_document` or `faculty_external_profile` style schema before normalizing CV.

### Badges

V1 `badges[]` is sparse and not represented by a normalized V2 table.

Mapping decision:

```text
badges -> source_record.raw_record
```

Do not drop badges. Treat normalized badge support as deferred.

---

## Import Batch / Source Record Mapping

### import_batch

| V1 source | V2 column | Rule |
|---|---|---|
| constant | `source_system` | `V1_PUBLIC_FACULTY` |
| source file | `source_name` | `build/v1/serving/faculties/{id}.json` or `data/v1/source/faculty_profiles.json` |
| `source-metadata.source_version` | `source_version` | preserve |
| source type | `source_type` | `JSON` |
| source file hash | `source_hash` | compute SHA-256 during migration/import |
| source count | `record_count` | expected `22` faculty detail records for current V1 serving snapshot |

### source_record

Recommended child records:

- one source record per faculty detail
- one source record per education item
- one source record per interest item
- one source record per expertise item
- one source record per selected publication
- one source record per external publication profile

This makes import idempotency and error reporting easier than using only one raw blob per faculty.

---

## Validation Rules

| Rule | Severity | Expected outcome |
|---|---|---|
| duplicate V1 `id` | error | stop/hold migration |
| missing V1 `id` in serving detail | error | skip record and report |
| invalid slug format | error | skip record and report |
| missing both `name.th` and `name.en` | error | skip faculty record |
| invalid email | warning/error | keep raw value in source_record; set normalized email null unless policy says fail |
| invalid URL | warning/error | keep raw value in source_record; set normalized URL null |
| non-numeric graduation year | warning | set `graduation_year = null`, preserve raw |
| publication missing title | error | skip publication child record |
| publication year outside 1900-3000 | warning/error | set null or hold publication depending severity policy |
| DOI duplicate | warning/info | merge publication work item and create additional faculty link |

---

## V1 Compatibility Test Cases

Required compatibility checks before #66 is accepted:

1. Faculty count after migration equals V1 serving faculty count: currently `22`.
2. Every V1 `id` exists as `faculty.public_slug`.
3. Every V1 detail route slug can look up exactly one V2 faculty.
4. V1 list fields can be projected from V2 without missing `id`, `name`, `academic_position`, `profile_image`, `research_interests`, or `expertise`.
5. V1 detail profile fields can be projected from V2 or preserved source data without losing contact, education, publication_profiles, selected_publications, CV, or badges.
6. Education count per faculty matches V1 detail.
7. Research interest count per faculty matches V1 detail after exact duplicate removal.
8. Expertise count per faculty matches V1 detail after exact duplicate removal.
9. Selected publication count per faculty matches V1 detail.
10. Publications with the same DOI are represented by one `work_item` and multiple faculty links.
11. All migrated V1 public records have `visibility = PUBLIC`.
12. No V1 public data is accidentally written as `INTERNAL` or `RESTRICTED`.
13. Invalid optional fields are reported in import warnings/errors and preserved in `source_record.raw_record`.

---

## Open Questions / Field Gaps

| Topic | Gap | Decision needed | Suggested owner |
|---|---|---|---|
| External faculty profiles | No normalized faculty-level external profile table | Add `faculty_external_profile` / `profile_link`, or keep only in source/projection for V2 | Tech Lead + Database |
| CV links | No faculty-level document/reference table | Add `faculty_document`, reuse future profile link model, or defer normalized CV support | Tech Lead |
| Badges | No badge/profile label table | Decide whether badges matter for V2 admin/search or only V1 projection | Frontend + Tech Lead |
| Publication volume/pages | `publication_detail` lacks `volume` and `pages` | Add columns if normalized search/display is required | Database |
| Publication citation text | no dedicated `citation_text` column | Current mapping uses `work_item.description`; add column if needed | Backend + Database |
| Interest display order | `faculty_interest` lacks `display_order` | Add column if V2 UI must preserve exact V1 order from DB | Frontend + Database |
| Education year system | graduation years include Thai-context values like `2543` | Preserve source integer for now; decide BE/CE normalization later | Data |

---

## Definition Of Done For #49

This mapping is ready for #50 and #66 when:

- field mapping CSV exists and is linked
- V1 `id -> faculty.public_slug` rule is frozen
- selected publication mapping and duplicate rules are frozen
- source/provenance mapping is frozen
- schema gaps are explicit and not hidden as silent data loss
- compatibility tests above are used as acceptance checks for the actual migration
