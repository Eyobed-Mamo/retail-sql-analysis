"""Rebuild the portfolio using Python's standard library only."""
from pathlib import Path
import csv
import random
import sqlite3
import calendar
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parent
random.seed(42)
for folder in ('sql', 'data', 'results', 'docs'):
    (ROOT / folder).mkdir(exist_ok=True)

schema = '''-- SQLite; monetary amounts are integer USD cents.
PRAGMA foreign_keys = ON;
DROP VIEW IF EXISTS delivered_order_totals;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    signup_date TEXT NOT NULL,
    region TEXT NOT NULL CHECK(region IN ('Northeast','South','Midwest','West'))
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    list_price_cents INTEGER NOT NULL CHECK(list_price_cents > 0),
    unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0)
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('delivered','cancelled','refunded'))
);
CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0),
    unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0),
    discount_cents INTEGER NOT NULL CHECK(discount_cents >= 0 AND discount_cents <= quantity * unit_price_cents),
    PRIMARY KEY (order_id, product_id)
);
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
CREATE INDEX idx_orders_status_date ON orders(status, order_date);
CREATE INDEX idx_items_product ON order_items(product_id);

-- One row per delivered order prevents counting an order once per line item.
CREATE VIEW delivered_order_totals AS
SELECT o.order_id, o.customer_id, o.order_date,
       SUM(i.quantity * i.unit_price_cents - i.discount_cents) AS revenue_cents,
       SUM(i.quantity * i.unit_cost_cents) AS cogs_cents
FROM orders o
JOIN order_items i ON i.order_id = o.order_id
WHERE o.status = 'delivered'
GROUP BY o.order_id, o.customer_id, o.order_date;
'''
(ROOT / 'sql/01_schema.sql').write_text(schema, encoding='utf-8')

queries = {
'01_overall_kpis': '''-- Revenue excludes cancellations and full refunds; AOV uses orders, not items.
SELECT COUNT(*) AS delivered_orders,
       COUNT(DISTINCT customer_id) AS purchasing_customers,
       ROUND(SUM(revenue_cents) / 100.0, 2) AS revenue_usd,
       ROUND(AVG(revenue_cents) / 100.0, 2) AS average_order_value_usd,
       ROUND(SUM(revenue_cents - cogs_cents) / 100.0, 2) AS gross_profit_usd,
       ROUND(100.0 * SUM(revenue_cents - cogs_cents) / NULLIF(SUM(revenue_cents), 0), 2) AS gross_margin_pct
FROM delivered_order_totals;''',
'02_monthly_growth': '''-- Calendar spine retains months with no sales; LAG finds the previous month.
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
FROM previous ORDER BY month;''',
'03_category_profitability': '''-- Historical prices and costs come from each order line.
SELECT p.category, SUM(i.quantity) AS units_sold,
       ROUND(SUM(i.quantity * i.unit_price_cents - i.discount_cents) / 100.0, 2) AS revenue_usd,
       ROUND(SUM(i.quantity * (i.unit_price_cents - i.unit_cost_cents) - i.discount_cents) / 100.0, 2) AS gross_profit_usd,
       ROUND(100.0 * SUM(i.quantity * (i.unit_price_cents - i.unit_cost_cents) - i.discount_cents)
           / NULLIF(SUM(i.quantity * i.unit_price_cents - i.discount_cents), 0), 2) AS gross_margin_pct
FROM order_items i JOIN orders o ON o.order_id = i.order_id
JOIN products p ON p.product_id = i.product_id
WHERE o.status = 'delivered'
GROUP BY p.category ORDER BY gross_profit_usd DESC;''',
'04_top_products': '''-- DENSE_RANK includes ties: a category can return more than three products.
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
FROM ranked WHERE category_rank <= 3 ORDER BY category, category_rank, product_id;''',
'05_repeat_purchase': '''-- This is an observed repeat rate, not a time-normalized retention rate.
WITH customer_orders AS (
    SELECT customer_id, COUNT(*) AS orders FROM delivered_order_totals GROUP BY customer_id
)
SELECT COUNT(*) AS purchasing_customers,
       SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN orders >= 2 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS repeat_customer_pct
FROM customer_orders;''',
'06_customer_segments': '''-- Transparent rule-based segments, as of 2026-01-01.
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
FROM segments GROUP BY segment ORDER BY historical_revenue_usd DESC;''',
'07_cohort_retention': '''-- Monthly purchase retention. First observed delivered order defines cohort.
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
ORDER BY s.cohort, x.month_offset;''',
'08_regional_performance': '''-- Customers with no delivered purchase remain in the denominator.
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
FROM customer_metrics GROUP BY region ORDER BY revenue_usd DESC;''',
'09_order_outcomes': '''-- Operational outcomes use ALL orders, including non-revenue orders.
SELECT status, COUNT(*) AS orders,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 2) AS order_share_pct
FROM orders GROUP BY status ORDER BY orders DESC;''',
'10_customer_concentration': '''-- Top 10% by observed spend, rounded up; customer_id breaks ties reproducibly.
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
FROM ranked;'''
}

