import os
import pdfplumber
import pandas as pd
import re

def extract_value(text, label):
    pattern = rf"{re.escape(label)}\s*\$?([\d,]+)\s+\$?([\d,]+)"
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group(1).replace(",", "")), int(match.group(2).replace(",", ""))
        except ValueError:
            return None, None
    return None, None

def extract_simple_metric(text, label):
    pattern = rf"{re.escape(label)}\s+(\d+)\s+(\d+)"
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group(1)), int(match.group(2))
        except ValueError:
            return None, None
    return None, None

def extractor(market_dir):
    files = sorted([f for f in os.listdir(market_dir) if f.lower().endswith(".pdf")])
    num_files = len(files)
    output_df = pd.DataFrame(index=range(60), columns=range(num_files * 4))  # 4 columns per submarket

    for i, fname in enumerate(files):
        pdf_path = os.path.join(market_dir, fname)
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text()
            text = re.sub(r"(?<=\d),(?=\d)", "", text)  # remove commas inside numbers

        parts = text.split("Townhouse/Condo")
        sf_text = parts[0]
        tc_text = parts[1] if len(parts) > 1 else ""

        sf_price_last, sf_price_this = extract_value(sf_text, "Average Sales Price*")
        sf_sales_last, sf_sales_this = extract_simple_metric(sf_text, "Closed Sales")
        tc_price_last, tc_price_this = extract_value(tc_text, "Average Sales Price*")
        tc_sales_last, tc_sales_this = extract_simple_metric(tc_text, "Closed Sales")

        # Column 2
        sf_inventory = re.search(r"Inventory of Homes for Sale\s+\d+\s+(\d+)", sf_text)
        sf_inventory_val = sf_inventory.group(1) if sf_inventory else ""

        sf_new_listings_last, sf_new_listings_this = extract_simple_metric(sf_text, "New Listings")
        sf_pending_last, sf_pending_this = extract_simple_metric(sf_text, "Pending Sales")

        # Column 3
        tc_inventory = re.search(r"Inventory of Homes for Sale\s+\d+\s+(\d+)", tc_text)
        tc_inventory_val = tc_inventory.group(1) if tc_inventory else ""

        tc_new_listings_last, tc_new_listings_this = extract_simple_metric(tc_text, "New Listings")
        tc_pending_last, tc_pending_this = extract_simple_metric(tc_text, "Pending Sales")
        
        col_start = i * 4

        # Fill columns
        # # Fill Column 1
        output_df.iloc[35, col_start] = sf_price_last
        output_df.iloc[37, col_start] = sf_price_this
        output_df.iloc[40, col_start] = sf_sales_last
        output_df.iloc[42, col_start] = sf_sales_this
        output_df.iloc[48, col_start] = tc_price_last
        output_df.iloc[50, col_start] = tc_price_this
        output_df.iloc[53, col_start] = tc_sales_last
        output_df.iloc[55, col_start] = tc_sales_this

        # # Fill Column 2 (single-family inventory and listings)
        output_df.iloc[0, col_start + 1] = sf_inventory_val
        output_df.iloc[7, col_start + 1] = sf_new_listings_this
        output_df.iloc[9, col_start + 1] = sf_new_listings_last
        output_df.iloc[25, col_start + 1] = sf_pending_this
        output_df.iloc[27, col_start + 1] = sf_pending_last

        # Fill Column 3 (townhouse/condo inventory and listings)
        output_df.iloc[0, col_start + 2] = tc_inventory_val
        output_df.iloc[7, col_start + 2] = tc_new_listings_this
        output_df.iloc[9, col_start + 2] = tc_new_listings_last
        output_df.iloc[25, col_start + 2] = tc_pending_this
        output_df.iloc[27, col_start + 2] = tc_pending_last

    return output_df

def make_extractor(start_row, start_col):
    def packager(market_dir):
        df = extractor(market_dir)
        return df, start_row, start_col
    return packager