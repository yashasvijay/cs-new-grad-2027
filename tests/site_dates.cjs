const assert = require('node:assert/strict');
const {formatDate, relativeDate} = require('../site/app.js');
for (const timezone of ['America/Los_Angeles', 'Asia/Tokyo']) {
  process.env.TZ = timezone;
  assert.equal(formatDate('2026-10-05', 2026), 'Oct 5');
  assert.equal(formatDate('2026-10-05T23:29:37+00:00', 2026), 'Oct 5');
  assert.equal(formatDate('2025-10-05', 2026), 'Oct 5, 2025');
  const now = new Date(2026, 9, 6, 12);
  assert.equal(relativeDate('2026-10-06', now), 'today');
  assert.equal(relativeDate('2026-10-05', now), '1 day ago');
  assert.equal(relativeDate('2026-10-04T23:29:37+00:00', now), '2 days ago');
  assert.equal(relativeDate('2026-09-30', now), '6 days ago');
  assert.equal(relativeDate('2026-10-07', now), 'Oct 7');
}
console.log('Date formatting passed in Los Angeles and Tokyo.');
