import test from "node:test";
import assert from "node:assert/strict";

import {
  buildResultPresentation,
  calculateUsdBrlVariationPercentage
} from "../../public/assets/presentation.js";

function assertAlmostEqual(actual, expected, tolerance = 1e-10) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `expected ${actual} to be within ${tolerance} of ${expected}`
  );
}

function getRow(section, label) {
  const row = section.rows.find((candidate) => candidate.label === label);
  assert.ok(row, `missing row ${label}`);
  return row;
}

test("presentation separates BRL, exchange, and USD perspectives", () => {
  const result = {
    initial_brl: 1000,
    final_brl: 1100,
    cdi_percentage: 10,
    initial_usdbrl: 5,
    final_usdbrl: 5.5,
    initial_usd: 200,
    final_usd_with_cdi: 200,
    real_usd_return_percentage: 0,
    initial_fx_date: "2024-01-02",
    final_fx_date: "2024-01-31",
    cdi_days_used: 22
  };

  const presentation = buildResultPresentation(result);

  assert.deepEqual(Object.keys(presentation), ["brl", "exchange", "usd"]);
  assert.equal(presentation.brl.title, "Capital em BRL pelo CDI");
  assert.equal(presentation.exchange.title, "Cambio USD/BRL");
  assert.equal(presentation.usd.title, "Posicao equivalente em USD");
  assert.equal(getRow(presentation.brl, "Valor final em BRL com CDI").value, 1100);
  assert.equal(getRow(presentation.exchange, "PTAX venda final").value, 5.5);
  assert.equal(getRow(presentation.usd, "Valor final em BRL convertido para USD").value, 200);
});

test("presentation derives exchange variation and equivalent rates", () => {
  const result = {
    initial_brl: 1000,
    final_brl: 1100,
    cdi_percentage: 10,
    initial_usdbrl: 5,
    final_usdbrl: 5.5,
    initial_usd: 200,
    final_usd_with_cdi: 200,
    real_usd_return_percentage: 0,
    initial_fx_date: "2024-01-02",
    final_fx_date: "2024-01-31",
    cdi_days_used: 22
  };

  const presentation = buildResultPresentation(result);

  assertAlmostEqual(calculateUsdBrlVariationPercentage(result), 10);
  assertAlmostEqual(getRow(presentation.brl, "CDI equivalente mensal").value, 10);
  assertAlmostEqual(getRow(presentation.exchange, "USD/BRL equivalente mensal").value, 10);
  assertAlmostEqual(getRow(presentation.usd, "Variacao equivalente mensal em USD").value, 0);
});
