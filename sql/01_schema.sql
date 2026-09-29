-- SQLite; monetary amounts are integer USD cents.
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
