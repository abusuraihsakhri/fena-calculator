import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  calculateFena, calculateFeurea, calculateBunCr,
  calculateUrineOsm, calculateSpecificGravity, calculateAssessment
} from '../web/calculator.mjs';

test('FENa arithmetic, zero numerator and thresholds', () => {
  const r = calculateFena({ urineNa: 10, serumNa: 140, serumCr: 2, urineCr: 200 });
  assert.ok(Math.abs(r.value - (10 * 2 / (140 * 200) * 100)) < 1e-12);
  assert.equal(r.category, 'prerenal');
  const base = { serumNa: 100, serumCr: 1, urineCr: 100 };
  assert.equal(calculateFena({ ...base, urineNa: 0 }).value, 0);
  assert.equal(calculateFena({ ...base, urineNa: 100 }).category, 'indeterminate');
  assert.equal(calculateFena({ ...base, urineNa: 200 }).category, 'indeterminate');
  assert.equal(calculateFena({ ...base, urineNa: 201 }).category, 'intrinsic');
});

test('FEUrea arithmetic and cutoffs', () => {
  const base = { serumCr: 1, bun: 100, urineCr: 100 };
  assert.equal(calculateFeurea({ ...base, urineUrea: 3499 }).category, 'prerenal');
  assert.equal(calculateFeurea({ ...base, urineUrea: 3500 }).category, 'indeterminate');
  assert.equal(calculateFeurea({ ...base, urineUrea: 5000 }).category, 'indeterminate');
  assert.equal(calculateFeurea({ ...base, urineUrea: 5001 }).category, 'intrinsic');
});

test('BUN/Cr, urine osmolality and specific gravity', () => {
  assert.equal(calculateBunCr({ bun: 40, serumCr: 2 }).category, 'indeterminate');
  assert.equal(calculateBunCr({ bun: 41, serumCr: 2 }).category, 'prerenal');
  assert.equal(calculateUrineOsm({ urineOsm: 600, serumOsm: 300 }).ratio, 2);
  assert.equal(calculateUrineOsm({ urineOsm: 350 }).category, 'indeterminate');
  assert.equal(calculateSpecificGravity(1.010).category, 'intrinsic');
  assert.equal(calculateSpecificGravity(1.005).category, 'dilute');
});

test('reject invalid inputs and absent FEUrea denominator', () => {
  const base = { urineNa: 10, serumNa: 140, serumCr: 2, urineCr: 200 };
  for (const n of [NaN, Infinity, -Infinity, -1]) {
    assert.throws(() => calculateFena({ ...base, urineNa: n }), RangeError);
  }
  for (const name of ['serumNa', 'serumCr', 'urineCr']) {
    assert.throws(() => calculateFena({ ...base, [name]: 0 }), RangeError);
  }
  assert.throws(() => calculateFeurea({ urineUrea: 10, bun: 0, serumCr: 1, urineCr: 50 }), RangeError);
  assert.throws(() => calculateUrineOsm({ urineOsm: -1 }), RangeError);
  assert.throws(() => calculateSpecificGravity(0.99), RangeError);
  assert.throws(() => calculateAssessment({ ...base, urineUrea: 100 }), /BUN/);
});

test('optional indices and unrounded threshold classification', () => {
  const r = calculateAssessment({
    urineNa: 99.9, serumNa: 100, serumCr: 1, urineCr: 100,
    bun: 40, urineUrea: 2000, urineOsm: 500, sg: 1.020
  });
  assert.equal(r.fena.category, 'prerenal');
  assert.equal(r.bunCr.value, 40);
  assert.equal(r.feurea.category, 'indeterminate');
  assert.equal(r.urineOsm.category, 'indeterminate');
  assert.equal(r.sg.category, 'intrinsic');
});

test('reject overflowing derived ratios', () => {
  assert.throws(() => calculateFena({ urineNa: 1e308, serumCr: 1e308, serumNa: 1e-308, urineCr: 1e-308 }), RangeError);
  assert.throws(() => calculateFeurea({ urineUrea: 1e308, serumCr: 1e308, bun: 1e-308, urineCr: 1e-308 }), RangeError);
  assert.throws(() => calculateBunCr({ bun: 1e308, serumCr: 1e-308 }), RangeError);
  assert.throws(() => calculateUrineOsm({ urineOsm: 1e308, serumOsm: 1e-308 }), RangeError);
});
