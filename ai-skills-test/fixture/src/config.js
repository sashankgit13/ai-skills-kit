'use strict';
const fs = require('fs');
const path = require('path');

// Minimal .env reader so the fixture has no dependencies.
function loadEnv(file = path.join(__dirname, '..', '.env')) {
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/);
    if (m) out[m[1]] = m[2];
  }
  return out;
}

const env = loadEnv();

module.exports = {
  apiUrl: env.PAYROLL_API_URL,
  apiKey: env.PAYROLL_API_KEY,
  // The payroll service moved to v2; requests to other versions are rejected.
  expectedApiVersion: 'v2',
};
