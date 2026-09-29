-- This is an observed repeat rate, not a time-normalized retention rate.
WITH customer_orders AS (
    SELECT customer_id, COUNT(*) AS orders FROM delivered_order_totals GROUP BY customer_id
)
SELECT COUNT(*) AS purchasing_customers,
       SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS repeat_customer_pct
FROM customer_orders;
