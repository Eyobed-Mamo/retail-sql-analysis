-- Customers with no delivered purchase remain in the denominator.
WITH customer_metrics AS (
    SELECT c.customer_id, c.region, COUNT(d.order_id) AS orders,
           COALESCE(SUM(d.revenue_cents), 0) AS revenue_cents
    FROM customers c LEFT JOIN delivered_order_totals d ON d.customer_id = c.customer_id
    GROUP BY c.customer_id, c.region
)
SELECT region, COUNT(*) AS registered_customers,
       SUM(CASE WHEN orders > 0 THEN 1 ELSE 0 END) AS purchasing_customers,
       ROUND(100.0 * SUM(CASE WHEN orders > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS purchase_participation_pct,
       ROUND(SUM(revenue_cents) / 100.0, 2) AS revenue_usd
FROM customer_metrics GROUP BY region ORDER BY revenue_usd DESC;
