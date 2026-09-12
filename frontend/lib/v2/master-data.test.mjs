import assert from 'node:assert/strict';
import test from 'node:test';

import masterData from './master-data.mjs';

test('academic periods are sorted by academic year and semester descending', () => {
  const response = masterData.listAcademicPeriods();

  assert.deepEqual(
    response.items.map((item) => item.id),
    ['ap-2568-1', 'ap-2567-2', 'ap-2567-1', 'ap-2566-2', 'ap-2566-1']
  );
  assert.equal(response.meta.count, 5);
});

test('academic periods can be filtered by year and semester', () => {
  const response = masterData.listAcademicPeriods('year=2567&semester=2');

  assert.equal(response.meta.count, 1);
  assert.equal(response.items[0].id, 'ap-2567-2');
});

test('work categories return active categories sorted by display order', () => {
  const response = masterData.listWorkCategories();

  assert.deepEqual(
    response.items.map((item) => item.code),
    ['TEACHING', 'RESEARCH', 'SUPERVISION', 'ACADEMIC_SERVICE', 'ADMINISTRATION']
  );
});

test('work types return all active types sorted by category order and display order', () => {
  const response = masterData.listWorkTypes();

  assert.equal(response.meta.count, 14);
  assert.deepEqual(
    response.items.slice(0, 3).map((item) => item.code),
    ['LECTURE', 'LAB', 'SEMINAR']
  );
});

test('work types can be filtered by category', () => {
  const response = masterData.listWorkTypes('category=RESEARCH');

  assert.deepEqual(
    response.items.map((item) => item.code),
    ['PUBLICATION', 'RESEARCH_PROJECT', 'RESEARCH_GRANT']
  );
});

test('unknown work type category returns INVALID_QUERY', () => {
  assert.throws(
    () => masterData.listWorkTypes('category=UNKNOWN'),
    (error) => error.code === 'INVALID_QUERY' && error.details.field === 'category'
  );
});

test('faculties expose only public-safe dropdown fields and preserve public_slug', () => {
  const response = masterData.listFaculties('q=prapaporn');

  assert.equal(response.meta.count, 1);
  assert.deepEqual(Object.keys(response.items[0]).sort(), [
    'academic_position',
    'department',
    'id',
    'name_en',
    'name_th',
    'profile_image_alt',
    'profile_image_url',
    'public_slug',
  ]);
  assert.equal(response.items[0].public_slug, 'prapaporn-rattanatamrong');
  assert.equal('metadata' in response.items[0], false);
  assert.equal('email_public' in response.items[0], false);
});

test('empty faculty search returns an empty envelope', () => {
  const response = masterData.listFaculties('q=no-such-faculty');

  assert.deepEqual(response, {
    items: [],
    meta: {
      count: 0,
    },
  });
});

test('internal faculty visibility is rejected on the public endpoint', () => {
  assert.throws(
    () => masterData.listFaculties('visibility=INTERNAL'),
    (error) => error.code === 'INVALID_QUERY' && error.details.field === 'visibility'
  );
});
