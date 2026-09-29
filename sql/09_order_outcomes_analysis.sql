-- Operational outcomes use ALL orders, including non-revenue orders.
SELECT status, COUNT(*) AS orders,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 2) AS order_share_pct
FROM orders GROUP BY status ORDER BY orders DESC;
