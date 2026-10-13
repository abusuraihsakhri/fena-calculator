/** Browser-only calculations; no network requests or retained input. */
function finite(value, name, { allowZero = false } = {}) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || (!allowZero && value === 0)) {
    throw new RangeError(name + ' must be a finite ' + (allowZero ? 'non-negative' : 'positive') + ' number.');
  }
  return value;
}
export function calculateFena({ urineNa, serumNa, serumCr, urineCr }) {
  finite(urineNa, 'Urine sodium', { allowZero: true });
  finite(serumNa, 'Serum sodium');
  finite(serumCr, 'Serum creatinine');
  finite(urineCr, 'Urine creatinine');
  const value = (urineNa / serumNa) * (serumCr / urineCr) * 100;
  if (!Number.isFinite(value)) throw new RangeError('Result is outside supported numeric range.');
  return { value, category: value < 1 ? 'prerenal' : value <= 2 ? 'indeterminate' : 'intrinsic' };
}
export function calculateFeurea({ urineUrea, bun, serumCr, urineCr }) {
  finite(urineUrea, 'Urine urea nitrogen', { allowZero: true });
  finite(bun, 'BUN');
  finite(serumCr, 'Serum creatinine');
  finite(urineCr, 'Urine creatinine');
  const value = (urineUrea / bun) * (serumCr / urineCr) * 100;
  if (!Number.isFinite(value)) throw new RangeError('Result is outside supported numeric range.');
  return { value, category: value < 35 ? 'prerenal' : value <= 50 ? 'indeterminate' : 'intrinsic' };
}
export function calculateBunCr({ bun, serumCr }) {
  finite(bun, 'BUN', { allowZero: true });
  finite(serumCr, 'Serum creatinine');
  const value = bun / serumCr;
  if (!Number.isFinite(value)) throw new RangeError('Result is outside supported numeric range.');
  return { value, category: value > 20 ? 'prerenal' : value >= 15 ? 'indeterminate' : 'intrinsic' };
}
export function calculateUrineOsm({ urineOsm, serumOsm = 285 }) {
  finite(urineOsm, 'Urine osmolality', { allowZero: true });
  finite(serumOsm, 'Serum osmolality');
  const ratio = urineOsm / serumOsm;
  if (!Number.isFinite(ratio)) throw new RangeError('Result is outside supported numeric range.');
  return { value: urineOsm, ratio, category: urineOsm > 500 ? 'prerenal' : urineOsm >= 350 ? 'indeterminate' : 'intrinsic' };
}
export function calculateSpecificGravity(sg) {
  finite(sg, 'Urine specific gravity');
  if (sg < 1) throw new RangeError('Urine specific gravity must be at least 1.000.');
  return { value: sg, category: sg > 1.020 ? 'prerenal' : sg >= 1.010 ? 'intrinsic' : 'dilute' };
}
export function calculateAssessment(values) {
  const fena = calculateFena(values);
  const result = { fena };
  if (values.bun != null) result.bunCr = calculateBunCr(values);
  if (values.urineUrea != null) {
    if (values.bun == null) throw new RangeError('Enter BUN to calculate FEUrea.');
    result.feurea = calculateFeurea(values);
  }
  if (values.urineOsm != null) result.urineOsm = calculateUrineOsm(values);
  if (values.sg != null) result.sg = calculateSpecificGravity(values.sg);
  return result;
}
const labels = {
  prerenal: 'Prerenal-pattern range',
  indeterminate: 'Indeterminate range',
  intrinsic: 'Intrinsic-pattern range',
  dilute: 'Dilute urine'
};
function readInput(form, name, required = false) {
  const input = form.elements.namedItem(name);
  const raw = input.value.trim();
  if (!raw) {
    if (required) throw new RangeError(input.dataset.label + ' is required.');
    return null;
  }
  const value = Number(raw);
  if (!Number.isFinite(value)) throw new RangeError(input.dataset.label + ' must be a finite number.');
  return value;
}
function entry(label, value, unit, category, context = '') {
  const item = document.createElement('div');
  item.className = 'result-row';
  const heading = document.createElement('div');
  heading.className = 'result-head';
  const strong = document.createElement('strong');
  strong.textContent = label;
  const number = document.createElement('span');
  number.className = 'result-num';
  number.textContent = value + ' ' + unit;
  heading.append(strong, number);
  const note = document.createElement('p');
  note.className = 'interpretation';
  note.textContent = labels[category] + (context ? ' · ' + context : '');
  item.append(heading, note);
  return item;
}
export function initCalculator(root = document) {
  const form = root.getElementById('calculator-form');
  if (!form) return;
  const results = root.getElementById('result-rows');
  const empty = root.getElementById('empty-state');
  const error = root.getElementById('form-error');
  const copy = root.getElementById('copy-button');
  let summary = '';
  form.addEventListener('submit', event => {
    event.preventDefault();
    error.textContent = '';
    results.replaceChildren();
    copy.disabled = true;
    summary = '';
    try {
      const values = Object.fromEntries([
        ['urineNa', true], ['serumNa', true], ['serumCr', true], ['urineCr', true],
        ['bun', false], ['urineUrea', false], ['urineOsm', false], ['sg', false]
      ].map(([key, required]) => [key, readInput(form, key, required)]));
      const res = calculateAssessment(values);
      results.append(entry('Fractional excretion of sodium', res.fena.value.toFixed(2), '%', res.fena.category, '<1%, 1–2%, >2%'));
      if (res.feurea) results.append(entry('Fractional excretion of urea', res.feurea.value.toFixed(2), '%', res.feurea.category, '<35%, 35–50%, >50%'));
      if (res.bunCr) results.append(entry('BUN / creatinine', res.bunCr.value.toFixed(1), ':1', res.bunCr.category, '<15, 15–20, >20'));
      if (res.urineOsm) results.append(entry('Urine osmolality', res.urineOsm.value.toFixed(0), 'mOsm/kg', res.urineOsm.category));
      if (res.sg) results.append(entry('Urine specific gravity', res.sg.value.toFixed(3), '', res.sg.category));
      summary = 'FENa calculator — educational interpretation only\n' +
        [...results.querySelectorAll('.result-row')].map(el => el.textContent).join('\n') +
        '\nDo not use urinary indices alone to diagnose AKI etiology.';
      empty.hidden = true;
      copy.disabled = false;
    } catch (e) {
      empty.hidden = false;
      error.textContent = e instanceof RangeError ? e.message : 'Unable to calculate. Check all inputs.';
    }
  });
  form.addEventListener('reset', () => {
    results.replaceChildren();
    empty.hidden = false;
    error.textContent = '';
    copy.disabled = true;
    summary = '';
  });
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(summary);
      copy.textContent = 'Copied';
    } catch {
      error.textContent = 'Clipboard unavailable; select and copy the results manually.';
    }
  });
}
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => initCalculator());
  else initCalculator();
}
