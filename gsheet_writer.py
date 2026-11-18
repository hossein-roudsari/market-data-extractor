import gspread
from oauth2client.service_account import ServiceAccountCredentials

from utils import date_utils

import pandas as pd


def write_to_gsheet(df: pd.DataFrame, start_row: int, start_col: int):
    spreadsheet_name = date_utils.get_spreadsheet_name()
    sheet_tab = date_utils.get_sheet_tab_name()

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open(spreadsheet_name).worksheet(sheet_tab)

    # for row_idx, row in df.iterrows():
    #     for col_idx, value in row.items():
    #         if pd.notna(value):
    #             sheet.update_cell(start_row + row_idx, start_col + col_idx, value)


    values = df.where(pd.notna(df), None).values.tolist()

    end_row = start_row + df.shape[0]
    end_col = start_col + df.shape[1]

    range_str = (
        gspread.utils.rowcol_to_a1(start_row, start_col)
        + ":"
        + gspread.utils.rowcol_to_a1(end_row, end_col)
        )

    sheet.update(range_str, values)


