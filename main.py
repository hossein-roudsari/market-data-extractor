import os
from file_router import route_extraction
from gsheet_writer import write_to_gsheet

DATA_DIR = "data"

def main():
    for market_name in os.listdir(DATA_DIR):
        market_path = os.path.join(DATA_DIR, market_name)
        if not os.path.isdir(market_path):
            continue  # Skip anything that's not a folder

        if not os.listdir(market_path):
            continue

        try:
            print(f"Processing market: {market_name}")
            df, start_row, start_col = route_extraction(market_name, market_path)
            write_to_gsheet(df, start_row, start_col)
            print(f"Completed: {market_name} at ({start_row}, {start_col})\\n")
        except Exception as e:
            print(f"Failed: {market_name} → {e}\\n")


if __name__ == "__main__":
    main()
