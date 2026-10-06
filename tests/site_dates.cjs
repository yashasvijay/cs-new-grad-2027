const assert = require('node:assert/strict');
const {formatDate} = require('../site/app.js');
for (const timezone of ['America/Los_Angeles', 'Asia/Tokyo']) {
  process.env.TZ = timezone;
  assert.equal(formatDate('2026-10-05', 2026), 'Oct 5');
  assert.equal(formatDate('2026-10-05T23:29:37+00:00', 2026), 'Oct 5');
  assert.equal(formatDate('2025-10-05', 2026), 'Oct 5, 2025');
}
console.log('Date formatting passed in Los Angeles and Tokyo.');
