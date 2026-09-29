-- Calendar spine retains months with no sales; LAG finds the previous month.
WITH RECURSIVE months(month) AS (
    SELECT '2024-01'
    UNION ALL SELECT strftime('%Y-%m', date(month || '-01', '+1 month'))
    FROM months WHERE month < '2025-12'
), monthly AS (
    SELECT m.month, COUNT(d.order_id) AS orders,
           COALESCE(SUM(d.revenue_cents), 0) AS revenue_cents
    FROM months m LEFT JOIN delivered_order_totals d
      ON substr(d.order_date, 1, 7) = m.month
    GROUP BY m.month
), previous AS (
    SELECT *, LAG(revenue_cents) OVER (ORDER BY month) AS previous_revenue
    FROM monthly
)
SELECT month, orders, ROUND(revenue_cents / 100.0, 2) AS revenue_usd,
       ROUND(100.0 * (revenue_cents - previous_revenue) / NULLIF(previous_revenue, 0), 2) AS mom_growth_pct
FROM previous ORDER BY month;
