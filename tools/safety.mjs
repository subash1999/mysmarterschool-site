import { isAbsolute, normalize } from 'node:path';

export function demoUrl(value) {
  const url = new URL(value);
  if (url.origin !== 'http://127.0.0.1:8025' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('Only http://127.0.0.1:8025 is permitted for demo capture.');
  }
  return url.origin;
}

export function demoDirectory(value, source) {
  if (!isAbsolute(value) || !isAbsolute(source)) throw new Error('Absolute paths required.');
  const path = normalize(value);
  if (!/^\/(?:private\/)?tmp\/smart-school-demo-[a-z0-9-]+$/.test(path) || path === normalize(source)) {
    throw new Error('Use a separate temporary smart-school-demo-… directory.');
  }
  return path;
}