catalog = {
 'Electronics': [('Wireless Headphones', 8900, 5400), ('Portable Speaker', 6500, 3900), ('USB-C Hub', 4500, 2200), ('Webcam', 7200, 4200), ('Wireless Mouse', 3200, 1500)],
 'Home': [('Desk Lamp', 4200, 1900), ('Throw Blanket', 3800, 1600), ('Storage Set', 2900, 1200), ('Coffee Press', 3500, 1500), ('Wall Clock', 2700, 1100)],
 'Fitness': [('Yoga Mat', 3400, 1300), ('Resistance Bands', 2400, 800), ('Water Bottle', 2200, 700), ('Foam Roller', 3000, 1100), ('Jump Rope', 1800, 600)],
 'Office': [('Notebook Set', 1600, 500), ('Desk Organizer', 2500, 900), ('Laptop Stand', 4800, 2100), ('Pen Set', 1200, 300), ('Monitor Riser', 3900, 1700)]
}
products = [(idx, name, category, price, cost) for idx, (category, name, price, cost) in enumerate(
    ((cat, *p) for cat, values in catalog.items() for p in values), 1)]
start = date(2024, 1, 1)
customers = [(i, (start + timedelta(days=random.randrange(650))).isoformat(),
              random.choice(['Northeast', 'South', 'Midwest', 'West'])) for i in range(1, 1201)]
customers[0] = (customers[0][0], start.isoformat(), customers[0][2])
weights = {c[0]: random.choices([1, 3, 9], weights=[65, 25, 10])[0] for c in customers}
orders, items = [], []
for month_index in range(24):
    year, month = 2024 + month_index // 12, month_index % 12 + 1
    # Deliberately modeled growth and holiday seasonality; not real market evidence.
    order_count = int((100 + month_index * 9) * (1.6 if month in (11, 12) else 1))
    for _ in range(order_count):
        day = date(year, month, random.randint(1, calendar.monthrange(year, month)[1])).isoformat()
        eligible = [c for c in customers if c[1] <= day]
        customer = random.choices(eligible, weights=[weights[c[0]] for c in eligible])[0]
        status = random.choices(['delivered', 'cancelled', 'refunded'], [88, 7, 5])[0]
        oid = len(orders) + 1
        orders.append((oid, customer[0], day, status))
        for pid, name, category, price, cost in random.sample(products, random.randint(1, 4)):
            qty = random.choices([1, 2, 3], [75, 20, 5])[0]
            discount = qty * price * random.choices([0, 10, 20], [65, 25, 10])[0] // 100
            items.append((oid, pid, qty, price, cost, discount))

