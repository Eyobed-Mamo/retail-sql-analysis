-- Historical prices and costs come from each order line.
SELECT p.category, SUM(i.quantity) AS units_sold,
       ROUND(SUM(i.quantity * i.unit_price_cents - i.discount_cents) / 100.0, 2) AS revenue_usd,
       ROUND(SUM(i.quantity * (i.unit_price_cents - i.unit_cost_cents) - i.discount_cents) / 100.0, 2) AS gross_profit_usd,
       ROUND(100.0 * SUM(i.quantity * (i.unit_price_cents - i.unit_cost_cents) - i.discount_cents)
           / NULLIF(SUM(i.quantity * i.unit_price_cents - i.discount_cents), 0), 2) AS gross_margin_pct
FROM order_items i JOIN orders o ON o.order_id = i.order_id
JOIN products p ON p.product_id = i.product_id
WHERE o.status = 'delivered'
GROUP BY p.category ORDER BY gross_profit_usd DESC;
