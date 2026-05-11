import test from "node:test";
import assert from "node:assert/strict";

import {
  DataUnavailableError,
  DomainValidationError,
  QuoteResolver,
  buildChartSeries,
  calculateEquivalentRatePercentage,
  calculateResult,
  lookupQuoteWithFallback
} from "../../public/assets/calculations.js";

const cdiRates = {
  "2024-01-01": 0.10,
  "2024-01-02": 0.20,
  "2024-01-03": 0.30
};

const usdRates = {
  "2023-12-29": 4.90,
  "2024-01-01": 5.00,
  "2024-01-03": 5.20,
  "2024-01-04": 5.30
};

function assertAlmostEqual(actual, expected, tolerance = 1e-10) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `expected ${actual} to be within ${tolerance} of ${expected}`
  );
}

test("calculation uses start inclusive and end exclusive CDI window", () => {
  const result = calculateResult({
    startDate: "2024-01-01",
    endDate: "2024-01-03",
    initialBrl: 1000.0,
    cdiRates,
    usdRates
  });

  const expectedFactor = (1 + 0.10 / 100) * (1 + 0.20 / 100);
  assertAlmostEqual(result.cdi_factor, expectedFactor);
  assert.equal(result.cdi_days_used, 2);
});

test("equivalent rate preserves the 252 business-day annual rate", () => {
  const equivalentRate = calculateEquivalentRatePercentage(13.25, 252, 252);
  assertAlmostEqual(equivalentRate, 13.25);
});

test("quote resolver uses previous quote inside fallback window", () => {
  const quote = lookupQuoteWithFallback(usdRates, "2024-01-02");
  assert.equal(quote.effective_date, "2024-01-01");
  assert.equal(quote.value, 5.00);
});

test("calculation resolves non-business dates to official CDI dates", () => {
  const result = calculateResult({
    startDate: "2024-01-06",
    endDate: "2024-01-09",
    initialBrl: 1000.0,
    cdiRates: {
      "2024-01-05": 0.10,
      "2024-01-08": 0.20,
      "2024-01-09": 0.30
    },
    usdRates: {
      "2024-01-05": 5.00,
      "2024-01-08": 5.10,
      "2024-01-09": 5.20
    }
  });

  const expectedFactor = (1 + 0.10 / 100) * (1 + 0.20 / 100);
  assert.equal(result.effective_start_date, "2024-01-05");
  assert.equal(result.effective_end_date, "2024-01-09");
  assert.equal(result.initial_fx_date, "2024-01-05");
  assertAlmostEqual(result.cdi_factor, expectedFactor);
  assert.equal(result.cdi_days_used, 2);
});

test("real circulation start can use first official CDI date inside tolerance", () => {
  const result = calculateResult({
    startDate: "1994-07-01",
    endDate: "1994-07-05",
    initialBrl: 1000.0,
    cdiRates: {
      "1994-07-04": 0.20,
      "1994-07-05": 0.30
    },
    usdRates: {
      "1994-07-01": 1.00,
      "1994-07-04": 0.94,
      "1994-07-05": 0.93
    }
  });

  assert.equal(result.effective_start_date, "1994-07-04");
  assert.equal(result.effective_end_date, "1994-07-05");
  assert.equal(result.initial_fx_date, "1994-07-04");
  assertAlmostEqual(result.cdi_factor, 1 + 0.20 / 100);
});

test("invalid period and value are rejected clearly", () => {
  assert.throws(
    () => calculateResult({ startDate: "2024-01-03", endDate: "2024-01-03", initialBrl: 1000, cdiRates, usdRates }),
    DomainValidationError
  );
  assert.throws(
    () => calculateResult({ startDate: "2024-01-01", endDate: "2024-01-03", initialBrl: 0, cdiRates, usdRates }),
    DomainValidationError
  );
});

test("quote outside fallback window raises data unavailable", () => {
  const resolver = new QuoteResolver({ "2024-01-01": 5.00 }, 2);
  assert.throws(() => resolver.lookup("2024-01-04"), DataUnavailableError);
});

test("calculation ignores invalid market rows", () => {
  const result = calculateResult({
    startDate: "2024-01-01",
    endDate: "2024-01-03",
    initialBrl: 1000,
    cdiRates: {
      ...cdiRates,
      "invalid-date": 99,
      "2024-01-02-extra": 99
    },
    usdRates: {
      ...usdRates,
      "invalid-date": 99
    }
  });

  const expectedFactor = (1 + 0.10 / 100) * (1 + 0.20 / 100);
  assertAlmostEqual(result.cdi_factor, expectedFactor);
});

test("chart series uses only official CDI dates and mirrors calculation fallbacks", () => {
  const series = buildChartSeries({
    startDate: "2024-01-06",
    endDate: "2024-01-09",
    initialBrl: 1000,
    cdiRates: {
      "2024-01-05": 0.10,
      "2024-01-08": 0.20,
      "2024-01-09": 0.30
    },
    usdRates: {
      "2024-01-05": 5.00,
      "2024-01-08": 5.10,
      "2024-01-09": 5.20
    }
  });

  assert.deepEqual(series.map((row) => row.date), ["2024-01-05", "2024-01-08", "2024-01-09"]);
  const expectedCdi = ((1 + 0.10 / 100) * (1 + 0.20 / 100) - 1) * 100;
  assertAlmostEqual(series.at(-1).cdi_accumulated, expectedCdi);
});
