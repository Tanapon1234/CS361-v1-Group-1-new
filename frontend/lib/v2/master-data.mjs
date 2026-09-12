import fs from 'node:fs';
import path from 'node:path';

const FIXTURE_FILES = {
  academicPeriods: 'academic-periods.json',
  evaluationPeriods: 'evaluation-periods.json',
  workCategories: 'work-categories.json',
  workTypes: 'work-types.json',
  faculties: 'faculties.json',
};

const VALID_SEMESTERS = new Set(['1', '2', '3', 'SUMMER', 'OTHER']);
const SEMESTER_ORDER = new Map([
  ['3', 5],
  ['2', 4],
  ['1', 3],
  ['SUMMER', 2],
  ['OTHER', 1],
]);

const PUBLIC_VISIBILITY = 'PUBLIC';
const ACTIVE_STATUS = 'ACTIVE';

export class MasterDataQueryError extends Error {
  constructor(field, message) {
    super(message);
    this.name = 'MasterDataQueryError';
    this.code = 'INVALID_QUERY';
    this.status = 400;
    this.details = { field };
  }
}

function getFixtureDirectory() {
  if (process.env.V2_MASTER_DATA_FIXTURE_DIR) {
    return path.resolve(process.env.V2_MASTER_DATA_FIXTURE_DIR);
  }

  const candidates = [
    path.resolve(process.cwd(), 'data', 'v2', 'fixtures'),
    path.resolve(process.cwd(), '..', 'data', 'v2', 'fixtures'),
  ];

  const fixtureDirectory = candidates.find((candidate) => fs.existsSync(candidate));
  return fixtureDirectory ?? candidates[1];
}

