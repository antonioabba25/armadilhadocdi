import { stdin, stdout } from "node:process";

import { calculateResult } from "../public/assets/calculations.js";

let rawInput = "";
stdin.setEncoding("utf8");
stdin.on("data", (chunk) => {
  rawInput += chunk;
});

stdin.on("end", () => {
  const payload = JSON.parse(rawInput);
  const results = payload.cases.map((testCase) => ({
    label: testCase.label,
    result: calculateResult({
      startDate: testCase.start_date,
      endDate: testCase.end_date,
      initialBrl: testCase.initial_brl,
      cdiRates: payload.cdi_rates,
      usdRates: payload.usd_rates
    })
  }));
  stdout.write(`${JSON.stringify(results)}\n`);
});
