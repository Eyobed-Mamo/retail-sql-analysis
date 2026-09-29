"""Execute a single read-only SQL analysis and write its output to stdout as CSV."""
import csv
import sqlite3
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if len(sys.argv) != 2:
    raise SystemExit('Usage: python run_query.py sql/02_monthly_growth_analysis.sql')
connection = sqlite3.connect((root / 'retail.db').as_uri() + '?mode=ro', uri=True)
connection.execute('PRAGMA query_only = ON')
cursor = connection.execute(Path(sys.argv[1]).read_text(encoding='utf-8'))
writer = csv.writer(sys.stdout)
writer.writerow([c[0] for c in cursor.description])
writer.writerows(cursor)
connection.close()
