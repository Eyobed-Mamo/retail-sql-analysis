-- DENSE_RANK includes ties: a category can return more than three products.
WITH sales AS (
    SELECT p.product_id, p.product_name, p.category,
           SUM(i.quantity * i.unit_price_cents - i.discount_cents) AS revenue_cents
    FROM products p JOIN order_items i ON i.product_id = p.product_id
    JOIN orders o ON o.order_id = i.order_id
    WHERE o.status = 'delivered'
    GROUP BY p.product_id, p.product_name, p.category
), ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY category ORDER BY revenue_cents DESC) AS category_rank
    FROM sales
)
SELECT category, category_rank, product_name, ROUND(revenue_cents / 100.0, 2) AS revenue_usd
FROM ranked WHERE category_rank <= 3 ORDER BY category, category_rank, product_id;
