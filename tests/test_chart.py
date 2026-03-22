"""Test generate_chart tool — verify all chart types produce valid output files."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_sql_server import generate_chart

PASS = 0
FAIL = 0


def check(name, result_json, expect_error=False):
    global PASS, FAIL
    result = json.loads(result_json)
    if expect_error:
        if "error" in result:
            print(f"  PASS  {name} — expected error: {result['error']}")
            PASS += 1
        else:
            print(f"  FAIL  {name} — expected error but got: {result}")
            FAIL += 1
        return

    if "error" in result:
        print(f"  FAIL  {name} — unexpected error: {result['error']}")
        FAIL += 1
        return

    path = result.get("file_path", "")
    if os.path.isfile(path):
        size = os.path.getsize(path)
        print(f"  PASS  {name} — {result['row_count']} rows, {size:,} bytes → {path}")
        PASS += 1
        # Clean up test file
        os.remove(path)
    else:
        print(f"  FAIL  {name} — file not found: {path}")
        FAIL += 1


# --- Chart type tests ---
print("=== Chart Type Tests ===")

check("bar chart",
      generate_chart(
          sql="SELECT g.Name AS Genre, COUNT(*) AS TrackCount FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.Name ORDER BY TrackCount DESC LIMIT 10",
          chart_type="bar", x_column="Genre", y_column="TrackCount",
          title="Top 10 Genres by Track Count"))

check("barh chart",
      generate_chart(
          sql="SELECT g.Name AS Genre, COUNT(*) AS TrackCount FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.Name ORDER BY TrackCount DESC LIMIT 10",
          chart_type="barh", x_column="Genre", y_column="TrackCount",
          title="Top 10 Genres by Track Count (Horizontal)"))

check("line chart",
      generate_chart(
          sql="SELECT strftime('%Y', InvoiceDate) AS Year, ROUND(SUM(Total), 2) AS Revenue FROM Invoice GROUP BY Year ORDER BY Year",
          chart_type="line", x_column="Year", y_column="Revenue",
          title="Revenue by Year"))

check("pie chart",
      generate_chart(
          sql="SELECT BillingCountry AS Country, ROUND(SUM(Total), 2) AS Revenue FROM Invoice GROUP BY BillingCountry ORDER BY Revenue DESC LIMIT 5",
          chart_type="pie", x_column="Country", y_column="Revenue",
          title="Top 5 Countries by Revenue"))

check("scatter chart",
      generate_chart(
          sql="SELECT Milliseconds / 1000.0 AS DurationSec, Bytes / 1048576.0 AS SizeMB FROM Track WHERE Bytes IS NOT NULL LIMIT 200",
          chart_type="scatter", x_column="DurationSec", y_column="SizeMB",
          title="Track Duration vs File Size"))

# --- Feature tests ---
print("\n=== Feature Tests ===")

check("sort_by_value",
      generate_chart(
          sql="SELECT g.Name AS Genre, COUNT(*) AS TrackCount FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.Name",
          chart_type="bar", x_column="Genre", y_column="TrackCount",
          sort_by_value=True, limit=5, title="Top 5 Genres (sorted + limited)"))

check("pdf output",
      generate_chart(
          sql="SELECT BillingCountry AS Country, COUNT(*) AS InvoiceCount FROM Invoice GROUP BY BillingCountry ORDER BY InvoiceCount DESC LIMIT 8",
          chart_type="bar", x_column="Country", y_column="InvoiceCount",
          output_format="pdf", title="Invoices by Country (PDF)"))

check("custom style",
      generate_chart(
          sql="SELECT strftime('%Y', InvoiceDate) AS Year, COUNT(*) AS Count FROM Invoice GROUP BY Year ORDER BY Year",
          chart_type="line", x_column="Year", y_column="Count",
          style="darkgrid", color_palette="colorblind", title="Invoices per Year (darkgrid + colorblind)"))

# --- Error handling tests ---
print("\n=== Error Handling Tests ===")

check("invalid chart type",
      generate_chart(sql="SELECT 1", chart_type="histogram", x_column="x", y_column="y"),
      expect_error=True)

check("invalid output format",
      generate_chart(sql="SELECT 1 AS x, 2 AS y", chart_type="bar", x_column="x", y_column="y", output_format="svg"),
      expect_error=True)

check("bad SQL",
      generate_chart(sql="SELECT FROM", chart_type="bar", x_column="x", y_column="y"),
      expect_error=True)

check("missing column",
      generate_chart(
          sql="SELECT Name FROM Genre LIMIT 5",
          chart_type="bar", x_column="Name", y_column="NonExistent"),
      expect_error=True)

check("empty result",
      generate_chart(
          sql="SELECT Name, GenreId FROM Genre WHERE GenreId = -999",
          chart_type="bar", x_column="Name", y_column="GenreId"),
      expect_error=True)

# --- Summary ---
print(f"\n{'='*40}")
print(f"Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
if FAIL > 0:
    sys.exit(1)
