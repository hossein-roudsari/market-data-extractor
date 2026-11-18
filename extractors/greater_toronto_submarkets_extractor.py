import os
import pandas as pd

from utils.date_utils import get_previous_month
from extractors.registry import register_extractor

covered_regions = {
    "Burlington", "Halton Hills", "Milton", "Oakville",
    "Peel Region", "Brampton", "Caledon", "Mississauga",
    "City of Toronto", "York Region", "Aurora", "Markham",
    "Newmarket", "Richmond Hill", "Vaughan", "Stouffville",
    "Durham Region", "Ajax", "Clarington", "Oshawa",
    "Pickering", "Uxbridge", "Whitby", "Orangeville"
    }

# Append remaining housing type metrics to merged_data
metric_map = {
    1: "Detached",
    2: "Semi",
    3: "Townhouse",
    4: "CondoTH",
    5: "Condo",
    }

year, _ = get_previous_month()

def extract_clean(df):
    df = df[df[0].notna() & df[0].ne("All TRREB Areas")].iloc[1:]

    def clean_numeric(col):
        return (
            col.astype(str)
               .str.replace(r"[^0-9.-]", "", regex=True)
               .replace("", "0")
               .astype(float)
        )

    df = pd.DataFrame({
        "Region": df[0].str.strip(),
        "Sales": clean_numeric(df[1]).astype(int),
        "Avg Price": clean_numeric(df[3])
    })

    return df[df["Region"].isin(covered_regions)].reset_index(drop=True)

@register_extractor("greater toronto area")
def extract(market_dir):
    all_files = sorted(os.listdir(market_dir))
    paths_curr_year = [os.path.join(market_dir, f) for f in all_files if f.startswith(f"mw{str(year)[2:]}") and f.endswith(".csv")]
    paths_prev_year = [os.path.join(market_dir, f) for f in all_files if f.startswith(f"mw{str(year - 1)[2:]}") and f.endswith(".csv")]

    dfs_curr_year = [extract_clean(pd.read_csv(path, header=None)) for path in paths_curr_year]
    dfs_prev_year = [extract_clean(pd.read_csv(path, header=None)) for path in paths_prev_year]

    merged_data = dfs_curr_year[0].copy()
    merged_data.columns = ["Region", f"Sales_{str(year)}", f"AvgPrice_{str(year)}"]
    merged_data = merged_data.merge(dfs_prev_year[0], on="Region", suffixes=("", f"_{str(year - 1)}"))
    merged_data.rename(columns={"Sales": f"Sales_{str(year - 1)}", "Avg Price": f"AvgPrice_{str(year - 1)}"}, inplace=True)

    for i, label in metric_map.items():
        df_curr_yr = dfs_curr_year[i].copy()
        df_curr_yr.columns = ["Region", f"{label}_Sales_{str(year)}", f"{label}_AvgPrice_{str(year)}"]
        
        df_prev_yr = dfs_prev_year[i].copy()
        df_prev_yr.columns = ["Region", f"{label}_Sales_{str(year - 1)}", f"{label}_AvgPrice_{str(year - 1)}"]
        
        merged_data = merged_data.merge(df_curr_yr, on="Region", how="left")
        merged_data = merged_data.merge(df_prev_yr, on="Region", how="left")

    rows = 75
    cols_per_submarket = 5
    num_submarkets = merged_data.shape[0]
    output = pd.DataFrame(index=range(rows), columns=range(num_submarkets * cols_per_submarket))

    for i, row in merged_data.iterrows():
        col = i * cols_per_submarket
        output.iat[0, col] = row[f"Sales_{str(year)}"]
        output.iat[2, col] = row[f"Sales_{str(year - 1)}"]
        output.iat[9, col] = row[f"AvgPrice_{str(year)}"]
        output.iat[11, col] = row[f"AvgPrice_{str(year - 1)}"]
        output.iat[19, col] = row[f"Detached_AvgPrice_{str(year - 1)}"]
        output.iat[21, col] = row[f"Detached_AvgPrice_{str(year)}"]
        output.iat[24, col] = row[f"Detached_Sales_{str(year - 1)}"]
        output.iat[26, col] = row[f"Detached_Sales_{str(year)}"]
        output.iat[32, col] = row[f"Semi_AvgPrice_{str(year - 1)}"]
        output.iat[34, col] = row[f"Semi_AvgPrice_{str(year)}"]
        output.iat[37, col] = row[f"Semi_Sales_{str(year - 1)}"]
        output.iat[39, col] = row[f"Semi_Sales_{str(year)}"]
        output.iat[45, col] = row[f"Townhouse_AvgPrice_{str(year - 1)}"]
        output.iat[47, col] = row[f"Townhouse_AvgPrice_{str(year)}"]
        output.iat[50, col + 2] = row[f"Townhouse_Sales_{str(year - 1)}"]
        output.iat[53, col + 1] = row[f"Townhouse_Sales_{str(year)}"]
        output.iat[50, col + 3] = row[f"CondoTH_Sales_{str(year - 1)}"]
        output.iat[53, col + 2] = row[f"CondoTH_Sales_{str(year)}"]
        output.iat[58, col] = row[f"Condo_AvgPrice_{str(year - 1)}"]
        output.iat[60, col] = row[f"Condo_AvgPrice_{str(year)}"]
        output.iat[63, col] = row[f"Condo_Sales_{str(year - 1)}"]
        output.iat[65, col] = row[f"Condo_Sales_{str(year)}"]
    
    start_row = 639
    start_col = 2
    return output, start_row, start_col