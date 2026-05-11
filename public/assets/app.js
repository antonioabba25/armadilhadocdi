import {
  DataUnavailableError,
  DomainValidationError,
  buildChartSeries,
  calculateResult
} from "./calculations.js";
import { buildResultPresentation } from "./presentation.js";

const DATASET_URL = "./data/market-data.latest.json";

let marketData = null;

const form = document.querySelector("#analysis-form");
const startInput = document.querySelector("#start-date");
const endInput = document.querySelector("#end-date");
const initialInput = document.querySelector("#initial-brl");
const dataStatus = document.querySelector("#data-status");
const resultTitle = document.querySelector("#result-title");
const metricsGrid = document.querySelector("#metrics-grid");
const fallbackNotice = document.querySelector("#fallback-notice");
const chart = document.querySelector("#comparison-chart");
const chartEmpty = document.querySelector("#chart-empty");
const generatedAt = document.querySelector("#generated-at");
const coverage = document.querySelector("#coverage");
const counts = document.querySelector("#counts");

const brlFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL"
});

const usdFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "USD"
});

const numberFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

const percentFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: "exceptZero"
});

function formatDate(isoDate) {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

function formatGeneratedAt(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Sao_Paulo"
  }).format(date);
}

function addDays(isoDate, days) {
  const date = new Date(`${isoDate}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function validateDataset(dataset) {
  if (!dataset || dataset.schema_version !== 1) {
    throw new Error("Dataset estatico em versao invalida.");
  }
  for (const key of ["coverage", "limits", "cdi_rates", "usd_rates"]) {
    if (!dataset[key] || typeof dataset[key] !== "object") {
      throw new Error(`Dataset sem ${key}.`);
    }
  }
  if (Object.keys(dataset.cdi_rates).length === 0 || Object.keys(dataset.usd_rates).length === 0) {
    throw new Error("Dataset estatico sem dados oficiais suficientes.");
  }
}

function setInitialFormValues(dataset) {
  const maxEnd = dataset.coverage.requested_end_date || dataset.coverage.end_date;
  const defaultEnd = dataset.coverage.end_date;
  const defaultStart = addDays(defaultEnd, -365);
  startInput.min = dataset.limits.earliest_supported_date;
  startInput.max = maxEnd;
  endInput.min = addDays(dataset.limits.earliest_supported_date, 1);
  endInput.max = maxEnd;
  startInput.value = defaultStart < startInput.min ? startInput.min : defaultStart;
  endInput.value = defaultEnd;
  initialInput.value = "1000.00";
}

function updateDatasetMetadata(dataset) {
  dataStatus.textContent = `Dados ate ${formatDate(dataset.coverage.end_date)}`;
  generatedAt.textContent = formatGeneratedAt(dataset.generated_at);
  coverage.textContent = `${formatDate(dataset.coverage.start_date)} a ${formatDate(dataset.coverage.end_date)}`;
  counts.textContent = `${Object.keys(dataset.cdi_rates).length} CDI, ${Object.keys(dataset.usd_rates).length} USD/BRL`;
}

function formatPresentationValue(row) {
  if (row.format === "brl") {
    return brlFormatter.format(row.value);
  }
  if (row.format === "usd") {
    return usdFormatter.format(row.value);
  }
  if (row.format === "percent") {
    return `${percentFormatter.format(row.value)}%`;
  }
  if (row.format === "quote") {
    return numberFormatter.format(row.value);
  }
  if (row.format === "integer") {
    return String(row.value);
  }
  if (row.format === "date") {
    return formatDate(row.value);
  }
  return String(row.value);
}

function renderPresentationSection(section, variant = "") {
  const wrapper = document.createElement("section");
  wrapper.className = `result-section${variant ? ` result-section-${variant}` : ""}`;
  const title = document.createElement("h3");
  title.textContent = section.title;

  const list = document.createElement("dl");
  list.className = "result-table";
  for (const row of section.rows) {
    const item = document.createElement("div");
    const label = document.createElement("dt");
    const value = document.createElement("dd");
    label.textContent = row.label;
    value.textContent = formatPresentationValue(row);
    item.append(label, value);
    list.append(item);
  }

  wrapper.append(title, list);
  metricsGrid.append(wrapper);
}

function renderResult(result) {
  metricsGrid.replaceChildren();
  fallbackNotice.className = "notice";

  resultTitle.textContent = "BRL, cambio e USD em perspectiva";

  const presentation = buildResultPresentation(result);
  renderPresentationSection(presentation.brl, "brl");
  renderPresentationSection(presentation.exchange, "exchange");
  renderPresentationSection(presentation.usd, "usd");

  const notices = [];
  if (result.effective_start_date !== result.start_date || result.effective_end_date !== result.end_date) {
    notices.push(
      `Periodo efetivo de mercado: ${formatDate(result.effective_start_date)} a ${formatDate(result.effective_end_date)}.`
    );
  }
  if (result.initial_fx_date !== result.effective_start_date) {
    notices.push(`PTAX inicial usada: ${formatDate(result.initial_fx_date)}.`);
  }
  if (result.final_fx_date !== result.effective_end_date) {
    notices.push(`PTAX final usada: ${formatDate(result.final_fx_date)}.`);
  }
  fallbackNotice.textContent = notices.join(" ");
}

function renderError(error) {
  resultTitle.textContent = "Nao foi possivel calcular";
  metricsGrid.replaceChildren();
  fallbackNotice.className = "notice error";
  fallbackNotice.textContent = error.message || "Erro inesperado.";
  chart.replaceChildren();
  chartEmpty.classList.remove("hidden");
}

function linePath(rows, key, xScale, yScale) {
  return rows
    .map((row, index) => `${index === 0 ? "M" : "L"} ${xScale(row.index).toFixed(2)} ${yScale(row[key]).toFixed(2)}`)
    .join(" ");
}

function renderChart(rows) {
  chart.replaceChildren();
  if (rows.length < 2) {
    chartEmpty.classList.remove("hidden");
    chartEmpty.textContent = "Nao ha pontos suficientes para o grafico.";
    return;
  }

  chartEmpty.classList.add("hidden");
  const width = 980;
  const height = 360;
  const padding = { top: 26, right: 26, bottom: 42, left: 58 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const indexedRows = rows.map((row, index) => ({ ...row, index }));
  const values = indexedRows.flatMap((row) => [
    row.cdi_accumulated,
    row.usd_accumulated,
    row.usd_percent_variation
  ]);
  const minValue = Math.min(0, ...values);
  const maxValue = Math.max(0, ...values);
  const span = maxValue - minValue || 1;
  const yMin = minValue - span * 0.08;
  const yMax = maxValue + span * 0.08;

  const xScale = (index) => padding.left + (index / (indexedRows.length - 1)) * plotWidth;
  const yScale = (value) => padding.top + ((yMax - value) / (yMax - yMin)) * plotHeight;

  chart.setAttribute("viewBox", `0 0 ${width} ${height}`);
  chart.setAttribute("preserveAspectRatio", "none");

  const fragment = document.createDocumentFragment();
  const yTicks = 5;
  for (let index = 0; index <= yTicks; index += 1) {
    const value = yMin + ((yMax - yMin) * index) / yTicks;
    const y = yScale(value);
    fragment.append(svgElement("line", {
      class: "grid-line",
      x1: padding.left,
      x2: width - padding.right,
      y1: y,
      y2: y
    }));
    const label = svgElement("text", {
      class: "axis-label",
      x: padding.left - 8,
      y: y + 4,
      "text-anchor": "end"
    });
    label.textContent = `${numberFormatter.format(value)}%`;
    fragment.append(label);
  }

  fragment.append(svgElement("line", {
    class: "axis-line",
    x1: padding.left,
    x2: width - padding.right,
    y1: yScale(0),
    y2: yScale(0)
  }));

  const firstLabel = svgElement("text", {
    class: "axis-label",
    x: padding.left,
    y: height - 14,
    "text-anchor": "start"
  });
  firstLabel.textContent = formatDate(indexedRows[0].date);
  fragment.append(firstLabel);

  const lastLabel = svgElement("text", {
    class: "axis-label",
    x: width - padding.right,
    y: height - 14,
    "text-anchor": "end"
  });
  lastLabel.textContent = formatDate(indexedRows.at(-1).date);
  fragment.append(lastLabel);

  for (const [key, className] of [
    ["cdi_accumulated", "series-cdi"],
    ["usd_accumulated", "series-usd"],
    ["usd_percent_variation", "series-real"]
  ]) {
    fragment.append(svgElement("path", {
      class: `series-line ${className}`,
      d: linePath(indexedRows, key, xScale, yScale)
    }));
  }

  chart.append(fragment);
}

function svgElement(tagName, attributes) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tagName);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, value);
  }
  return element;
}

function runAnalysis() {
  if (!marketData) {
    throw new Error("Dataset ainda nao foi carregado.");
  }
  const startDate = startInput.value;
  const endDate = endInput.value;
  const initialBrl = Number(initialInput.value);
  const result = calculateResult({
    startDate,
    endDate,
    initialBrl,
    cdiRates: marketData.cdi_rates,
    usdRates: marketData.usd_rates
  });
  const chartRows = buildChartSeries({
    startDate,
    endDate,
    initialBrl,
    cdiRates: marketData.cdi_rates,
    usdRates: marketData.usd_rates
  });
  renderResult(result);
  renderChart(chartRows);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    runAnalysis();
  } catch (error) {
    if (
      error instanceof DomainValidationError ||
      error instanceof DataUnavailableError ||
      error instanceof Error
    ) {
      renderError(error);
    } else {
      renderError(new Error("Erro inesperado."));
    }
  }
});

async function loadDataset() {
  try {
    const response = await fetch(DATASET_URL, { cache: "no-cache" });
    if (!response.ok) {
      throw new Error("Dataset estatico nao encontrado.");
    }
    const dataset = await response.json();
    validateDataset(dataset);
    marketData = dataset;
    setInitialFormValues(dataset);
    updateDatasetMetadata(dataset);
    runAnalysis();
  } catch (error) {
    dataStatus.textContent = "Dados indisponiveis";
    generatedAt.textContent = "--";
    coverage.textContent = "--";
    counts.textContent = "--";
    renderError(error instanceof Error ? error : new Error("Erro ao carregar dados."));
  }
}

loadDataset();
