export const EARLIEST_SUPPORTED_DATE = "1994-07-01";
export const MAX_USD_FALLBACK_DAYS = 15;
export const MAX_MARKET_DATE_FALLBACK_DAYS = 15;
export const BUSINESS_DAYS_PER_YEAR = 252;
export const BUSINESS_DAYS_PER_MONTH = 22;

const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const MS_PER_DAY = 24 * 60 * 60 * 1000;

export class DomainValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "DomainValidationError";
  }
}

export class DataUnavailableError extends Error {
  constructor(message) {
    super(message);
    this.name = "DataUnavailableError";
  }
}

export function isIsoDate(value) {
  if (typeof value !== "string" || !ISO_DATE_PATTERN.test(value)) {
    return false;
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function parseIsoDate(value) {
  if (!isIsoDate(value)) {
    throw new DomainValidationError("Use datas no formato YYYY-MM-DD.");
  }
  return new Date(`${value}T00:00:00Z`);
}

function daysBetween(startDate, endDate) {
  return Math.round((parseIsoDate(endDate).getTime() - parseIsoDate(startDate).getTime()) / MS_PER_DAY);
}

function normalizeSeries(series, minDate = null) {
  const valuesByDate = new Map();
  if (!series || typeof series !== "object") {
    return valuesByDate;
  }

  for (const [rawDate, rawValue] of Object.entries(series)) {
    if (!isIsoDate(rawDate)) {
      continue;
    }
    if (minDate !== null && rawDate < minDate) {
      continue;
    }
    const value = Number(rawValue);
    if (!Number.isFinite(value)) {
      continue;
    }
    valuesByDate.set(rawDate, value);
  }
  return valuesByDate;
}

function sortedDatesFromMap(valuesByDate) {
  return Array.from(valuesByDate.keys()).sort();
}

function bisectRight(sortedValues, target) {
  let left = 0;
  let right = sortedValues.length;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (sortedValues[middle] <= target) {
      left = middle + 1;
    } else {
      right = middle;
    }
  }
  return left;
}

export function validateInputs(startDate, endDate, initialBrl) {
  if (!isIsoDate(startDate) || !isIsoDate(endDate)) {
    throw new DomainValidationError("Use datas no formato YYYY-MM-DD.");
  }
  if (startDate < EARLIEST_SUPPORTED_DATE) {
    throw new DomainValidationError(
      "A data inicial deve ser em ou posterior a 01/07/1994, quando o real brasileiro entrou em circulação."
    );
  }
  if (endDate <= startDate) {
    throw new DomainValidationError("A data final deve ser maior que a data inicial.");
  }
  if (!(Number(initialBrl) > 0)) {
    throw new DomainValidationError("O valor inicial deve ser maior que zero.");
  }
}

export class QuoteResolver {
  constructor(usdRates, maxDaysBack = MAX_USD_FALLBACK_DAYS, minDate = null) {
    this.maxDaysBack = maxDaysBack;
    this.valuesByDate = normalizeSeries(usdRates, minDate);
    this.orderedDates = sortedDatesFromMap(this.valuesByDate);
  }

  lookup(targetDate) {
    if (!isIsoDate(targetDate)) {
      throw new DomainValidationError("Use datas no formato YYYY-MM-DD.");
    }
    const index = bisectRight(this.orderedDates, targetDate) - 1;
    if (index >= 0) {
      const effectiveDate = this.orderedDates[index];
      if (daysBetween(effectiveDate, targetDate) <= this.maxDaysBack) {
        return {
          requested_date: targetDate,
          effective_date: effectiveDate,
          value: this.valuesByDate.get(effectiveDate)
        };
      }
    }
    throw new DataUnavailableError(
      "Não foi encontrada cotação USD/BRL suficiente para o período selecionado."
    );
  }
}

export class MarketDateResolver {
  constructor(series, label, maxDaysBack = MAX_MARKET_DATE_FALLBACK_DAYS, minDate = null) {
    this.label = label;
    this.maxDaysBack = maxDaysBack;
    this.orderedDates = sortedDatesFromMap(normalizeSeries(series, minDate));
  }

  lookup(targetDate, allowForwardIfBeforeFirst = false) {
    if (!isIsoDate(targetDate)) {
      throw new DomainValidationError("Use datas no formato YYYY-MM-DD.");
    }
    const index = bisectRight(this.orderedDates, targetDate) - 1;
    if (index >= 0) {
      const effectiveDate = this.orderedDates[index];
      if (daysBetween(effectiveDate, targetDate) <= this.maxDaysBack) {
        return effectiveDate;
      }
    }

    if (allowForwardIfBeforeFirst && this.orderedDates.length > 0) {
      const effectiveDate = this.orderedDates[0];
      if (targetDate <= effectiveDate && daysBetween(targetDate, effectiveDate) <= this.maxDaysBack) {
        return effectiveDate;
      }
    }

    throw new DataUnavailableError(
      `Não foi encontrado dado de ${this.label} suficiente para o período selecionado.`
    );
  }
}

export function lookupQuoteWithFallback(usdRates, targetDate, maxDaysBack = MAX_USD_FALLBACK_DAYS) {
  return new QuoteResolver(usdRates, maxDaysBack).lookup(targetDate);
}

export function resolveCdiPeriod(cdiRates, startDate, endDate) {
  const resolver = new MarketDateResolver(
    cdiRates,
    "CDI",
    MAX_MARKET_DATE_FALLBACK_DAYS,
    EARLIEST_SUPPORTED_DATE
  );
  const effectiveStartDate = resolver.lookup(startDate, true);
  const effectiveEndDate = resolver.lookup(endDate);

  if (effectiveEndDate <= effectiveStartDate) {
    throw new DataUnavailableError("Não há dias úteis de CDI suficientes para o período informado.");
  }

  return [effectiveStartDate, effectiveEndDate];
}

export function calculateCdiFactor(cdiRates, startDate, endDate) {
  const normalized = normalizeSeries(cdiRates);
  const windowRates = [];
  for (const [isoDate, rate] of normalized.entries()) {
    if (startDate <= isoDate && isoDate < endDate) {
      windowRates.push([isoDate, rate]);
    }
  }
  windowRates.sort((left, right) => left[0].localeCompare(right[0]));

  let factor = 1.0;
  for (const [, rate] of windowRates) {
    factor *= 1 + rate / 100;
  }

  if (windowRates.length === 0) {
    throw new DataUnavailableError("Não há dados de CDI suficientes para o período informado.");
  }
  return [factor, windowRates.length];
}

export function calculateEquivalentRatePercentage(
  periodPercentage,
  periodBusinessDays,
  equivalentBusinessDays
) {
  if (periodBusinessDays <= 0) {
    throw new Error("period_business_days must be greater than zero.");
  }
  if (equivalentBusinessDays <= 0) {
    throw new Error("equivalent_business_days must be greater than zero.");
  }
  const periodFactor = 1 + periodPercentage / 100;
  const equivalentFactor = periodFactor ** (equivalentBusinessDays / periodBusinessDays);
  return (equivalentFactor - 1) * 100;
}

export function calculateResult({ startDate, endDate, initialBrl, cdiRates, usdRates }) {
  const normalizedInitialBrl = Number(initialBrl);
  validateInputs(startDate, endDate, normalizedInitialBrl);
  const [effectiveStartDate, effectiveEndDate] = resolveCdiPeriod(cdiRates, startDate, endDate);
  const [cdiFactor, cdiDaysUsed] = calculateCdiFactor(cdiRates, effectiveStartDate, effectiveEndDate);

  const quoteResolver = new QuoteResolver(usdRates, MAX_USD_FALLBACK_DAYS, EARLIEST_SUPPORTED_DATE);
  const initialQuote = quoteResolver.lookup(effectiveStartDate);
  const finalQuote = quoteResolver.lookup(effectiveEndDate);

  const finalBrl = normalizedInitialBrl * cdiFactor;
  const initialUsd = normalizedInitialBrl / initialQuote.value;
  const finalUsdWithCdi = finalBrl / finalQuote.value;
  const realUsdReturnPercentage = (finalUsdWithCdi / initialUsd - 1) * 100;

  return {
    start_date: startDate,
    end_date: endDate,
    effective_start_date: effectiveStartDate,
    effective_end_date: effectiveEndDate,
    initial_brl: normalizedInitialBrl,
    final_brl: finalBrl,
    cdi_factor: cdiFactor,
    cdi_percentage: (cdiFactor - 1) * 100,
    initial_usd: initialUsd,
    final_usd_with_cdi: finalUsdWithCdi,
    initial_usdbrl: initialQuote.value,
    final_usdbrl: finalQuote.value,
    initial_fx_date: initialQuote.effective_date,
    final_fx_date: finalQuote.effective_date,
    real_usd_return_percentage: realUsdReturnPercentage,
    cdi_days_used: cdiDaysUsed
  };
}

export function buildChartSeries({ startDate, endDate, cdiRates, usdRates, initialBrl }) {
  const normalizedInitialBrl = Number(initialBrl);
  validateInputs(startDate, endDate, normalizedInitialBrl);
  const [effectiveStartDate, effectiveEndDate] = resolveCdiPeriod(cdiRates, startDate, endDate);
  const quoteResolver = new QuoteResolver(usdRates, MAX_USD_FALLBACK_DAYS, EARLIEST_SUPPORTED_DATE);
  const initialQuote = quoteResolver.lookup(effectiveStartDate);
  const cdiValues = normalizeSeries(cdiRates);

  const timeline = sortedDatesFromMap(cdiValues).filter(
    (currentDate) => effectiveStartDate <= currentDate && currentDate <= effectiveEndDate
  );

  const rows = [];
  let cdiFactor = 1.0;
  for (const currentDate of timeline) {
    const effectiveQuote = quoteResolver.lookup(currentDate);
    const usdVariation = effectiveQuote.value / initialQuote.value - 1;
    const cdiVariation = cdiFactor - 1;
    const usdPercentVariation = (1 + cdiVariation) / (1 + usdVariation) - 1;

    rows.push({
      date: currentDate,
      cdi_accumulated: cdiVariation * 100,
      usd_accumulated: usdVariation * 100,
      usd_percent_variation: usdPercentVariation * 100,
      adjusted_capital: normalizedInitialBrl * cdiFactor,
      usd_brl_quote: effectiveQuote.value
    });

    if (currentDate < effectiveEndDate) {
      cdiFactor *= 1 + cdiValues.get(currentDate) / 100;
    }
  }
  return rows;
}
