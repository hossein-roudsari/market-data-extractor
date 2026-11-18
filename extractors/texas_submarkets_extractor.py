import os
import re
import pandas as pd

from extractors.registry import register_extractor

# Output layout row mapping
target_rows = {
    "this_year_sales": 16,
    "last_year_sales": 18,
    "this_year_avg_price": 25,
    "last_year_avg_price": 27,
    "this_year_listings": 0,
    "this_year_dollar_vol": 34,
    "last_year_dollar_vol": 36,
    "this_year_inventory": 43,
    "last_year_inventory": 45,
    }

num_rows = max(target_rows.values()) + 1

def natural_key(filename):
    """
    Extract a numeric sort key from filename.
    - 'Housing Activity.csv' => 0
    - 'Housing Activity (1).csv' => 1
    - 'Housing Activity (10).csv' => 10
    """
    base_pattern = r"Housing Activity(?: \((\d+)\))?\.csv"
    match = re.match(base_pattern, filename)
    if match:
        number = match.group(1)
        return int(number) if number else 0
    else:
        return float('inf')  # push non-matching files to end

@register_extractor("texas submarkets")
def extract_submarkets(market_dir):
    # Use correct file order
    filenames = sorted(
        
        [f for f in os.listdir(market_dir) if f.lower().endswith(".csv")],
        key=natural_key
        )

    column_blocks = []
    for fname in filenames:
        fpath = os.path.join(market_dir, fname)
        df = pd.read_csv(fpath)
        submarket = str(df.at[1, "Market Name"]).strip()

        col1 = [
            df.at[0, "Sales"],
            df.at[12, "Sales"],
            df.at[0, "Average Price"],
            df.at[12, "Average Price"],
        ]
        col2 = [
            df.at[0, "Active Listings EOM"],
            df.at[0, "Dollar Volume"],
            df.at[12, "Dollar Volume"],
            df.at[0, "Months Inventory"],
            df.at[12, "Months Inventory"],
        ]

        # Build 3 columns of output with correct placement
        col_data = [None] * num_rows
        col_data2 = [None] * num_rows
        col_data3 = [None] * num_rows

        col_data[target_rows["this_year_sales"]] = col1[0]
        col_data[target_rows["last_year_sales"]] = col1[1]
        col_data[target_rows["this_year_avg_price"]] = col1[2]
        col_data[target_rows["last_year_avg_price"]] = col1[3]

        col_data2[target_rows["this_year_listings"]] = col2[0]
        col_data2[target_rows["this_year_dollar_vol"]] = col2[1]
        col_data2[target_rows["last_year_dollar_vol"]] = col2[2]
        col_data2[target_rows["this_year_inventory"]] = col2[3]
        col_data2[target_rows["last_year_inventory"]] = col2[4]

        column_blocks.extend([col_data, col_data2, col_data3])

    # Build final output matrix (num_rows × total_columns)
    output_df = pd.DataFrame(column_blocks).T
    
    start_row = 4511
    start_col = 2
    return output_df, start_row, start_col
