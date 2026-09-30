# Findings from the synthetic dataset

These are demonstration results, not real company performance. The generator deliberately creates growth, holiday seasonality, and unequal purchase propensity. Recommendations below are hypotheses for a fictional business, not measured impact.

| Metric | Result |
|---|---:|
| Delivered orders | 4,827 |
| Purchasing customers | 976 |
| Revenue after discounts | $559,427.20 |
| Average order value | $115.90 |
| Gross profit | $286,925.20 |
| Gross margin | 51.29% |
| Observed repeat customer rate | 76.74% |

## Decisions this analysis could support

1. **Product mix:** Electronics contributes the highest gross profit ($92,765.80). Compare category margin as well as revenue before prioritizing promotions. Validate demand, inventory, and acquisition cost before changing spend. Evidence: `results/03_category_profitability.csv`.
2. **Seasonal planning:** 2025-11 is the highest-revenue month ($51,623.60). In a real business, compare more years and promotion calendars before planning inventory around this pattern. Seasonality here is intentionally generated. Evidence: `results/02_monthly_growth.csv`.
3. **Customer concentration:** The top 98 purchasers contribute 39.47% of revenue. A fictional retention program could focus on these customers, with a randomized holdout to measure incremental value. Evidence: `results/10_customer_concentration.csv`.
4. **Repeat purchasing:** 749 of 976 purchasers bought at least twice. Use cohort retention to compare customers with equal observation periods; this overall repeat rate favors earlier customers. Evidence: `results/05_repeat_purchase.csv` and `results/07_cohort_retention.csv`.

## Boundaries

Gross profit subtracts product cost only. It excludes shipping, advertising, payroll, payment fees, taxes, and return handling. Refunded orders are fully excluded; partial refunds are not modeled. Status is a final snapshot, not an event history, so this is not an accounting revenue-recognition report. First observed purchase may differ from true first purchase in a real truncated dataset. No causal claims or real commercial improvements are established.
