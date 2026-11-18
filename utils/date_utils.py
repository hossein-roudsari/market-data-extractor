from datetime import datetime
import calendar

def get_previous_month():
    today = datetime.today()
    year = today.year
    month = today.month - 1
    if month == 0:
        month = 12
        year -= 1
    return year, month

def get_sheet_tab_name():
    year, month = get_previous_month()
    return calendar.month_name[month] + f" {str(year)[2:]}"  # e.g., "May 25"

def get_spreadsheet_name():
    year, month = get_previous_month()
    quarter_start = ((month - 1) // 3) * 3 + 1
    quarter_months = [calendar.month_abbr[quarter_start + i] for i in range(3)]
    # return f"Market Reports | {quarter_months[0]} - {quarter_months[2]} {year}"
    return f"Market Reports | {quarter_months[0]} {year}"
