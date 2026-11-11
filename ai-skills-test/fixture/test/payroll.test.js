'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { calcNetPay } = require('../src/payroll');

test('calcNetPay applies tax and rounds', () => {
  assert.strictEqual(calcNetPay(1000, 0.2), 800);
  assert.strictEqual(calcNetPay(1234.567, 0.1), 1111.11);
});

test('calcNetPay rejects negative gross', () => {
  assert.throws(() => calcNetPay(-1, 0.2));
});
