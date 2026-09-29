-- Monthly purchase retention. First observed delivered order defines cohort.
-- Missing future months are excluded, while observed months without returns show 0%.
WITH RECURSIVE offsets(month_offset) AS (
    SELECT 0 UNION ALL SELECT month_offset + 1 FROM offsets WHERE month_offset < 6
), first_purchase AS (
    SELECT customer_id, MIN(substr(order_date, 1, 7)) AS cohort
    FROM delivered_order_totals GROUP BY customer_id
), sizes AS (
    SELECT cohort, COUNT(*) AS cohort_customers FROM first_purchase GROUP BY cohort
), activity AS (
    SELECT DISTINCT f.customer_id, f.cohort,
       (CAST(strftime('%Y', d.order_date) AS INTEGER) - CAST(substr(f.cohort, 1, 4) AS INTEGER)) * 12
       + CAST(strftime('%m', d.order_date) AS INTEGER) - CAST(substr(f.cohort, 6, 2) AS INTEGER) AS month_offset
    FROM first_purchase f JOIN delivered_order_totals d ON d.customer_id = f.customer_id
)
SELECT s.cohort, x.month_offset, s.cohort_customers,
       COUNT(a.customer_id) AS active_customers,
       ROUND(100.0 * COUNT(a.customer_id) / s.cohort_customers, 2) AS retention_pct
FROM sizes s CROSS JOIN offsets x LEFT JOIN activity a
  ON a.cohort = s.cohort AND a.month_offset = x.month_offset
WHERE date(s.cohort || '-01', '+' || x.month_offset || ' months') <= '2025-12-01'
GROUP BY s.cohort, x.month_offset, s.cohort_customers
ORDER BY s.cohort, x.month_offset;