function readFixture(fileName) {
  const filePath = path.join(getFixtureDirectory(), fileName);
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

export function loadFixtureRepository() {
  return {
    academicPeriods: readFixture(FIXTURE_FILES.academicPeriods),
    evaluationPeriods: readFixture(FIXTURE_FILES.evaluationPeriods),
    workCategories: readFixture(FIXTURE_FILES.workCategories),
    workTypes: readFixture(FIXTURE_FILES.workTypes),
    faculties: readFixture(FIXTURE_FILES.faculties),
  };
}

function asSearchParams(searchParams) {
  if (searchParams instanceof URLSearchParams) return searchParams;
  return new URLSearchParams(searchParams ?? '');
}

function optionalParam(searchParams, key) {
  const value = asSearchParams(searchParams).get(key);
  const normalized = value?.trim();
  return normalized ? normalized : undefined;
}

function makeEnvelope(items) {
  return {
    items,
    meta: {
      count: items.length,
    },
  };
}

function parseAcademicYear(searchParams) {
  const year = optionalParam(searchParams, 'year');
  if (!year) return undefined;
  if (!/^\d{4}$/.test(year)) {
    throw new MasterDataQueryError('year', 'year must be a 4-digit academic year');
  }
  return Number(year);
}

function parseSemester(searchParams) {
  const semester = optionalParam(searchParams, 'semester');
  if (!semester) return undefined;
  if (!VALID_SEMESTERS.has(semester)) {
    throw new MasterDataQueryError('semester', 'semester must be one of 1, 2, 3, SUMMER, OTHER');
  }
  return semester;
}

function parseActive(searchParams) {
  const active = optionalParam(searchParams, 'active');
  if (active === undefined) return true;
  if (active === 'true') return true;
  if (active === 'false') return false;
  throw new MasterDataQueryError('active', 'active must be true or false');
}

function parsePublicStatus(searchParams) {
  const status = optionalParam(searchParams, 'status') ?? ACTIVE_STATUS;
  if (status !== ACTIVE_STATUS) {
    throw new MasterDataQueryError('status', 'status must be ACTIVE for public master data endpoints');
  }
  return status;
}

function parsePublicVisibility(searchParams) {
  const visibility = optionalParam(searchParams, 'visibility') ?? PUBLIC_VISIBILITY;
  if (visibility !== PUBLIC_VISIBILITY) {
    throw new MasterDataQueryError(
      'visibility',
      'visibility must be PUBLIC for public master data endpoints'
    );
  }
  return visibility;
}

export function mapAcademicPeriod(row) {
  return {
    id: row.id,
    academic_year: row.academic_year,
    semester: row.semester,
    label: row.label,
    start_date: row.start_date ?? null,
    end_date: row.end_date ?? null,
  };
}

export function mapEvaluationPeriod(row) {
  return {
    id: row.id,
    code: row.code,
    label: row.label,
    start_date: row.start_date,
    end_date: row.end_date,
    academic_period_id: row.academic_period_id ?? null,
  };
}

export function mapWorkCategory(row) {
  return {
    code: row.code,
    label_th: row.label_th,
    label_en: row.label_en,
    description: row.description ?? null,
    display_order: row.display_order,
    is_active: Boolean(row.is_active),
  };
}

export function mapWorkType(row) {
  return {
    code: row.code,
    category_code: row.category_code,
    label_th: row.label_th,
    label_en: row.label_en,
    description: row.description ?? null,
    default_visibility: row.default_visibility,
    display_order: row.display_order,
    is_active: Boolean(row.is_active),
  };
}

export function mapFacultyOption(row) {
  return {
    id: row.id,
    public_slug: row.public_slug,
    name_th: row.name_th ?? null,
    name_en: row.name_en ?? null,
    academic_position: row.academic_position ?? null,
    department: row.department ?? null,
    profile_image_url: row.profile_image_url ?? null,
    profile_image_alt: row.profile_image_alt ?? null,
  };
}

function sortAcademicPeriods(left, right) {
  if (right.academic_year !== left.academic_year) {
    return right.academic_year - left.academic_year;
  }
  return (SEMESTER_ORDER.get(right.semester) ?? 0) - (SEMESTER_ORDER.get(left.semester) ?? 0);
}

function sortText(left, right) {
  return left.localeCompare(right, 'th');
}

export function listAcademicPeriods(searchParams) {
  const year = parseAcademicYear(searchParams);
  const semester = parseSemester(searchParams);
  const repository = loadFixtureRepository();

  const items = repository.academicPeriods
    .map(mapAcademicPeriod)
    .filter((period) => year === undefined || period.academic_year === year)
    .filter((period) => semester === undefined || period.semester === semester)
    .sort(sortAcademicPeriods);

  return makeEnvelope(items);
}

export function listEvaluationPeriods(searchParams) {
  const academicPeriodId = optionalParam(searchParams, 'academic_period_id');
  const repository = loadFixtureRepository();

  const items = repository.evaluationPeriods
    .map(mapEvaluationPeriod)
    .filter((period) => !academicPeriodId || period.academic_period_id === academicPeriodId)
    .sort((left, right) => {
      const dateOrder = right.start_date.localeCompare(left.start_date);
      return dateOrder || sortText(left.code, right.code);
    });

  return makeEnvelope(items);
}

export function listWorkCategories(searchParams) {
  const active = parseActive(searchParams);
  const repository = loadFixtureRepository();

  const items = repository.workCategories
    .map(mapWorkCategory)
    .filter((category) => category.is_active === active)
    .sort((left, right) => left.display_order - right.display_order || sortText(left.code, right.code));

  return makeEnvelope(items);
}

export function listWorkTypes(searchParams) {
  const active = parseActive(searchParams);
  const category = optionalParam(searchParams, 'category');
  const repository = loadFixtureRepository();
  const knownCategories = new Set(repository.workCategories.map((item) => item.code));

  if (category && !knownCategories.has(category)) {
    throw new MasterDataQueryError('category', 'category must be a known work category code');
  }

  const categoryOrder = new Map(
    repository.workCategories.map((item) => [item.code, item.display_order ?? 0])
  );

  const items = repository.workTypes
    .map(mapWorkType)
    .filter((type) => type.is_active === active)
    .filter((type) => !category || type.category_code === category)
    .sort((left, right) => {
      const categorySort =
        (categoryOrder.get(left.category_code) ?? 0) - (categoryOrder.get(right.category_code) ?? 0);
      return categorySort || left.display_order - right.display_order || sortText(left.code, right.code);
    });

  return makeEnvelope(items);
}

export function listFaculties(searchParams) {
  parsePublicStatus(searchParams);
  parsePublicVisibility(searchParams);

  const query = optionalParam(searchParams, 'q')?.toLocaleLowerCase('th');
  const repository = loadFixtureRepository();

  const items = repository.faculties
    .filter((faculty) => faculty.status === ACTIVE_STATUS)
    .filter((faculty) => faculty.visibility === PUBLIC_VISIBILITY)
    .filter((faculty) => {
      if (!query) return true;
      return [
        faculty.public_slug,
        faculty.name_th,
        faculty.name_en,
        faculty.academic_position,
        faculty.department,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLocaleLowerCase('th').includes(query));
    })
    .map(mapFacultyOption)
    .sort((left, right) => {
      const leftName = left.name_th ?? left.name_en ?? left.public_slug;
      const rightName = right.name_th ?? right.name_en ?? right.public_slug;
      return sortText(leftName, rightName);
    });

  return makeEnvelope(items);
}

export function formatMasterDataError(error) {
  if (error instanceof MasterDataQueryError) {
    return {
      status: error.status,
      body: {
        error: {
          code: error.code,
          message: error.message,
          details: error.details,
        },
      },
    };
  }

  return {
    status: 500,
    body: {
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Unable to load V2 master data',
      },
    },
  };
}

const masterData = {
  MasterDataQueryError,
  FIXTURE_FILES,
  formatMasterDataError,
  listAcademicPeriods,
  listEvaluationPeriods,
  listFaculties,
  listWorkCategories,
  listWorkTypes,
  loadFixtureRepository,
  mapAcademicPeriod,
  mapEvaluationPeriod,
  mapFacultyOption,
  mapWorkCategory,
  mapWorkType,
};

export { FIXTURE_FILES };

export default masterData;
