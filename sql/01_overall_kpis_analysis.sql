-- Revenue excludes cancellations and full refunds; AOV uses orders, not items.
SELECT COUNT(*) AS delivered_orders,
       COUNT(DISTINCT customer_id) AS purchasing_customers,
       ROUND(SUM(revenue_cents) / 100.0, 2) AS revenue_usd,
       ROUND(AVG(revenue_cents) / 100.0, 2) AS average_order_value_usd,
       ROUND(SUM(revenue_cents - cogs_cents) / 100.0, 2) AS gross_profit_usd,
       ROUND(100.0 * SUM(revenue_cents - cogs_cents) / NULLIF(SUM(revenue_cents), 0), 2) AS gross_margin_pct
FROM delivered_order_totals;
