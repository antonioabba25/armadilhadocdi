import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const indexHtml = readFileSync(new URL("../../public/index.html", import.meta.url), "utf8");
const appJs = readFileSync(new URL("../../public/assets/app.js", import.meta.url), "utf8");

test("static UI does not present a practical conclusion before IPCA support", () => {
  const forbiddenCopy = [
    "Resultado principal",
    "Resultado pratico",
    "Resultado prático",
    "Melhorou em USD",
    "Piorou em USD",
    "Preservou quase tudo em USD"
  ];

  for (const copy of forbiddenCopy) {
    assert.equal(indexHtml.includes(copy), false, `index.html still contains ${copy}`);
    assert.equal(appJs.includes(copy), false, `app.js still contains ${copy}`);
  }
});

test("static UI introduces the result as period analysis", () => {
  assert.equal(indexHtml.includes("Análise do período"), true);
  assert.equal(appJs.includes("BRL, câmbio e USD em perspectiva"), true);
});
