# Data dictionary and metric contract

## Source tables

| Table | Grain and key | Fields |
|---|---|---|
| customers | One registered customer; customer_id | signup_date: ISO YYYY-MM-DD; region: fictional US region |
| products | One catalog product; product_id | product_name, category, list_price_cents, unit_cost_cents |
| orders | One order; order_id | customer_id foreign key, order_date ISO YYYY-MM-DD, status |
| order_items | One distinct product within an order; (order_id, product_id) | quantity, historical unit_price_cents, historical unit_cost_cents, discount_cents |

`discount_cents` is a discount on the entire line, not on each unit. Amounts are integer US cents to avoid storing floating-point currency. Conversion to dollars and rounding occur only in display outputs. Product prices are current catalog values; analysis uses historical line prices and costs. In this sample they do not vary over time.

## Metric definitions

- **Revenue:** sum of quantity × historical unit price − line discount for delivered orders only.
- **Product cost (COGS):** sum of quantity × historical unit cost for delivered orders.
- **Gross profit:** revenue minus product cost; this is not net profit.
- **Gross margin:** total gross profit / total revenue. Do not average product margin percentages.
- **Average order value (AOV):** delivered revenue / number of delivered orders.
- **Purchasing customer:** a customer with at least one delivered order in the observation window.
- **Repeat customer rate:** customers with at least two delivered orders / purchasing customers. Multiple orders on the same day count separately. Customers without a delivered order are excluded.
- **Month-over-month growth:** (current month revenue − previous month revenue) / previous month revenue. Missing first comparison and zero denominators return NULL, exported as a blank CSV field.
- **Cohort:** calendar month of the customer's first observed delivered purchase.
- **Month N retention:** distinct cohort customers purchasing in that calendar month / original cohort size. Month 0 is 100%. Customers need not purchase in every intervening month. This is purchase activity retention, not continuous subscription retention or a rolling 30-day measure.
- **Region purchase participation:** registered customers with a delivered purchase / all registered customers in the region. This is not website conversion; there is no session or visitor data.
- **Recency:** days from last delivered order to January 1, 2026. Segment thresholds are illustrative rules, not validated churn predictions.
- **Top decile:** top 10% of purchasing customers by observed revenue, rounded up to a whole customer. Customer ID breaks equal-spend ties.

## Observation and exclusions

The complete observation window is 2024-01-01 through 2025-12-31. Retention shows offsets 0–6 and excludes future months after the window. Cancelled and fully refunded orders contribute no revenue or cost to the sales analyses but remain in the order-outcomes query. There are no partial refunds, refund timestamps, inventory levels, acquisition channels, or operating expenses. Recent registrations have less time to purchase; regional participation and overall repeat rates do not adjust for this.
