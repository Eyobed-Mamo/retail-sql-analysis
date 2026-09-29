-- Top 10% by observed spend, rounded up; customer_id breaks ties reproducibly.
WITH spend AS (
    SELECT customer_id, SUM(revenue_cents) AS revenue_cents
    FROM delivered_order_totals GROUP BY customer_id
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY revenue_cents DESC, customer_id) AS customer_rank,
           COUNT(*) OVER () AS customers FROM spend
)
SELECT COUNT(*) AS purchasing_customers,
       SUM(CASE WHEN customer_rank <= (customers + 9) / 10 THEN 1 ELSE 0 END) AS top_customers,
       ROUND(100.0 * SUM(CASE WHEN customer_rank <= (customers + 9) / 10 THEN revenue_cents ELSE 0 END)
           / NULLIF(SUM(revenue_cents), 0), 2) AS top_decile_revenue_share_pct
FROM ranked;
