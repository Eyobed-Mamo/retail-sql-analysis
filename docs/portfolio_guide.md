# Presenting this project

## Before posting

Read the walkthrough, run at least one query, and make one change you can explain. Publish this as a personal learning project using synthetic data. Do not describe it as paid employment, real client work, or evidence of increased company revenue.

## Résumé wording after you have reviewed and run it

**Retail Sales & Customer Retention Analysis | SQL, SQLite, Python**

- Completed an AI-assisted SQL portfolio project using a four-table synthetic retail database; reviewed ten analyses covering sales growth, product profitability, customer segmentation, and cohort retention.
- Applied joins, CTEs, and window functions to calculate documented business metrics, with revenue reconciliation and data-quality checks.

Use the second bullet only once you can run, modify, and explain those techniques. Add actual dataset counts from the build output if useful. Do not claim that the recommendations produced commercial improvements.

## LinkedIn post after your review

I completed an AI-assisted SQL portfolio project exploring sales and customer retention for a fictional online retailer.

Using synthetic data in SQLite, the project examines monthly revenue, category profitability, repeat purchases, and customer cohorts. It includes annotated SQL, a reproducible database, query outputs, and validation checks.

One lesson from the project: getting the metric definition and table grain right matters as much as writing the SQL. Counting order lines as orders can distort average order value, and recent customer cohorts should not be judged on months that have not happened yet.

The data is simulated, so the results demonstrate analytical methods rather than real business impact.

Repository: [add your GitHub repository link]

## Interview explanation

“This is an AI-assisted personal project using synthetic retail data. I studied how the four tables connect and how the queries measure revenue and returning customers. The main design choice is calculating order totals before order-level KPIs, which avoids duplicating orders after joins. Cohort retention counts distinct customers and excludes future observation months. The results are illustrative; real recommendations would require real data and further validation.”

Adapt this explanation to what you have actually learned and changed. A useful next step is to add your own analysis and explain why you chose its metric definition.
