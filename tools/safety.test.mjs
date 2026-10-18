import test from 'node:test';
import assert from 'node:assert/strict';
const safety = await import(new URL('file://' + process.cwd() + '/tools/safety.mjs')).catch(() => ({}));
test('capture permits only the dedicated loopback demo port', () => {
  assert.equal(typeof safety.demoUrl, 'function');
  assert.equal(safety.demoUrl('http://127.0.0.1:8025'), 'http://127.0.0.1:8025');
  for (const url of ['https://example.com', 'https://tenant.mysmarterschool.com', 'http://127.0.0.1:80', 'http://localhost:8025@evil.test']) assert.throws(() => safety.demoUrl(url));
});
test('demo runtime must be an absolute disposable directory, separate from source', () => {
  assert.equal(typeof safety.demoDirectory, 'function');
  assert.equal(safety.demoDirectory('/private/tmp/smart-school-demo-20261019', '/Users/owner/source'), '/private/tmp/smart-school-demo-20261019');
  assert.equal(safety.demoDirectory('/tmp/smart-school-demo-ci', '/home/owner/source'), '/tmp/smart-school-demo-ci');
  for (const path of ['relative', '/Users/owner/source', '/private/tmp', '/']) assert.throws(() => safety.demoDirectory(path, '/Users/owner/source'));
});
