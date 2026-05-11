import {
  BUSINESS_DAYS_PER_MONTH,
  BUSINESS_DAYS_PER_YEAR,
  calculateEquivalentRatePercentage
} from "./calculations.js";

export function calculateUsdBrlVariationPercentage(result) {
  return (result.final_usdbrl / result.initial_usdbrl - 1) * 100;
}

export function buildResultPresentation(result) {
  const usdBrlVariationPercentage = calculateUsdBrlVariationPercentage(result);

  return {
    brl: {
      title: "Capital em BRL pelo CDI",
      rows: [
        { label: "Valor inicial em BRL", value: result.initial_brl, format: "brl" },
        { label: "Valor final em BRL com CDI", value: result.final_brl, format: "brl" },
        { label: "CDI acumulado no periodo", value: result.cdi_percentage, format: "percent" },
        {
          label: "CDI equivalente mensal",
          value: calculateEquivalentRatePercentage(
            result.cdi_percentage,
            result.cdi_days_used,
            BUSINESS_DAYS_PER_MONTH
          ),
          format: "percent"
        },
        {
          label: "CDI equivalente anual",
          value: calculateEquivalentRatePercentage(
            result.cdi_percentage,
            result.cdi_days_used,
            BUSINESS_DAYS_PER_YEAR
          ),
          format: "percent"
        },
        { label: "Dias uteis de CDI usados", value: result.cdi_days_used, format: "integer" }
      ]
    },
    exchange: {
      title: "Cambio USD/BRL",
      rows: [
        { label: "PTAX venda inicial", value: result.initial_usdbrl, format: "quote" },
        { label: "PTAX venda final", value: result.final_usdbrl, format: "quote" },
        {
          label: "Variacao acumulada do USD/BRL",
          value: usdBrlVariationPercentage,
          format: "percent"
        },
        {
          label: "USD/BRL equivalente mensal",
          value: calculateEquivalentRatePercentage(
            usdBrlVariationPercentage,
            result.cdi_days_used,
            BUSINESS_DAYS_PER_MONTH
          ),
          format: "percent"
        },
        {
          label: "USD/BRL equivalente anual",
          value: calculateEquivalentRatePercentage(
            usdBrlVariationPercentage,
            result.cdi_days_used,
            BUSINESS_DAYS_PER_YEAR
          ),
          format: "percent"
        },
        { label: "Data efetiva inicial da PTAX", value: result.initial_fx_date, format: "date" },
        { label: "Data efetiva final da PTAX", value: result.final_fx_date, format: "date" }
      ]
    },
    usd: {
      title: "Posicao equivalente em USD",
      rows: [
        { label: "Valor inicial convertido para USD", value: result.initial_usd, format: "usd" },
        { label: "Valor final em BRL convertido para USD", value: result.final_usd_with_cdi, format: "usd" },
        {
          label: "Variacao acumulada da posicao em USD",
          value: result.real_usd_return_percentage,
          format: "percent"
        },
        {
          label: "Variacao equivalente mensal em USD",
          value: calculateEquivalentRatePercentage(
            result.real_usd_return_percentage,
            result.cdi_days_used,
            BUSINESS_DAYS_PER_MONTH
          ),
          format: "percent"
        },
        {
          label: "Variacao equivalente anual em USD",
          value: calculateEquivalentRatePercentage(
            result.real_usd_return_percentage,
            result.cdi_days_used,
            BUSINESS_DAYS_PER_YEAR
          ),
          format: "percent"
        }
      ]
    }
  };
}
