-- Transparent rule-based segments, as of 2026-01-01.
WITH customer_metrics AS (
    SELECT customer_id, COUNT(*) AS order_count,
           SUM(revenue_cents) AS spend_cents,
           CAST(julianday('2026-01-01') - julianday(MAX(order_date)) AS INTEGER) AS recency_days
    FROM delivered_order_totals GROUP BY customer_id
), segments AS (
    SELECT *, CASE
      WHEN recency_days <= 90 AND order_count >= 3 THEN 'Active repeat'
      WHEN recency_days > 180 AND order_count >= 2 THEN 'Lapsed repeat'
      WHEN order_count = 1 THEN 'One-time'
      ELSE 'Other repeat' END AS segment
    FROM customer_metrics
)
SELECT segment, COUNT(*) AS customers,
       ROUND(SUM(spend_cents) / 100.0, 2) AS historical_revenue_usd,
       ROUND(AVG(spend_cents) / 100.0, 2) AS average_customer_spend_usd
FROM segments GROUP BY segment ORDER BY historical_revenue_usd DESC;
