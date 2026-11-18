import os
import pdfplumber
import pandas as pd
import re

from extractors.registry import register_extractor

# Submarkets in order
submarkets = [
    "Greater Vancouver", "Burnaby", "Coquitlam", "Delta - South", "Maple Ridge",
    "Pitt Meadows", "New Westminster", "North Vancouver", "Port Coquitlam",
    "Port Moody/Belcarra", "Richmond", "Squamish", "Sunshine Coast",
    "Vancouver East", "Vancouver West", "West Vancouver", "Whistler/Pemberton",
    ]

# Burnaby split areas for prices
burnaby_subs = ["Burnaby East", "Burnaby North", "Burnaby South"]

# Mapping in price tables
market_name_mapping = {
    "Greater Vancouver": "Greater Vancouver",
    "Grand Totals": "Greater Vancouver",
    "Burnaby East": "Burnaby",
    "Burnaby North": "Burnaby",
    "Burnaby South": "Burnaby",
    "Coquitlam": "Coquitlam",
    "Ladner": "Delta - South",
    "Delta": "Delta - South",
    "Maple Ridge": "Maple Ridge",
    "Maple Ridge/Pitt Meadows": "Maple Ridge",
    "Pitt Meadows": "Pitt Meadows",
    "New Westminster": "New Westminster",
    "North Vancouver": "North Vancouver",
    "Port Coquitlam": "Port Coquitlam",
    "Port Moody": "Port Moody/Belcarra",
    "Port Moody/Belcarra": "Port Moody/Belcarra",
    "Richmond": "Richmond",
    "Squamish": "Squamish",
    "Sunshine Coast": "Sunshine Coast",
    "Vancouver East": "Vancouver East",
    "Vancouver West": "Vancouver West",
    "West Vancouver": "West Vancouver",
    "West Vancouver/Howe Sound": "West Vancouver",
    "Whistler": "Whistler/Pemberton",
    "Whistler/Pemberton": "Whistler/Pemberton",
    }

# Define row mappings
burnaby_row_map = {
    "Composite Price": 0,
    "Composite YoY": 2,
    "Detached Price": 9,
    "Detached YoY": 11,
    "Detached Sales Last Year": 15,
    "Detached Sales This Year": 17,
    "Townhouse Price": 22,
    "Townhouse YoY": 24,
    "Townhouse Sales Last Year": 28,
    "Townhouse Sales This Year": 30,
    "Apartment Price": 35,
    "Apartment YoY": 37,
    "Apartment Sales Last Year": 41,
    "Apartment Sales This Year": 43
    }

submarket_row_map = {
    "Composite Price": 0,
    "Composite YoY": 3,
    "Detached YoY": 8,
    "Detached Price": 12,
    "Detached Sales Last Year": 15,
    "Detached Sales This Year": 17,
    "Townhouse YoY": 21,
    "Townhouse Price": 25,
    "Townhouse Sales Last Year": 28,
    "Townhouse Sales This Year": 30,
    "Apartment YoY": 34,
    "Apartment Price": 38,
    "Apartment Sales Last Year": 41,
    "Apartment Sales This Year": 43
    }

