import os
import pandas as pd
from datetime import datetime
from extractors.registry import register_extractor

def extract_metric(df, location, property_type, description, year):
    row = df[
        (df['location'] == location) &
        (df['property_type'] == property_type) &
        (df['description'] == description)
        ]
    return row[str(year)].values[0] if not row.empty else None

@register_extractor("southland region")
def extract(market_dir):
    # Find the single CSV file inside the market directory
    csv_files = [f for f in os.listdir(market_dir) if f.lower().endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in: {market_dir}")
    if len(csv_files) > 1:
        raise ValueError(f"Multiple CSV files found in: {market_dir}. Expected only one.")
    
    filepath = os.path.join(market_dir, csv_files[0])
    df_full = pd.read_csv(filepath)
    df_sorted = df_full.sort_values(by='location')
    columns_to_drop = df_sorted.columns[-5:].tolist() + ['month']
    df_cleaned = df_sorted.drop(columns=columns_to_drop, errors='ignore')

    sfv_markets = [
        "Arleta", "Bell Canyon", "Calabasas", "Canoga Park", "Chatsworth",
        "Encino", "Granada Hills", "Hidden Hills", "Lake Balboa", "Lake View Terrace",
        "Mission Hills", "North Hills", "North Hollywood", "Northridge", "Pacoima",
        "Panorama City", "Porter Ranch", "Reseda", "San Fernando", "Sherman Oaks", "Studio City",
        "Sun Valley", "Sylmar", "Tarzana", "Toluca Lake", "Valley Glen", "Valley Village",
        "Van Nuys", "West Hills", "Winnetka", "Woodland Hills"
        ]

    scv_markets = [
        "Acton", "Agua Dulce", "Canyon Country", "Castaic", "Newhall", "Saugus",
        "Stevenson Ranch", "Valencia"
        ]

    covered_markets = sfv_markets + scv_markets

    this_year = datetime.today().year
    last_year = this_year - 1

    output_df = pd.DataFrame(index=range(75), columns=range(len(covered_markets) * 3))

    for i, market in enumerate(covered_markets):
        base_col = i * 3

        output_df.iloc[1, base_col + 1] = extract_metric(df_cleaned, market, "Residential", "Active Listings", this_year)
        output_df.iloc[26, base_col] = extract_metric(df_cleaned, market, "Residential", "Median Sale Price", this_year)
        output_df.iloc[28, base_col] = extract_metric(df_cleaned, market, "Residential", "Median Sale Price", last_year)
        output_df.iloc[36, base_col] = extract_metric(df_cleaned, market, "Single Family", "Median Sale Price", last_year)
        output_df.iloc[38, base_col] = extract_metric(df_cleaned, market, "Single Family", "Median Sale Price", this_year)
        output_df.iloc[41, base_col] = extract_metric(df_cleaned, market, "Single Family", "Escrows Closed", last_year)
        output_df.iloc[43, base_col] = extract_metric(df_cleaned, market, "Single Family", "Escrows Closed", this_year)
        output_df.iloc[49, base_col] = extract_metric(df_cleaned, market, "Condominium", "Median Sale Price", last_year)
        output_df.iloc[51, base_col] = extract_metric(df_cleaned, market, "Condominium", "Median Sale Price", this_year)
        output_df.iloc[54, base_col] = extract_metric(df_cleaned, market, "Condominium", "Escrows Closed", last_year)
        output_df.iloc[56, base_col] = extract_metric(df_cleaned, market, "Condominium", "Escrows Closed", this_year)

    start_row = 1864
    start_col = 2
    return output_df, start_row, start_col