db = sqlite3.connect(ROOT / 'retail.db')
db.executescript(schema)
tables = {
    'customers': (['customer_id', 'signup_date', 'region'], customers),
    'products': (['product_id', 'product_name', 'category', 'list_price_cents', 'unit_cost_cents'], products),
    'orders': (['order_id', 'customer_id', 'order_date', 'status'], orders),
    'order_items': (['order_id', 'product_id', 'quantity', 'unit_price_cents', 'unit_cost_cents', 'discount_cents'], items)
}
for table, (headers, rows) in tables.items():
    db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' for _ in headers)})", rows)
    with (ROOT / f'data/{table}.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        writer.writerow(headers)
        writer.writerows(rows)
db.commit()
results = {}
for name, query in queries.items():
    (ROOT / f'sql/{name}_analysis.sql').write_text(query + '\n', encoding='utf-8')
    cursor = db.execute(query)
    headers = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    results[name] = [dict(zip(headers, row)) for row in rows]
    with (ROOT / f'results/{name}.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        writer.writerow(headers)
        writer.writerows(rows)

checks = {
 'database_integrity': db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok',
 'foreign_keys': not db.execute('PRAGMA foreign_key_check').fetchall(),
 'no_orders_before_signup': db.execute('SELECT COUNT(*) FROM orders o JOIN customers c USING(customer_id) WHERE o.order_date < c.signup_date').fetchone()[0] == 0,
 'no_empty_orders': db.execute('SELECT COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id=o.order_id)').fetchone()[0] == 0,
 'all_24_months': len(results['02_monthly_growth']) == 24,
 'cohort_month_zero_100_percent': all(r['retention_pct'] == 100 for r in results['07_cohort_retention'] if r['month_offset'] == 0),
 'retention_bounds': all(0 <= r['retention_pct'] <= 100 for r in results['07_cohort_retention']),
 'no_future_retention': all(int(r['cohort'][:4]) * 12 + int(r['cohort'][5:]) + r['month_offset'] <= 2025 * 12 + 12 for r in results['07_cohort_retention'])
}
# Independently reconcile SQL revenue and order counts with the generated source records.
delivered = {o[0] for o in orders if o[3] == 'delivered'}
source_revenue = sum(i[2] * i[3] - i[5] for i in items if i[0] in delivered)
sql_revenue = db.execute('SELECT SUM(revenue_cents) FROM delivered_order_totals').fetchone()[0]
checks['source_revenue_reconciliation'] = source_revenue == sql_revenue
checks['delivered_order_count'] = len(delivered) == results['01_overall_kpis'][0]['delivered_orders']
checks['category_reconciliation'] = round(sum(r['revenue_usd'] for r in results['03_category_profitability']), 2) == round(source_revenue / 100, 2)
checks['monthly_reconciliation'] = round(sum(r['revenue_usd'] for r in results['02_monthly_growth']), 2) == round(source_revenue / 100, 2)
(ROOT / 'results/validation.txt').write_text('\n'.join(f"{'PASS' if passed else 'FAIL'}: {name}" for name, passed in checks.items()) + '\n', encoding='utf-8')
assert all(checks.values()), checks

kpi = results['01_overall_kpis'][0]
repeat = results['05_repeat_purchase'][0]
category = results['03_category_profitability'][0]
peak = max(results['02_monthly_growth'], key=lambda r: r['revenue_usd'])
concentration = results['10_customer_concentration'][0]
findings = f'''# Findings from the synthetic dataset

These are demonstration results, not real company performance. The generator deliberately creates growth, holiday seasonality, and unequal purchase propensity. Recommendations below are hypotheses for a fictional business, not measured impact.

| Metric | Result |
|---|---:|
| Delivered orders | {kpi['delivered_orders']:,} |
| Purchasing customers | {kpi['purchasing_customers']:,} |
| Revenue after discounts | ${kpi['revenue_usd']:,.2f} |
| Average order value | ${kpi['average_order_value_usd']:,.2f} |
| Gross profit | ${kpi['gross_profit_usd']:,.2f} |
| Gross margin | {kpi['gross_margin_pct']}% |
| Observed repeat customer rate | {repeat['repeat_customer_pct']}% |

## Decisions this analysis could support

1. **Product mix:** {category['category']} contributes the highest gross profit (${category['gross_profit_usd']:,.2f}). Compare category margin as well as revenue before prioritizing promotions. Validate demand, inventory, and acquisition cost before changing spend. Evidence: `results/03_category_profitability.csv`.
2. **Seasonal planning:** {peak['month']} is the highest-revenue month (${peak['revenue_usd']:,.2f}). In a real business, compare more years and promotion calendars before planning inventory around this pattern. Seasonality here is intentionally generated. Evidence: `results/02_monthly_growth.csv`.
3. **Customer concentration:** The top {concentration['top_customers']} purchasers contribute {concentration['top_decile_revenue_share_pct']}% of revenue. A fictional retention program could focus on these customers, with a randomized holdout to measure incremental value. Evidence: `results/10_customer_concentration.csv`.
4. **Repeat purchasing:** {repeat['repeat_customers']:,} of {repeat['purchasing_customers']:,} purchasers bought at least twice. Use cohort retention to compare customers with equal observation periods; this overall repeat rate favors earlier customers. Evidence: `results/05_repeat_purchase.csv` and `results/07_cohort_retention.csv`.

## Boundaries

Gross profit subtracts product cost only. It excludes shipping, advertising, payroll, payment fees, taxes, and return handling. Refunded orders are fully excluded; partial refunds are not modeled. Status is a final snapshot, not an event history, so this is not an accounting revenue-recognition report. First observed purchase may differ from true first purchase in a real truncated dataset. No causal claims or real commercial improvements are established.
'''
(ROOT / 'docs/findings.md').write_text(findings, encoding='utf-8')
db.close()
print(f'Built {len(customers):,} customers, {len(products)} products, {len(orders):,} orders, {len(items):,} order lines.')
print(f'Executed {len(queries)} analyses; {len(checks)} validation checks passed.')
print(findings)