@register_extractor("greater vancouver")
def extract(market_dir):
    # Find the single PDF file inside the market directory
    pdf_files = [f for f in os.listdir(market_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise FileNotFoundError(f"No CSV file found in: {market_dir}")
    if len(pdf_files) > 1:
        raise ValueError(f"Multiple CSV files found in: {market_dir}. Expected only one.")
    
    pdf_path = os.path.join(market_dir, pdf_files[0])

    # Build columns
    columns = []

    for market in submarkets:
        if market == "Burnaby":
            columns += ["Burnaby", "", "Burnaby East", "Burnaby North", "Burnaby South", ""]
            continue
        columns += [f"{market}", "", "", "", ""]

    # Initialize empty DataFrame
    num_rows = 50
    df = pd.DataFrame(None, index=range(1, num_rows + 1), columns=columns)

    # Temporary storage
    burnaby_prices = {"Burnaby East": {}, "Burnaby North": {}, "Burnaby South": {}}
    market_prices = {market: {} for market in submarkets if market != "Burnaby"}
    sales_data = {}

    # Extract prices
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in [2, 3]:
            page = pdf.pages[page_num]
            text = page.extract_text()
            lines = text.split("\n")

            pattern = re.compile(r"^(.*?)\s+\$?([\d,]+)\s+[\d.]+\s+[-\d.]+%\s+[-\d.]+%\s+[-\d.]+%\s+([-+\d.]+)%")

            current_section = "Composite"

            for line in lines:
                if "Single Family Detached" in line:
                    current_section = "Detached"
                elif "Townhouse" in line:
                    current_section = "Townhouse"
                elif "Apartment" in line:
                    current_section = "Apartment"
                else:
                    match = pattern.match(line)
                    if match:
                        area, price, yoy = match.groups()
                        area = area.strip()
                        price = price.replace(",", "")
                        yoy = yoy.replace("%", "").strip()
                        if area in burnaby_subs:
                            burnaby_prices[area][f"{current_section} Price"] = int(price)
                            burnaby_prices[area][f"{current_section} YoY"] = float(yoy) / 100
                        elif area in market_name_mapping:
                            mapped_area = market_name_mapping[area]
                            if mapped_area in market_prices:
                                market_prices[mapped_area][f"{current_section} Price"] = int(price)
                                market_prices[mapped_area][f"{current_section} YoY"] = float(yoy) / 100

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[7]  # Page 8 is index 7
        sales_text = page.extract_text().split("\n")

    i = 8
    while i < len(sales_text):
        line = sales_text[i].strip().strip(" %")

        parsed = False

        if line and not any(line.startswith(prefix) for prefix in ["DETACHED", "ATTACHED", "APARTMENTS"]):
            market_name = line.title()
            if market_name not in market_name_mapping and market_name != "Burnaby":
                i += 1
                continue
            if market_name != "Burnaby":
                market_name = market_name_mapping[market_name]

            if i + 3 < len(sales_text):
                detached_line = sales_text[i + 1].strip()
                attached_line = sales_text[i + 2].strip()
                apartment_line = sales_text[i + 3].strip()

                detached_split = re.split(r"\s+", detached_line)
                attached_split = re.split(r"\s+", attached_line)
                apartment_split = re.split(r"\s+", apartment_line)

                try:
                    sales_data[market_name] = {
                        "Detached Sales Last Year": detached_split[5],
                        "Detached Sales This Year": detached_split[7],
                        "Townhouse Sales Last Year": attached_split[5],
                        "Townhouse Sales This Year": attached_split[7],
                        "Apartment Sales Last Year": apartment_split[5],
                        "Apartment Sales This Year": apartment_split[7]
                    }
                    parsed = True
                except IndexError:
                    print(f"Could not parse sales data for {market_name}")

        i += 4 if parsed else 1  # KEY LINE — move by 4 only if parsed; otherwise move 1

    col_idx = 0
    for market in submarkets:
        prices = market_prices.get(market, {})
        sales = sales_data.get(market, {})

        # Fill Burnaby data
        if market == "Burnaby":
            for key, row in burnaby_row_map.items():
                if "Sales" in key:
                    df.iat[row, col_idx] = int(sales.get(key, 0))
            col_idx += 2
            for sub in burnaby_subs:
                for key, row in burnaby_row_map.items():
                    if "Price" in key:
                        df.iat[row, col_idx] = burnaby_prices[sub][key]
                    elif "YoY" in key:
                        df.iat[row, col_idx] = burnaby_prices[sub][key]
                col_idx += 1
            col_idx += 1
            continue

        for key, row in submarket_row_map.items():
            if "Sales" in key:
                df.iat[row, col_idx] = int(sales.get(key, 0))
            elif "Price" in key:
                df.iat[row, col_idx] = int(prices.get(key, 0))
            elif key == "Composite YoY":
                df.iat[submarket_row_map[key], col_idx + 1] = prices.get("Composite YoY", 0.0)
            elif "YoY" in key:
                df.iat[submarket_row_map[key], col_idx + 2] = prices.get(key, 0.0)

        col_idx += 5
    
    # Reset columns
    df.columns = range(df.shape[1])

    start_row = 348
    start_col = 2
    return df, start_row, start_col