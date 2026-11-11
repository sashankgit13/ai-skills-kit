'use strict';
const config = require('./config');

// Pretend API client: checks configuration the way the real service would.
function connect() {
  if (!config.apiKey) return { ok: false, error: 'missing API key' };
  if (!config.apiUrl || !config.apiUrl.endsWith('/' + config.expectedApiVersion)) {
    return { ok: false, error: 'connection refused: unsupported API version' };
  }
  return { ok: true };
}

if (require.main === module) {
  console.log(JSON.stringify(connect()));
}

module.exports = { connect };
