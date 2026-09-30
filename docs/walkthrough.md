# Understand the project step by step

## 1. The story

Imagine an online shop owner asking: “What sells, what makes money, and do customers come back?” The project turns individual purchases into answers to those questions.

## 2. Understand the four tables

A customer places an order. An order contains line items. Each line item points to a product. For example, one order could include two water bottles and one yoga mat. That is one order, two line items, and three units. These counts are different, and mixing them up is a common analytical mistake.

## 3. Calculate revenue correctly

```sql
SELECT order_id, product_id,
       (quantity * unit_price_cents - discount_cents) / 100.0 AS line_revenue_usd
FROM order_items
LIMIT 10;
```

Two $22 bottles with a $4.40 total line discount produce $39.60 revenue. The database stores 2200 and 440 cents. You subtract the discount once because it belongs to the whole line.

## 4. Connect the tables

```sql
SELECT o.order_id, p.product_name, i.quantity
FROM orders o
JOIN order_items i ON i.order_id = o.order_id
JOIN products p ON p.product_id = i.product_id
WHERE o.status = 'delivered'
LIMIT 10;
```

`JOIN` connects matching IDs. `WHERE` keeps the rows relevant to the question. An order with three different products appears three times here. That is correct for a product analysis, but counting these rows would overstate the order count.

## 5. Summarize at the right level

The `delivered_order_totals` view first adds all line revenues within each order. A view is a saved query you can use like a table. It has one row per delivered order, making this AOV query safe:

```sql
SELECT ROUND(AVG(revenue_cents) / 100.0, 2) AS average_order_value_usd
FROM delivered_order_totals;
```

Open `sql/01_overall_kpis_analysis.sql` next. `SUM` adds values, `COUNT` counts rows, and `COUNT(DISTINCT customer_id)` counts each purchasing customer once.

## 6. Learn CTEs and window functions

A CTE, introduced by `WITH`, names an intermediate query so a long analysis can be read in steps. In monthly growth, the steps are: create all months, total each month's revenue, fetch the previous month's revenue, and calculate growth.

`LAG` looks at the prior row without collapsing rows. If last month's revenue was $10,000 and this month's is $12,000, growth is (12,000 − 10,000) / 10,000 = 20%. `NULLIF` prevents division by zero; an undefined result stays blank rather than being reported as 0%.

`DENSE_RANK` in the product query ranks products separately within each category. Equal revenues get the same rank.

## 7. Understand retention

If 100 customers first buy in January and 20 of those customers buy in February, January's month-1 retention is 20%. If someone buys twice in February, they still count as one returning customer.

The cohort query makes a grid of cohorts and month offsets, then attaches purchase activity. That is why a fully observed month with no returning customers appears as 0%, while a future month does not appear at all. December 2025 customers have no observable month-1 result in this dataset.

## 8. Practice explaining your work

Try these before adding the project to a résumé:

1. Explain why cancelled and refunded orders are excluded from sales KPIs.
2. Explain why averaging line-item revenue is not AOV.
3. Change the product ranking from revenue to gross profit in a copy of the query.
4. Explain why 80% overall repeat purchase does not mean 80% monthly retention.
5. Identify one reason synthetic results cannot justify real marketing spending.

You are ready to discuss this project when you can describe the business question, table grain, metric definition, query approach, findings, and limitations without reading a script.
