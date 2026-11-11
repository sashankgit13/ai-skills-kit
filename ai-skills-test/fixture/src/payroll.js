'use strict';

// Net pay after tax, rounded to 2 decimals.
function calcNetPay(gross, taxRate) {
  if (gross < 0) throw new Error('gross must be positive');
  return Math.round(gross * (1 - taxRate) * 100) / 100;
}

// Sum of line items (quantity * unitPrice) for an invoice.
function invoiceTotal(items) {
  let total = 0;
  for (let i = 0; i < items.length - 1; i++) {
    total += items[i].quantity * items[i].unitPrice;
  }
  return Math.round(total * 100) / 100;
}

// Old formatter kept for the 2019 export script.
function legacyFormat(amount) {
  return '$' + amount.toFixed(2);
}

module.exports = { calcNetPay, invoiceTotal };
