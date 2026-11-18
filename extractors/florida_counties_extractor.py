import os
import pdfplumber
import pandas as pd
import re

from extractors.registry import register_extractor
from utils.date_utils import get_previous_month

@register_extractor("florida counties")
def extract(market_dir):
    pdf_dict = {}

    for fname in sorted(os.listdir(market_dir)):
        if not fname.lower().endswith(".pdf"):
            continue

        parts = fname.split("_")
        region_key = parts[0]
        category = parts[1]
        full_path = os.path.join(market_dir, fname)
        
        if region_key not in pdf_dict:
            pdf_dict[region_key] = {}

        pdf_dict[region_key][category] = full_path

    # Build ordered list: Florida first, then rest
    pdf_groups = []

    pdf_groups.append(("Florida", pdf_dict.pop("Florida")))

    for submarket in sorted(pdf_dict):
        pdf_groups.append((submarket, pdf_dict[submarket]))
    # print(pdf_groups[0])

    
    curr_year, _ = get_previous_month()
    prev_year = curr_year - 1

    # Regex patterns
    patterns = {
        f"avg_price_{curr_year}": r"Average Sale Price\s+\$?([\d,]+)",
        f"avg_price_{prev_year}": r"Average Sale Price\s+\$?[\d,]+\s+\$?([\d,]+)",
        
        f"sales_{curr_year}": r"Closed Sales\s+([\d,]+)",
        f"sales_{prev_year}": r"Closed Sales\s+[\d,]+\s+([\d,]+)",

        "inventory": r"Inventory \(Active Listings\)\s+([\d,]+)",

        f"new_listings_{curr_year}": r"New Listings\s+([\d,]+)\s+[\d,]+",
        f"new_listings_{prev_year}": r"New Listings\s+[\d,]+\s+([\d,]+)"
    }


    # Function to extract metrics from a PDF file
    def extract_metrics(file_path):
        with pdfplumber.open(file_path) as pdf:
            text = pdf.pages[0].extract_text()
            data = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    data[key] = int(match.group(1).replace(",", ""))
                else:
                    data[key] = None
            return data

    # Create structure to hold all columns
    master_rows = {}

    # Insert values into cell-based layout
    def set_cell(row, col, val):
        if row not in master_rows:
            master_rows[row] = {}
        master_rows[row][col] = val

    # Column offset increments by 5 per sub-market
    for market_index, (market_name, files) in enumerate(pdf_groups):
        col_offset = market_index * 5

        results = []
        for category in ["Single Family Homes", "Townhouses and Condos", "Manufactured Homes"]:
            results.append(extract_metrics(files[category]))

        # Column 1: price/sales
        set_cell(34, col_offset + 0, results[0][f"avg_price_{prev_year}"])
        set_cell(36, col_offset + 0, results[0][f"avg_price_{curr_year}"])
        set_cell(39, col_offset + 0, results[0][f"sales_{prev_year}"])
        set_cell(41, col_offset + 0, results[0][f"sales_{curr_year}"])
        set_cell(47, col_offset + 0, results[1][f"avg_price_{prev_year}"])
        set_cell(49, col_offset + 0, results[1][f"avg_price_{curr_year}"])
        set_cell(52, col_offset + 0, results[1][f"sales_{prev_year}"])
        set_cell(54, col_offset + 0, results[1][f"sales_{curr_year}"])
        set_cell(60, col_offset + 0, results[2][f"avg_price_{prev_year}"])
        set_cell(62, col_offset + 0, results[2][f"avg_price_{curr_year}"])
        set_cell(65, col_offset + 0, results[2][f"sales_{prev_year}"])
        set_cell(67, col_offset + 0, results[2][f"sales_{curr_year}"])

        # Column 2–4: inventory and new listings
        set_cell(0, col_offset + 1, results[0][f"inventory"])
        set_cell(6, col_offset + 1, results[0][f"new_listings_{curr_year}"])
        set_cell(8, col_offset + 1, results[0][f"new_listings_{prev_year}"])

        set_cell(0, col_offset + 2, results[1][f"inventory"])
        set_cell(6, col_offset + 2, results[1][f"new_listings_{curr_year}"])
        set_cell(8, col_offset + 2, results[1][f"new_listings_{prev_year}"])

        set_cell(0, col_offset + 3, results[2][f"inventory"])
        set_cell(6, col_offset + 3, results[2][f"new_listings_{curr_year}"])
        set_cell(8, col_offset + 3, results[2][f"new_listings_{prev_year}"])

    # Determine full dimensions and create dataframe
    max_row = max(master_rows)
    max_col = max(max(cols.keys()) for cols in master_rows.values())
    df = pd.DataFrame([[master_rows.get(r, {}).get(c, None) for c in range(max_col + 1)] for r in range(max_row + 1)])
    df = df.astype(object).where(pd.notnull(df), None)

    start_row = 3172
    start_col = 2
    return df, start_row, start_col