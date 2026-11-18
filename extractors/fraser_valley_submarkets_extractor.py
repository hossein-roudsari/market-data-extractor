import os
import pymupdf
import pandas as pd
import re
from collections import defaultdict

from extractors.registry import register_extractor

submarkets = ["Fraser Valley Board", "Surrey", "Abbotsford", "Langley", "Mission"]

# Row map for master sheet
row_mapping = {
    "benchmark_price": 0,
    "benchmark_pct_change": 3,
    "detached_avg_price_last_year": 10,
    "detached_avg_price_this_year": 12,
    "detached_sales_last_year": 15,
    "detached_sales_this_year": 17,
    "townhouse_avg_price_last_year": 23,
    "townhouse_avg_price_this_year": 25,
    "townhouse_sales_last_year": 28,
    "townhouse_sales_this_year": 30,
    "apartment_avg_price_last_year": 36,
    "apartment_avg_price_this_year": 38,
    "apartment_sales_last_year": 41,
    "apartment_sales_this_year": 43,
    }

# Map page indices
market_page_map = {
    "Fraser Valley Board": 0,
    "Abbotsford": 0,
    "Mission": 0,
    "Langley": 1,
    "Surrey": 2,
    }

def group_words_into_lines(words, y_tolerance=2):
    lines = defaultdict(list)
    for w in words:
        x0, y0, x1, y1, text, *_ = w
        y_key = round(y0 / y_tolerance)
        lines[y_key].append((x0, text))
    sorted_lines = []
    for y in sorted(lines.keys()):
        line_words = sorted(lines[y], key=lambda x: x[0])
        line_text = " ".join(word for _, word in line_words)
        sorted_lines.append(line_text)
    return sorted_lines

# Extract all sales and average prices from submarket summary tables
def extract_table_metrics(page_lines, market_name):
    if market_name == "Fraser Valley Board":
        market_name = "All Areas Combined"
    # returns { category: value }
    metrics = {}
    start_idx = None
    for i, line in enumerate(page_lines):
        if market_name.lower() in line.lower():
            start_idx = i
            break
    if start_idx is None:
        return None

    # Extract lines until next header or blank
    table_lines = []
    for line in page_lines[start_idx + 1:]:
        if any(header in line.lower() for header in ["sales", "average price"]):
            table_lines.append(line)
        # elif len(line.strip()) == 0 or re.match(r"^\s*$", line):
        elif 'detached' in line.lower():
            break
    if not table_lines:
        return None

    # Parse sales rows
    for line in table_lines:
        if "sales" in line.lower():
            parts = line.split()
            metrics["detached_sales_this_year"] = int(parts[1].replace(",", ""))
            metrics["detached_sales_last_year"] = int(parts[2].replace(",", ""))
            metrics["townhouse_sales_this_year"] = int(parts[6].replace(",", ""))
            metrics["townhouse_sales_last_year"] = int(parts[7].replace(",", ""))
            metrics["apartment_sales_this_year"] = int(parts[11].replace(",", ""))
            metrics["apartment_sales_last_year"] = int(parts[12].replace(",", ""))
        if "average price" in line.lower():
            line = line.replace("$", "")
            parts = line.split()
            metrics["detached_avg_price_this_year"] = int(parts[2].replace(",", ""))
            metrics["detached_avg_price_last_year"] = int(parts[3].replace(",", ""))
            metrics["townhouse_avg_price_this_year"] = int(parts[7].replace(",", ""))
            metrics["townhouse_avg_price_last_year"] = int(parts[8].replace(",", ""))
            metrics["apartment_avg_price_this_year"] = int(parts[12].replace(",", ""))
            metrics["apartment_avg_price_last_year"] = int(parts[13].replace(",", ""))
    return metrics

@register_extractor("fraser valley")
def extractor(market_dir):
    # Find the single PDF file inside the market directory
    pdf_files = [f for f in os.listdir(market_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise FileNotFoundError(f"No PDF file found in: {market_dir}")
    if len(pdf_files) > 1:
        raise ValueError(f"Multiple PDF files found in: {market_dir}. Expected only one.")
    
    pdf_path = os.path.join(market_dir, pdf_files[0])

    # Open the PDF just long enough to read pages
    with pymupdf.open(pdf_path) as doc:
        pages_lines = []
        for i in range(2, len(doc)):
            words = doc[i].get_text("words")
            lines = group_words_into_lines(words)
            pages_lines.append(lines)

    # Extract Benchmark Price + % Change from RESIDENTIAL COMBINED (page 6 = index 5)
    residential_page = pages_lines[3]
    benchmark_prices = {}
    benchmark_pct_changes = {}

    for submarket in submarkets:
        for line in residential_page:
            if submarket.lower() in line.lower() and 'north' not in line.lower() and 'south' not in line.lower():
                parts = line.split()
                nums = [x.replace("$", "").replace(",", "") for x in parts if re.match(r"^\$?\d[\d,]*$", x)]
                if nums:
                    benchmark_prices[submarket] = int(nums[0].replace(",", ""))
                # % Change is always 4th from the right
                pct = float(parts[-4])
                benchmark_pct_changes[submarket] = pct / 100
                break

    # Fill the sheet data
    num_rows = 45
    data = {submarket: [None] * num_rows for submarket in submarkets}

    for submarket in submarkets:
        # Benchmark
        data[submarket][row_mapping["benchmark_price"]] = benchmark_prices.get(submarket)
        data[submarket][row_mapping["benchmark_pct_change"]] = benchmark_pct_changes.get(submarket)

        # Page to read
        page_idx = market_page_map[submarket]
        page_lines = pages_lines[page_idx]
        metrics = extract_table_metrics(page_lines, submarket)
        if metrics:
            for k, v in metrics.items():
                data[submarket][row_mapping[k]] = v

    # Prepare CSV rows
    csv_rows = []

    for i in range(num_rows):
        row = []
        for submarket in submarkets:
            value = data[submarket][i]
            if i == 3:
                row.extend([None, value, None, None])
            else:
                row.extend([value, None, None, None])
        csv_rows.append(row)

    df_out = (
        pd.DataFrame(csv_rows, dtype="object")  # keep Python objects
          .where(lambda x: x.notna(), None)     # NaN → None
          )

    start_row = 439
    start_col = 2
    return df_out, start_row, start_col