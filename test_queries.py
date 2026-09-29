"""Small independent fixtures test metric semantics, not just generated totals."""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parent

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.executescript((ROOT / 'sql/01_schema.sql').read_text())
        self.db.executemany('INSERT INTO customers VALUES (?, ?, ?)', [
            (1, '2024-01-01', 'West'), (2, '2024-01-01', 'West'),
            (3, '2025-12-01', 'South'), (4, '2024-01-01', 'West')])
        self.db.executemany('INSERT INTO products VALUES (?, ?, ?, ?, ?)', [
            (1, 'A', 'Home', 1000, 400), (2, 'B', 'Home', 1000, 400)])
        self.db.executemany('INSERT INTO orders VALUES (?, ?, ?, ?)', [
            (1, 1, '2024-01-05', 'delivered'), (2, 1, '2024-02-05', 'delivered'),
            (3, 1, '2024-02-06', 'delivered'), (4, 2, '2024-01-10', 'delivered'),
            (5, 2, '2024-02-10', 'refunded'), (6, 2, '2024-02-11', 'cancelled'),
            (7, 3, '2025-12-15', 'delivered')])
        self.db.executemany('INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)', [
            (1, 1, 2, 1000, 400, 200), (1, 2, 1, 1000, 400, 0),
            (2, 1, 1, 1000, 400, 0), (3, 1, 1, 1000, 400, 0),
            (4, 1, 1, 1000, 400, 0), (5, 1, 1, 9000, 400, 0),
            (6, 1, 1, 9000, 400, 0), (7, 1, 1, 1000, 400, 0)])

    def tearDown(self):
        self.db.close()

    def query(self, prefix):
        path = next((ROOT / 'sql').glob(prefix + '_*_analysis.sql'))
        return [dict(row) for row in self.db.execute(path.read_text())]

    def test_order_grain_discount_and_status_exclusions(self):
        row = self.query('01')[0]
        self.assertEqual(row['delivered_orders'], 5)
        self.assertEqual(row['revenue_usd'], 68)
        self.assertEqual(row['average_order_value_usd'], 13.6)
        self.assertEqual(row['gross_profit_usd'], 40)

    def test_zero_month_and_undefined_growth(self):
        rows = {r['month']: r for r in self.query('02')}
        self.assertEqual(rows['2024-03']['revenue_usd'], 0)
        self.assertEqual(rows['2024-03']['mom_growth_pct'], -100)
        self.assertIsNone(rows['2024-04']['mom_growth_pct'])

    def test_repeat_rate_denominator(self):
        row = self.query('05')[0]
        self.assertEqual(row['purchasing_customers'], 3)
        self.assertEqual(row['repeat_customers'], 1)
        self.assertEqual(row['repeat_customer_pct'], 33.33)

    def test_cohort_deduplication_zero_and_future_months(self):
        rows = {(r['cohort'], r['month_offset']): r for r in self.query('07')}
        self.assertEqual(rows[('2024-01', 1)]['retention_pct'], 50)
        self.assertEqual(rows[('2024-01', 2)]['retention_pct'], 0)
        self.assertEqual(rows[('2025-12', 0)]['retention_pct'], 100)
        self.assertNotIn(('2025-12', 1), rows)

    def test_nonpurchasers_remain_in_regional_denominator(self):
        row = next(r for r in self.query('08') if r['region'] == 'West')
        self.assertEqual(row['registered_customers'], 3)
        self.assertEqual(row['purchase_participation_pct'], 66.67)

    def test_small_top_decile_rounds_up(self):
        row = self.query('10')[0]
        self.assertEqual(row['top_customers'], 1)
        self.assertEqual(row['top_decile_revenue_share_pct'], 70.59)

if __name__ == '__main__':
    unittest.main(verbosity=2)
